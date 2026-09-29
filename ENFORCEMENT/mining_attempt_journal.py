#!/usr/bin/env python3
"""Local-only, fail-closed provider-attempt journal for resumable Mining runs.

A request is written as INTENT before its external callback is invoked. After
the callback, a bounded allowlisted receipt is atomically/fsync-persisted. A
replayed receipt is returned without calling the provider again; an INTENT with
no receipt is IN_FLIGHT_UNCERTAIN and MUST NOT be automatically repeated.
This is an execution journal, not raw source/Index/CURRENT storage.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile

SCHEMA="TAKY_MINING_LOCAL_ATTEMPT_JOURNAL_V1"
MAX_RECEIPT_BYTES=1_000_000
SOURCE_FIELDS={
    "source_id","id","source_identity","url","html_url","title","name",
    "source_class","claim","summary","subject","predicate","scope","value",
    "polarity","direct_support","fresh_enough","independent_support_count",
    "published_at","updated_at","excerpt_ref",
}
ACQUISITION_FIELDS={
    "state","sha256","size_bytes","preserved_path","final_url","content_type",
    "canonical_promotion",
}


def _hash(value):
    raw=value if isinstance(value,bytes) else str(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sync_directory(directory):
    try:
        fd=os.open(str(directory),os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    except OSError:
        # Some platforms prohibit directory fsync; file fsync + replace
        # are still used. Never claim crash-proof durability on that host.
        pass


def _atomic_json(path:Path, value:dict):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,
                    separators=(",",":"))+"\n").encode("utf-8")
    if len(raw)>MAX_RECEIPT_BYTES:
        raise ValueError("ATTEMPT_RECEIPT_EXCEEDS_LOCAL_BOUND")
    with tempfile.NamedTemporaryFile(mode="wb",dir=path.parent,
                                     prefix=".mining-attempt-",delete=False) as temp:
        try:
            temp.write(raw);temp.flush();os.fsync(temp.fileno())
            name=temp.name
        except BaseException:
            name=temp.name
            temp.close()
            Path(name).unlink(missing_ok=True)
            raise
    try:
        os.replace(name,path)
        _sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def _receipt(output):
    if not isinstance(output,dict) or str(output.get("state") or "").upper() not in {
        "SUCCESS","EMPTY","FAILED"
    }:
        return {"state":"FAILED","error":"INVALID_PROVIDER_RESULT"}
    state=str(output["state"]).upper()
    result={"state":state}
    if output.get("error"):
        # Only the error code is retained, never arbitrary exception text.
        code=str(output["error"]).strip().upper()
        result["error"]=code[:96] if code.replace("_","").replace("-","").isalnum() else "PROVIDER_ERROR"
    response=output.get("response")
    if isinstance(response,dict):
        rows=response.get("results")
        if not isinstance(rows,list):
            rows=[]
        result["response"]={
            "results":[{k:row[k] for k in SOURCE_FIELDS if k in row
                        and isinstance(row[k],(str,bool,int,float,type(None)))}
                       for row in rows[:50] if isinstance(row,dict)],
            **({"retrieved_at":response["retrieved_at"]}
               if isinstance(response.get("retrieved_at"),str) else {}),
        }
    proof=output.get("source_acquisition")
    if isinstance(proof,dict):
        result["source_acquisition"]={
            k:proof[k] for k in ACQUISITION_FIELDS if k in proof
            and isinstance(proof[k],(str,bool,int,float,type(None)))
        }
    result["external_fetch_performed"]=output.get("external_fetch_performed") is True
    return result


class LocalAttemptJournal:
    def __init__(self, directory:Path, *, goal_id:str):
        if not str(goal_id or "").strip():
            raise ValueError("GOAL_ID_REQUIRED")
        self.directory=Path(directory)
        self.goal_id=str(goal_id)
        self.directory.mkdir(parents=True,exist_ok=True)

    def _identity(self,request):
        return {k:request.get(k) for k in (
            "request_id","provider","frontier_id","query","purpose")}
    
    def _path(self,request):
        rid=str(request.get("request_id") or "").strip()
        if not rid:
            raise ValueError("REQUEST_ID_REQUIRED")
        return self.directory/(_hash(self.goal_id+"|"+rid)+".json")

    def _read(self,path, identity):
        try:
            saved=json.loads(path.read_text(encoding="utf-8"))
            if (saved.get("schema")!=SCHEMA
                or saved.get("goal_id")!=self.goal_id
                or saved.get("request")!=identity
                or saved.get("state") not in {"INTENT","RECEIPT"}
                or (saved["state"]=="RECEIPT" and
                    not isinstance(saved.get("result"),dict))):
                raise ValueError("ATTEMPT_JOURNAL_IDENTITY_OR_SCHEMA_MISMATCH")
            return saved
        except (OSError,ValueError,TypeError,KeyError):
            return None

    def will_invoke(self,request):
        """For preflight budget only; existing INTENT/corrupt entries never rerun."""
        return not self._path(request).exists()

    def execute(self,request,provider_fn):
        """Return (safe result, actual callback invoked, replayed receipt).

        Concurrent process/crash ambiguity resolves to HOLD, never a second
        unobserved network request. Caller must reconcile uncertain INTENT.
        """
        identity=self._identity(request)
        path=self._path(request)
        intent={"schema":SCHEMA,"goal_id":self.goal_id,"request":identity,
                "state":"INTENT"}
        try:
            fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:
            saved=self._read(path,identity)
            if saved is None:
                return {"state":"FAILED","error":"CORRUPT_ATTEMPT_JOURNAL"},False,False
            if saved["state"]=="RECEIPT":
                result=saved["result"]
                proof=result.get("source_acquisition") or {}
                if proof.get("state")=="ACQUIRED_AND_PRESERVED":
                    # A cached binary-acquisition receipt without its original
                    # bytes is NOT a successful replay. Never follow arbitrary
                    # paths or trust stale claims.
                    try:
                        source=Path(proof["preserved_path"])
                        size=int(proof["size_bytes"])
                        if (not source.is_file() or source.stat().st_size!=size
                            or _hash(source.read_bytes())!=proof["sha256"]):
                            raise ValueError("STALE_OR_CHANGED_ORIGINAL")
                    except (OSError,KeyError,ValueError,TypeError):
                        return {"state":"FAILED","error":"SOURCE_RECEIPT_STALE"},False,False
                return result,False,True
            return {"state":"FAILED","error":"IN_FLIGHT_UNCERTAIN"},False,False
        with os.fdopen(fd,"wb") as out:
            raw=(json.dumps(intent,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
            out.write(raw);out.flush();os.fsync(out.fileno())
        _sync_directory(self.directory)
        if provider_fn is None:
            output={"state":"FAILED","error":"PROVIDER_ADAPTER_UNAVAILABLE"}
            invoked=False
        else:
            invoked=True
            try:
                output=provider_fn(dict(request))
            except Exception:
                output={"state":"FAILED","error":"PROVIDER_EXECUTION_EXCEPTION"}
        try:
            safe=_receipt(output)
            _atomic_json(path,{**intent,"state":"RECEIPT","result":safe})
            return safe,invoked,False
        except Exception:
            # The external call may already have succeeded. Never retry it
            # merely because storing the observed result failed.
            return {"state":"FAILED","error":"IN_FLIGHT_UNCERTAIN"},invoked,False
