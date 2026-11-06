"""Canonical dependency decisions for TAKY's existing read-only workers.

V2 is intentionally NOT a new LLM orchestrator.  V1 keeps owning the
Claude/Codex cycle. V2 binds a registered WORK_ID to a canonical VERIFIED/
ADOPTED upstream and delegates to the existing TAKY local worker, without
ever promoting model text, a local check, or a generated report to DONE.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


def registered_dependency_revision(deps: list, index: dict,
                                   evidence_root: Path) -> str | None:
    """A read-only registered-state fingerprint, never a DONE attestation."""
    revisions=[]
    for dep in deps:
        row=index.get(dep)
        if (not isinstance(row,dict) or
                row.get("status") not in {"VERIFIED","ADOPTED"}):
            return None
        refs=row.get("evidence")
        if not isinstance(refs,list) or not refs:
            return None
        pins=[]
        for ref in refs:
            if not isinstance(ref,str) or len(ref)>1024:
                return None
            supplied=Path(ref)
            try:
                if (supplied.is_symlink() or
                        getattr(supplied,"is_junction",lambda:False)()):
                    return None
                file=supplied.resolve(strict=True)
                if (not file.is_file() or file.parent!=evidence_root.resolve()
                        or not 0<file.stat().st_size<=8*1024*1024):
                    return None
                pins.append(hashlib.sha256(file.read_bytes()).hexdigest())
            except (OSError, ValueError):
                return None
        revisions.append([dep,row["status"],pins])
    return hashlib.sha256(json.dumps(revisions,sort_keys=True,
                  ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()


def execute_registered_queue(document: dict, repo: Path, local: Path,
                             *, validate_only: bool = False,
                             registered_executor=None,
                             expected_dependencies: dict | None = None) -> dict:
    if (not isinstance(document, dict)
            or document.get("schema") != "TAKY_GOAL_QUEUE_V2"
            or set(document) != {"schema", "queue_id", "items"}):
        return {"status": "QUEUE_V2_SCHEMA_INVALID", "items_executed": 0}
    if (not local.is_dir() or local.is_symlink()
            or getattr(local,"is_junction",lambda:False)()
            or local.resolve().parent!=repo.resolve()):
        return {"status":"QUEUE_V2_LOCAL_WRITE_SCOPE_UNTRUSTED",
                "items_executed":0}
    queue_id = document.get("queue_id")
    tasks = document.get("items")
    if (not isinstance(queue_id, str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]{4,80}",queue_id)
            or not isinstance(tasks, list) or not 1 <= len(tasks) <= 8):
        return {"status": "QUEUE_V2_SCHEMA_INVALID", "items_executed": 0}
    tools_dir = repo / "TOOLS"
    if not tools_dir.is_dir():
        return {"status": "QUEUE_V2_SOURCE_MISSING", "items_executed": 0}
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    try:
        from TAKY_ORCHESTRATION_ADVANCE import (
            DEFAULT_BOARD, EVIDENCE, LOCAL_EXECUTORS, choose, read_json,
            run_checks, CanonicalPreclaimSourceHold,
            CanonicalPreclaimDependencyHold)
        root = EVIDENCE.resolve(strict=True)
        board_path = DEFAULT_BOARD.resolve(strict=True)
        if board_path.stat().st_size > 4 * 1024 * 1024:
            return {"status": "QUEUE_V2_BOARD_UNTRUSTED", "items_executed": 0}
        board = read_json(board_path)
        rows = board.get("tasks")
        if not isinstance(rows, list):
            return {"status": "QUEUE_V2_BOARD_UNTRUSTED", "items_executed": 0}
        index = {row.get("id"): row for row in rows if isinstance(row,dict)}
        if len(index) != len(rows):
            return {"status": "QUEUE_V2_BOARD_UNTRUSTED", "items_executed": 0}
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        return {"status": "QUEUE_V2_BOARD_UNTRUSTED", "items_executed": 0}
    keys = set()
    admitted = []
    for item in tasks:
        if (not isinstance(item,dict) or set(item) != {"work_id", "depends_on"}
                or not isinstance(item["work_id"],str)
                or not re.fullmatch(r"[A-Za-z0-9-]{4,90}", item["work_id"])
                or not isinstance(item["depends_on"],list)
                or any(not isinstance(x,str) for x in item["depends_on"])):
            return {"status": "QUEUE_V2_STEP_INVALID", "items_executed": 0}
        work_id = item["work_id"]
        task = index.get(work_id)
        deps = item["depends_on"]
        if (work_id in keys or task is None or work_id not in LOCAL_EXECUTORS
                or task.get("approval_required") is not False
                or task.get("status") not in {
                    "NOT_STARTED", "DISCOVERY", "EVALUATION", "READY", "IMPLEMENTING"
                } or deps != task.get("dependencies",[])):
            return {"status": "QUEUE_V2_CANONICAL_BINDING_REJECTED",
                    "items_executed": 0}
        keys.add(work_id)
        admitted.append((work_id, list(deps)))
    if validate_only:
        return {"schema":"TAKY_GOAL_QUEUE_VALIDATION_V1",
                "status":"QUEUE_INPUT_VERIFIED_NOT_DISPATCHED",
                "items_total":len(admitted),"items_executed":0,
                "goals_verified_done":0}

    def source_evidence_ok(dependency: str, latest_index: dict) -> bool:
        # A canonical registered-state precheck, not an independently signed
        # DONE; final user intent still belongs to TAKY2 DONE and USER gates.
        return registered_dependency_revision([dependency],latest_index,root) is not None

    results = []
    for work_id, deps in admitted:
        worker_launched=False
        try:
            latest = read_json(board_path)
            latest_index = {r.get("id"):r for r in latest["tasks"]
                            if isinstance(r,dict)}
            this = latest_index.get(work_id)
            if (not isinstance(this,dict) or this.get("dependencies",[]) != deps
                    or this.get("approval_required") is not False):
                results.append({"work_id":work_id,"status":"CANONICAL_AUTHORITY_CHANGED",
                                "attempted":False})
                continue
            waiting=[d for d in deps if not source_evidence_ok(d,latest_index)]
            if waiting:
                results.append({"work_id":work_id,
                                "status":"WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE",
                                "pending_dependency_ids":waiting,
                                "attempted":False})
                continue
            if expected_dependencies is not None:
                observed_dependency=registered_dependency_revision(
                    deps,latest_index,root)
                if expected_dependencies.get(work_id)!=observed_dependency:
                    results.append({"work_id":work_id,
                                    "status":"DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED",
                                    "gate_observed_dependency_revision":(
                                        observed_dependency or "UNAVAILABLE"),
                                    "attempted":False})
                    continue
            plan=choose(latest,root)
            row=next((x for x in plan["considered"]
                      if x["task_id"]==work_id),None)
            route=row.get("route") if isinstance(row,dict) else None
            if (expected_dependencies is not None and route in {
                    "LOCAL_SLICE_ALREADY_EVIDENCED","LOCAL_SLICE_NEEDS_CORRECTION"}):
                # Force a *separately revision-bound* read-only worker receipt.
                # Ordinary local evidence remains immutable and untouched.
                route="READY_FOR_LOCAL_EXECUTION"
            if route=="LOCAL_SLICE_ALREADY_EVIDENCED":
                existing=Path(row["existing_evidence"]).resolve(strict=True)
                if existing.parent!=root:
                    raise ValueError("CACHED_EVIDENCE_NOT_IN_CANONICAL_FOLDER")
                proof=read_json(existing)
                if (proof.get("schema")!="TAKY_LOCAL_WORK_SLICE_V1"
                        or proof.get("task_id")!=work_id
                        or proof.get("portfolio_done") is not False):
                    raise ValueError("CACHED_WORK_EVIDENCE_INVALID")
                results.append({"work_id":work_id,
                                "status":"REUSED_CANONICAL_LOCAL_EVIDENCE",
                                "evidence_sha256":hashlib.sha256(
                                    existing.read_bytes()).hexdigest(),
                                "attempted":False})
                continue
            if route!="READY_FOR_LOCAL_EXECUTION":
                results.append({"work_id":work_id,
                                "status":"EXISTING_CANONICAL_GATE_HOLD",
                                "gate_route":route,
                                "gate_input_error_type":(
                                    row.get("input_error_type") if isinstance(row,dict)
                                    else None),
                                "attempted":False})
                continue
            # The existing signed-input worker rechecks the board after its
            # local diagnosis. No new executor or authority bypass.
            if expected_dependencies is not None:
                before=read_json(board_path)
                recent={r.get("id"):r for r in before["tasks"] if isinstance(r,dict)}
                near_dispatch=registered_dependency_revision(
                    deps,recent,root)
                if (near_dispatch!=expected_dependencies.get(work_id)
                        or recent.get(work_id,{}).get("approval_required") is not False):
                    results.append({"work_id":work_id,
                                    "status":"DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED",
                                    "gate_observed_dependency_revision":(
                                        near_dispatch or "UNAVAILABLE"),
                                    "attempted":False})
                    continue
            # Production has ONE durable work-claim owner: run_checks().
            # The older outer claim caused a proven predispatch failure to be
            # mislabeled attempted/irreversible. Retain the injected fake-runner
            # guard only for isolated tests; no external provider may use it.
            synthetic_claim=None
            if registered_executor is not None:
                from TAKY_ORCHESTRATION_ADVANCE import evidence_signature
                import os
                from uuid import uuid4
                _,source_version=evidence_signature(
                    before if expected_dependencies is not None else latest,work_id)
                proof_revision=(registered_dependency_revision(
                    deps,recent if expected_dependencies is not None
                    else latest_index,root) if deps else
                    hashlib.sha256(b"NO_REGISTERED_DEPENDENCIES").hexdigest())
                key=hashlib.sha256((work_id+"|"+str(proof_revision)).encode()).hexdigest()[:24]
                synthetic_claim=local/("taky-registered-worker-"+work_id+"-"+key+".json")
                claimed={"schema":"TAKY_REGISTERED_WORKER_CLAIM_V1",
                         "work_id":work_id,"source_version":source_version,
                         "dependency_revision":proof_revision,
                         "state":"OUTCOME_UNKNOWN_NO_BLIND_RETRY"}
                try:
                    with synthetic_claim.open("x",encoding="utf-8") as out:
                        json.dump(claimed,out,ensure_ascii=False)
                except FileExistsError:
                    results.append({"work_id":work_id,
                                    "status":"REGISTERED_WORKER_ALREADY_CLAIMED",
                                    "attempted":False})
                    continue
                worker_launched=True
                result=registered_executor(work_id,board_path,root)
            else:
                def _claimed_by_canonical_worker(_work_id):
                    nonlocal worker_launched
                    worker_launched=True
                if expected_dependencies is not None:
                    result=run_checks(
                        work_id,board_path,root,
                        dependency_revision=expected_dependencies[work_id],
                        on_worker_claimed=_claimed_by_canonical_worker)
                else:
                    result=run_checks(
                        work_id,board_path,root,
                        on_worker_claimed=_claimed_by_canonical_worker)
            if (not isinstance(result,dict)
                    or result.get("task_id")!=work_id
                    or result.get("no_model_calls") is not True):
                raise ValueError("LOCAL_WORKER_RESULT_UNVERIFIED")
            if expected_dependencies is not None:
                after=read_json(board_path)
                refreshed={r.get("id"):r for r in after["tasks"] if isinstance(r,dict)}
                if registered_dependency_revision(deps,refreshed,root)!=(
                        expected_dependencies.get(work_id)):
                    results.append({"work_id":work_id,
                                    "status":"DEPENDENCY_CHANGED_DURING_LOCAL_PROBE",
                                    "attempted":True})
                    continue
            evidence=Path(result["evidence"]).resolve(strict=True)
            proof=read_json(evidence)
            if (evidence.parent!=root
                    or proof.get("schema")!="TAKY_LOCAL_WORK_SLICE_V1"
                    or proof.get("task_id")!=work_id
                    or proof.get("portfolio_done") is not False):
                raise ValueError("LOCAL_PROOF_NOT_DONE_SAFE")
            if (expected_dependencies is not None and
                    (not isinstance(proof.get("inputs"),dict) or
                     proof["inputs"].get("registered_dependency_revision") !=
                        expected_dependencies.get(work_id))):
                raise ValueError("LOCAL_PROOF_DEPENDENCY_NOT_BOUND")
            if synthetic_claim is not None:
                claimed["state"]="LOCAL_PROBE_EVIDENCED_NOT_PORTFOLIO_DONE"
                claimed["evidence_sha256"]=hashlib.sha256(evidence.read_bytes()).hexdigest()
                tmp=local/("taky-registered-claim-update-"+uuid4().hex+".tmp")
                try:
                    with tmp.open("x",encoding="utf-8") as out:
                        json.dump(claimed,out,ensure_ascii=False)
                    if (synthetic_claim.is_symlink() or getattr(
                            synthetic_claim,"is_junction",lambda:False)()):
                        raise ValueError("REGISTERED_CLAIM_REPARSE")
                    os.replace(tmp,synthetic_claim)
                finally:
                    tmp.unlink(missing_ok=True)
            results.append({"work_id":work_id,
                            "status":"LOCAL_DIAGNOSIS_EVIDENCED_NOT_DONE",
                            "local_result_state":proof.get("state"),
                            "evidence_sha256":hashlib.sha256(
                                evidence.read_bytes()).hexdigest(),
                            "attempted":worker_launched})
        except CanonicalPreclaimDependencyHold as error:
            results.append({"work_id":work_id,
                            "status":"DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED",
                            "gate_observed_dependency_revision":(
                                error.observed_revision or "UNAVAILABLE"),
                            "attempted":False})
        except CanonicalPreclaimSourceHold as error:
            results.append({"work_id":work_id,
                            "status":"EXISTING_CANONICAL_GATE_HOLD",
                            "gate_route":"LOCAL_INPUT_PROVENANCE_HOLD",
                            "gate_input_error_type":error.source_error_type,
                            "attempted":False})
        except (OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
            results.append({"work_id":work_id,
                            "status":"SAFE_LOCAL_RECOVERY_REQUIRED",
                            "error_class":type(error).__name__,
                            "attempted":worker_launched})
    deferred=[r["work_id"] for r in results if r["status"] in {
        "WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE",
        "CANONICAL_AUTHORITY_CHANGED",
        "EXISTING_CANONICAL_GATE_HOLD",
        "SAFE_LOCAL_RECOVERY_REQUIRED",
        "EXISTING_LOCAL_PROBE_NOT_DEPENDENCY_BOUND",
        "DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED",
        "DEPENDENCY_CHANGED_DURING_LOCAL_PROBE",
        "REGISTERED_WORKER_ALREADY_CLAIMED",
    }]
    summary={
        "schema":"TAKY_GOAL_QUEUE_OBSERVATION_V2",
        "queue_id":queue_id,
        "status":("REGISTERED_LOCAL_TASKS_PARTIALLY_DEFERRED" if deferred
                  else "REGISTERED_LOCAL_TASKS_OBSERVED"),
        "items_total":len(admitted),
        "items_executed":sum(1 for r in results if r["attempted"]),
        "items_deferred":len(deferred),
        "deferred_work_ids":deferred,
        "items":results,
        "goals_verified_done":0,
        "model_calls":0,
        "authority_updated":False,
    }
    from uuid import uuid4
    receipt=local/("taky-goal-queue-"+uuid4().hex+".json")
    try:
        with receipt.open("x",encoding="utf-8") as out:
            json.dump(summary,out,ensure_ascii=False,indent=2)
        if json.loads(receipt.read_text(encoding="utf-8"))!=summary:
            raise ValueError("QUEUE_EVIDENCE_READBACK_FAILED")
        summary["local_queue_receipt"]=str(receipt.relative_to(repo))
    except (OSError,ValueError):
        summary["status"]="QUEUE_RECEIPT_PERSISTENCE_FAILED"
    return summary
