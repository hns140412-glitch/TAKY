"""Preserve verified local browser feedback as non-authoritative evidence.

The existing browser verifier remains the sole receipt checker. Durable files
are candidates only; they do not update CURRENT, LEARNING, or app content.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE" / "LOCAL_TECHNICAL_FEEDBACK_JOURNAL"
SCHEMA = "TAKY_LOCAL_TECHNICAL_FEEDBACK_JOURNAL_V1"

def digest(data):
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()

def persist(reconcile, root=JOURNAL):
    import global_source_live_consumer as live
    import global_source_learning_feedback as flow
    if reconcile.get("status")!="VERIFIED_LOCAL_RECEIPTS_RECONCILED":
        raise ValueError("NOT_VERIFIED_RECONCILIATION")
    details=reconcile.get("run_details")
    if not isinstance(details,list) or len(details)!=reconcile.get("run_count"):
        raise ValueError("JOURNAL_MISSING_VERIFIED_DETAILS")
    if Path(root).is_symlink() or JOURNAL.is_symlink():
        raise ValueError("JOURNAL_DIRECTORY_SYMLINK_REFUSED")
    if Path(root).resolve()!=JOURNAL.resolve():
        raise ValueError("JOURNAL_PATH_NOT_CANONICAL")
    if not all(x.get("semantic_approved") is False and x.get("knowledge_approved") is False
               and x.get("live_browser_evidence") is True for x in details):
        raise ValueError("FEEDBACK_AUTHORITY_BOUNDARY_FAILED")
    verified=[]
    for item in details:
        run=item.get("run_id")
        if (not isinstance(run,str) or not live.RUN_PATTERN.fullmatch(run)
            or live._live_evidence(run)!=item.get("receipt_sha256")):
            raise ValueError("JOURNAL_RUNTIME_RECEIPT_INVALID")
        if (item.get("consumer_code_sha256")!=flow.sha(flow.CODE.read_bytes())
            or item.get("raw_sha256") is None or item.get("anchor_sha256") is None):
            raise ValueError("JOURNAL_SOURCE_OR_EXECUTOR_REVISION_CHANGED")
        payload={key:item[key] for key in (
            "run_id","receipt_sha256","source_id","raw_sha256",
            "anchor_sha256","forming_revision","consumer_code_sha256",
            "before","after")}
        payload.update(schema=SCHEMA,authority="REVIEW_CANDIDATE_NOT_APPROVED",
                       educational_learning=False,app_consumption_approved=False,
                       current_modified=False,source_modified=False,
                       source_kind="LOCAL_BROWSER_TECHNICAL_METHOD")
        payload["manifest_sha256"]=digest(payload)
        verified.append(payload)
    if len({p["run_id"] for p in verified})!=len(verified):
        raise ValueError("DUPLICATE_VERIFIED_RUN_ID")
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    saved=[]
    new=0
    for payload in verified:
        name="TECHNICAL_FEEDBACK_"+hashlib.sha256(payload["run_id"].encode()).hexdigest()[:24]+".json"
        file=root/name
        data=json.dumps(payload,ensure_ascii=False,indent=2)+"\n"
        if file.is_symlink():
            raise ValueError("JOURNAL_ENTRY_SYMLINK_REFUSED")
        try:
            with file.open("x",encoding="utf-8") as target:
                target.write(data)
                target.flush()
                import os
                os.fsync(target.fileno())
            new+=1
        except FileExistsError:
            if file.read_text(encoding="utf-8")!=data:
                raise ValueError("FEEDBACK_JOURNAL_REPLAY_CONFLICT")
        if file.read_text(encoding="utf-8")!=data:
            raise ValueError("JOURNAL_IMMUTABLE_READBACK_FAILED")
        saved.append(str(file))
    return {"status":"VERIFIED_TECHNICAL_FEEDBACK_PERSISTED_NOT_APPROVED",
            "validated_runs":len(verified),"new_files":new,
            "replayed_existing":len(verified)-new,
            "journal_paths":saved,"semantic_approvals":0,
            "educational_learning_updates":0,"operational_db_written":False,
            "CURRENT_changed":False}
