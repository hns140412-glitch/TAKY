"""TAKY event-keyed resumption of deferred *registered read-only* tasks.

An old Reason message does not run again. Only a fresh verified change in its
canonical upstream dependency evidence can admit one bounded retry through
the existing TAKY V2 local gate. Exclusive claims forbid parallel/ambiguous
retries; model and deployment permissions are NEVER conveyed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable


def _sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def recover_deferred_once(repo:Path, *,
                          max_receipts:int=20,
                          admission=None,
                          observer=None) ->dict:
    if type(max_receipts) is not int or not 1<=max_receipts<=50:
        return {"status":"DEPENDENCY_WATCH_INVALID_LIMIT"}
    root=repo.resolve()
    local=root/".local"
    if (not local.is_dir() or local.is_symlink()
            or getattr(local,"is_junction",lambda:False)()
            or local.resolve().parent!=root):
        return {"status":"DEPENDENCY_WATCH_LOCAL_UNTRUSTED"}
    workdir=root/"TOOLS"
    if not workdir.is_dir():
        return {"status":"DEPENDENCY_WATCH_OWNER_UNAVAILABLE"}
    import sys
    if str(workdir) not in sys.path:
        sys.path.insert(0,str(workdir))
    from TAKY_ORCHESTRATION_ADVANCE import DEFAULT_BOARD, EVIDENCE, read_json
    from taky_registered_goal_queue import (
        execute_registered_queue, registered_dependency_revision)
    verify = admission or execute_registered_queue
    view = observer or (lambda:read_json(DEFAULT_BOARD))
    counters={"observed":0,"still_waiting":0,"already_claimed":0,
              "new_attempts":0,"reused_evidence":0,"uncertain":0}
    # Rotate through all receipts rather than permanently hiding old
    # deferred work behind the newest N unrelated messages.
    import bisect
    import os
    from uuid import uuid4
    cursor_path=local/"taky-dependency-scan-cursor.json"
    if cursor_path.is_symlink() or getattr(cursor_path,"is_junction",lambda:False)():
        return {"status":"DEPENDENCY_SCAN_CURSOR_UNTRUSTED"}
    try:
        old=json.loads(cursor_path.read_text(encoding="utf-8"))
        cursor=(old.get("last") if isinstance(old,dict) and
                old.get("schema")=="TAKY_DEPENDENCY_CURSOR_V1" else "")
    except (OSError,ValueError,TypeError):
        cursor=""
    if not isinstance(cursor,str):
        cursor=""
    universe=sorted(p for p in local.glob("taky-reason-result-*.json")
                    if p.is_file() and not p.is_symlink())
    names=[p.name for p in universe]
    start=bisect.bisect_right(names,cursor)
    records=(universe[start:]+universe[:start])[:max_receipts]
    events=[]
    for filepath in records:
        if (filepath.is_symlink() or getattr(filepath,"is_junction",lambda:False)()
                or not filepath.is_file() or filepath.stat().st_size>262144):
            continue
        try:
            event=json.loads(filepath.read_text(encoding="utf-8"))
            if not isinstance(event,dict):
                continue
            mid=event.get("message_id")
            if (event.get("schema")!="TAKY_REASON_RESULT_V1" or not
                isinstance(mid,str) or not mid.isalnum() or len(mid)>42 or
                filepath.name!="taky-reason-result-"+mid+".json" or
                not isinstance(event.get("queue"),dict) or
                event["queue"].get("schema")!="TAKY_GOAL_QUEUE_OBSERVATION_V2"):
                continue
            waiting=[x for x in event["queue"].get("items",[])
                     if isinstance(x,dict) and x.get("status")==
                        "WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE"]
            if not waiting:continue
            snap=local/("taky-intake-snapshot-"+mid+".json")
            claim=local/("taky-reason-claim-"+mid+".json")
            if (not snap.is_file() or snap.is_symlink()
                    or getattr(snap,"is_junction",lambda:False)()
                    or not claim.is_file() or claim.is_symlink()
                    or getattr(claim,"is_junction",lambda:False)()
                    or snap.stat().st_size>65536):
                continue
            snapshot=snap.read_bytes()
            bound=json.loads(claim.read_text(encoding="utf-8"))
            if not isinstance(bound,dict):
                continue
            if (bound.get("schema")!="TAKY_REASON_CLAIM_V1" or
                    bound.get("message_id")!=mid or
                    bound.get("manifest_sha256")!=_sha(snapshot) or
                    bound.get("queue_id")!=event.get("queue_id") or
                    event.get("manifest_sha256")!=_sha(snapshot) or
                    bound.get("state")!="RECORDED"):
                continue
            original=json.loads(snapshot)
            if not isinstance(original,dict):
                continue
            if (original.get("schema")!="TAKY_GOAL_QUEUE_V2" or
                    original.get("queue_id")!=event.get("queue_id")):
                continue
            intended={x["work_id"]:x for x in original.get("items",[])
                      if isinstance(x,dict) and "work_id" in x}
            if not set(x.get("work_id") for x in waiting).issubset(intended):
                continue
            board=view()
            if not isinstance(board,dict) or not isinstance(board.get("tasks"),list):
                raise ValueError("CANONICAL_BOARD_INVALID")
            rows={x.get("id"):x for x in board.get("tasks",[])
                  if isinstance(x,dict)}
            ready=[]
            for item in waiting:
                original_task=intended.get(item["work_id"])
                deps=original_task.get("depends_on") if isinstance(original_task,dict) else None
                child=rows.get(item["work_id"])
                if (not isinstance(deps,list) or not isinstance(child,dict)
                        or child.get("dependencies")!=deps or
                        child.get("approval_required") is not False):
                    continue
                revision=registered_dependency_revision(deps,rows,EVIDENCE)
                if revision is not None:
                    ready.append((item["work_id"],deps,revision))
            counters["observed"]+=len(waiting)
            counters["still_waiting"]+=len(waiting)-len(ready)
            for work_id,deps,proof in ready:
                # Stable across original Reason messages and child metadata.
                # A single registered dependency revision gets one wake.
                binding=_sha((work_id+"|"+proof).encode("utf-8"))
                marker=local/("taky-dependency-attempt-"+work_id+"-"+binding[:20]+".json")
                payload={"schema":"TAKY_DEPENDENCY_ATTEMPT_V1",
                         "message_id":mid,"work_id":work_id,"binding_sha256":binding,
                         "state":"CLAIMED_OUTCOME_UNKNOWN"}
                # A previously proven PRE-DISPATCH hold can be reconsidered
                # only on actual source/worker/contract change. This includes
                # provenance becoming accessible again after a transient fault.
                from TAKY_ORCHESTRATION_ADVANCE import evidence_signature
                try:
                    _,source_digest=evidence_signature(board,work_id)
                    source_probe={"state":"SOURCE_INPUTS_AVAILABLE",
                                  "digest":source_digest}
                except (OSError,ValueError,KeyError,TypeError) as source_error:
                    source_probe={"state":"SOURCE_INPUTS_UNAVAILABLE",
                                  "error_class":type(source_error).__name__}
                repair_scope=_sha(
                    json.dumps({"child":rows[work_id],
                                "provenance":source_probe,
                                "dependency_revision":proof},
                               sort_keys=True,ensure_ascii=False).encode("utf-8")+
                    (Path(__file__).resolve().parents[1]/"TOOLS"/
                     "TAKY_ORCHESTRATION_ADVANCE.py").read_bytes())
                try:
                    with marker.open("x",encoding="utf-8") as f:
                        json.dump(payload,f,ensure_ascii=False)
                except FileExistsError:
                    # Only a *proven non-dispatch* can be reconsidered, and
                    # only after actual canonical worker/authority changes.
                    # Never rearm uncertain or executed attempts.
                    if marker.is_symlink() or getattr(
                            marker,"is_junction",lambda:False)():
                        counters["uncertain"]+=1
                        continue
                    prior=json.loads(marker.read_text(encoding="utf-8"))
                    if (not isinstance(prior,dict) or
                            prior.get("state")!="PREDISPATCH_HOLD_NO_WORKER_CALL" or
                            prior.get("binding_sha256")!=binding or
                            prior.get("repair_source_sha256")==repair_scope):
                        counters["already_claimed"]+=1
                        continue
                    rearm=local/("taky-dependency-rearm-"+work_id+"-"+
                                binding[:16]+"-"+repair_scope[:16]+".json")
                    try:
                        with rearm.open("x",encoding="utf-8") as stream:
                            json.dump({"schema":"TAKY_PREDISPATCH_REARM_V1",
                                       "work_id":work_id,
                                       "repair_source_sha256":repair_scope},
                                      stream)
                    except FileExistsError:
                        counters["already_claimed"]+=1
                        continue
                # Every fresh proof identity gets at most one bounded attempt.
                try:
                    report=verify({"schema":"TAKY_GOAL_QUEUE_V2",
                         "queue_id":event["queue_id"],"items":[intended[work_id]]},
                         root,local,
                         expected_dependencies={work_id:proof})
                    if (not isinstance(report,dict) or
                            report.get("schema")!="TAKY_GOAL_QUEUE_OBSERVATION_V2"):
                        raise ValueError("UNVERIFIED_RECOVERY_REPORT")
                    ref=report.get("local_queue_receipt")
                    if (not isinstance(ref,str) or
                            not ref.replace(chr(92),"/").startswith(".local/")):
                        raise ValueError("RECOVERY_LOCAL_RECEIPT_MISSING")
                    raw_observed=root/ref
                    if (raw_observed.is_symlink() or
                            getattr(raw_observed,"is_junction",lambda:False)()):
                        raise ValueError("RECOVERY_RECEIPT_REPARSE")
                    observed_path=raw_observed.resolve(strict=True)
                    if (not observed_path.is_file()
                            or observed_path.parent!=local
                            or observed_path.stat().st_size>524288):
                        raise ValueError("RECOVERY_RECEIPT_OUT_OF_SCOPE")
                    disk=json.loads(observed_path.read_text(encoding="utf-8"))
                    if (disk!= {k:v for k,v in report.items()
                               if k!="local_queue_receipt"}
                            or disk.get("queue_id")!=event["queue_id"]
                            or disk.get("model_calls")!=0
                            or disk.get("goals_verified_done")!=0):
                        raise ValueError("RECOVERY_RECEIPT_BINDING_MISMATCH")
                    statuses=[x for x in report.get("items",[])
                              if isinstance(x,dict) and x.get("work_id")==work_id]
                    predispatch=(len(statuses)==1 and
                        statuses[0].get("attempted") is False and
                        statuses[0].get("status") in {
                            "EXISTING_CANONICAL_GATE_HOLD",
                            "CANONICAL_AUTHORITY_CHANGED",
                            "DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED",
                        })
                    payload["state"]=(
                        "PREDISPATCH_HOLD_NO_WORKER_CALL" if predispatch
                        else "RECEIPT_OBSERVED_NOT_PORTFOLIO_DONE")
                    if predispatch:
                        # Pin the ACTUAL rejecting gate's observed provenance,
                        # not a speculative sample taken before admission.
                        # Otherwise unavailable -> restored -> available can
                        # look identical to the earlier pre-attempt sample.
                        rejected=statuses[0]
                        if (rejected.get("gate_route")==
                                "LOCAL_INPUT_PROVENANCE_HOLD" and
                                isinstance(rejected.get("gate_input_error_type"),str)):
                            failure_probe={
                                "state":"SOURCE_INPUTS_UNAVAILABLE",
                                "error_class":rejected["gate_input_error_type"]}
                            failure_revision=proof
                        elif (rejected.get("status")==
                                "DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED"):
                            # Revision B was actually observed at rejection.
                            # If the trusted upstream returns to A, A must be
                            # eligible for exactly one fresh bounded precheck.
                            failure_probe=source_probe
                            failure_revision=rejected.get(
                                "gate_observed_dependency_revision","UNAVAILABLE")
                        else:
                            failure_probe=None
                            failure_revision=None
                        if failure_probe is not None:
                            payload["repair_source_sha256"]=_sha(
                                json.dumps({"child":rows[work_id],
                                            "provenance":failure_probe,
                                            "dependency_revision":failure_revision},
                                           sort_keys=True,ensure_ascii=False
                                           ).encode("utf-8")+
                                (Path(__file__).resolve().parents[1]/"TOOLS"/
                                 "TAKY_ORCHESTRATION_ADVANCE.py").read_bytes())
                        else:
                            payload["repair_source_sha256"]=repair_scope
                        counters["still_waiting"]+=1
                    payload["result_status"]=report.get("status")
                    payload["local_queue_receipt"]=ref
                    payload["goals_verified_done"]=0
                    counters["new_attempts"]+=1
                    if any(x.get("status")=="REUSED_CANONICAL_LOCAL_EVIDENCE"
                           for x in report.get("items",[])):
                        counters["reused_evidence"]+=1
                except (OSError,ValueError,TypeError,RuntimeError) as exc:
                    payload["error_class"]=type(exc).__name__
                    counters["uncertain"]+=1
                # Marker is always retained, even on unknown outcomes.
                temporary=local/("taky-dependency-write-"+uuid4().hex+".tmp")
                try:
                    with temporary.open("x",encoding="utf-8") as out:
                        json.dump(payload,out,ensure_ascii=False,indent=2)
                    if (marker.is_symlink() or getattr(
                            marker,"is_junction",lambda:False)()):
                        raise ValueError("DEPENDENCY_MARKER_REPARSE")
                    os.replace(temporary,marker)
                except (OSError,ValueError):
                    counters["uncertain"]+=1
                finally:
                    temporary.unlink(missing_ok=True)
                events.append({"work_id":work_id,"state":payload["state"]})
        except (OSError,ValueError,TypeError,KeyError,AttributeError):
            counters["uncertain"]+=1
    if records:
        fresh=local/("taky-dependency-cursor-"+uuid4().hex+".tmp")
        try:
            with fresh.open("x",encoding="utf-8") as stream:
                json.dump({"schema":"TAKY_DEPENDENCY_CURSOR_V1",
                           "last":records[-1].name},stream)
            if cursor_path.is_symlink() or getattr(
                    cursor_path,"is_junction",lambda:False)():
                raise ValueError("CURSOR_REPARSE")
            os.replace(fresh,cursor_path)
        except (OSError,ValueError):
            counters["uncertain"]+=1
        finally:
            fresh.unlink(missing_ok=True)
    return {"schema":"TAKY_DEPENDENCY_WATCH_V1",
            "status":"BOUNDED_DEPENDENCY_OBSERVATION",
            **counters,"events":events,
            "new_model_calls":0,"portfolio_done_claimed":False}
