#!/usr/bin/env python3
"""Choose and execute an existing, dependency-ready TAKY local work slice.

Never upgrades a portfolio task, calls models, pushes, deploys, or edits app/UI/audio.
Executor allowlist means this action can run *known* read-only checks only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from TAKY_ORCHESTRATION_RECONCILE import DEFAULT_BOARD, read_json
from TAKY_ORCHESTRATION_LOCAL_WORKERS import WORKERS as LOCAL_READONLY_WORKERS
from TAKY_ORCHESTRATION_OUTCOME_WORKERS import OUTCOME_READONLY_WORKERS
ALL_READONLY_WORKERS = {**LOCAL_READONLY_WORKERS, **OUTCOME_READONLY_WORKERS}

TAKY = Path(r"D:\Git PWA\TAKY")
GUARDS = TAKY / "ENFORCEMENT"
EVIDENCE = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\80_EVIDENCE")
EXCLUDED_WORDS = ("ARCHIGROW", "ARCHI GROW", "VOICE", "AUDIO", "SPEECH", "PRONUNCIATION",
                  "UI", "VISUAL", "DESIGN", "GALLERY", "ASSET", "CREW", "FAMILY", "APPROVED SCREEN")
NON_FINAL = {"NOT_STARTED","DISCOVERY","EVALUATION","READY","IMPLEMENTING"}
PRIORITIES = {"P0":0,"P1":1,"P2":2}
LOCAL_EXECUTORS = {"CLN-002":"LOCAL_CANONICAL_CURRENT_READBACK",
                   "INT-001":"LOCAL_SIGNED_WORK_HANDOFF_READBACK",
                   "CLN-009":"LOCAL_TOOLCHAIN_AND_PATH_AUDIT",
                   "MCP-002":"LOCAL_MCP_LAUNCHER_PREFLIGHT",
                   "CLN-001":"LOCAL_WORKTREE_READONLY_INVENTORY",
                   "MCP-001":"LOCAL_MCP_CONFIG_READONLY_INVENTORY",
                   "SKL-001":"LOCAL_SKILL_READONLY_CATALOG",
                   "FAMILY-DURABLE-001":"LOCAL_PRODUCT_OUTCOME_EVIDENCE_READBACK",
                   "OPS-001":"LOCAL_SOURCE_ADOPTION_EVIDENCE_READBACK"}
# Pure read-only diagnostics may proceed while a parent inventory is underway.
# Incomplete dependencies remain visible and forbid completion or promotion.
SAFE_PRECHECK_WITH_PENDING_DEPS = {"CLN-002","INT-001","MCP-002","CLN-001","MCP-001","SKL-001",
                                   "FAMILY-DURABLE-001","OPS-001"}
# Explicit read-only worker IDs may inspect existing evidence; this grants no
# permission to edit a family product, audio, source or project CURRENT.
READ_ONLY_OUTCOME_OBSERVERS = {"CLN-002","INT-001","FAMILY-DURABLE-001","OPS-001"}

def decision(task: dict, states: dict[str,str]) -> tuple[str,list[str]]:
    tid = str(task.get("id",""))
    state = str(task.get("status",""))
    if state not in NON_FINAL: return "NOT_ACTIVE", []
    if task.get("approval_required") is True: return "REQUIRES_APPROVAL", []
    descriptor = " ".join(str(task.get(k,"")) for k in ("title","category","id")).upper()
    if tid not in READ_ONLY_OUTCOME_OBSERVERS and any(
        re.search(r"(?<![A-Z0-9])"+re.escape(word)+r"(?![A-Z0-9])",descriptor)
        for word in EXCLUDED_WORDS
    ):
        return "USER_HOLD_UI_AUDIO_ARCHI_FAMILY", []
    deps = [str(x) for x in task.get("dependencies",[]) or []]
    unresolved = [x for x in deps if states.get(x)!="VERIFIED" and states.get(x)!="ADOPTED"]
    if unresolved and tid not in SAFE_PRECHECK_WITH_PENDING_DEPS:
        return "NEEDS_DEPENDENCY_EVIDENCE", unresolved
    if tid not in LOCAL_EXECUTORS: return "LOCAL_EXECUTOR_NOT_BOUND", unresolved
    return "READY_FOR_LOCAL_EXECUTION", unresolved

def live_outcome_provenance_fingerprint(work_id: str, workbench: Path) -> str:
    """Invalidate a cached read-only PASS if an actual observed input changes.

    The receipt itself is hashed separately. Never trust a source path for
    arbitrary filesystem read: all paths are confined to exact existing local
    source/evidence trees. This fingerprint is NOT a semantic review or DONE.
    """
    evidence_root = workbench / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
    receipt = read_json(evidence_root / "PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json")
    targets: dict[str, Path] = {}
    if work_id == "FAMILY-DURABLE-001":
        base = TAKY.parent
        entrypoints = (
            "TAKY-MOBILE/index.html", "Ready & Set/index.html",
            "Hide & Seek/index.html", "Snap & Pop/index.html",
            "Play Camp/src/App.tsx", "Play Camp/src/main.tsx",
            "Play Camp/src/lib/readyBridge.ts",
        )
        observed = receipt.get("browser_journey") or {}
        for name in entrypoints:
            targets[name] = base / name
        pins = {
            "result_ref": base / "TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/approval-hold-result.json",
            "screenshot_ref": base / "TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/05-play-camp.png",
            "ready_partial_screenshot_ref": base / "TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/06-ready-approval-hold-result.png",
            "mobile_partial_screenshot_ref": base / "TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/07-mobile-approval-hold-return.png",
            "test_source_ref": base / "TAKY-MOBILE/tests/learning-loop-multi-specialist-roundtrip-e2e.cjs",
            "audio_authority_ref": base / "Play Camp/src/data/playCampPronunciationAssets.ts",
        }
        for key, target in pins.items():
            if Path(str((observed.get(key) or {}).get("path") or "")).resolve() != target.resolve():
                raise ValueError("PRODUCT_PROVENANCE_PATH_NOT_PINNED:" + key)
            targets[key] = target
        manifest = observed.get("pinned_entrypoint_sources_at_local_observation")
        if (not isinstance(manifest, list)
                or [str((entry or {}).get("path")) for entry in manifest]
                != [str(base / name).replace("\\", "/") for name in entrypoints]):
            raise ValueError("PRODUCT_ENTRYPOINT_PROVENANCE_MISMATCH")
    elif work_id == "OPS-001":
        source_root = TAKY.parent / "TAKY-SOURCE-VAULT"
        original = read_json(evidence_root / "SOURCE_FIRST_FROZEN_UNITS_V2_20261023.json")
        safe_roots = (
            source_root / "reports/site_watch/mining_generations",
            source_root / "data/site_watch/snapshots",
            source_root / "data/site_watch/local_content_candidates",
        )
        nodes = [original.get("mining_generation_ref")]
        for entry in original.get("items") or []:
            if not isinstance(entry, dict):
                raise ValueError("SOURCE_PROVENANCE_MANIFEST_INVALID")
            nodes.extend({"path": entry.get(key)}
                         for key in ("raw_path", "text_path"))
        for node in nodes:
            if not isinstance(node, dict) or not isinstance(node.get("path"), str):
                raise ValueError("SOURCE_PROVENANCE_ENTRY_INVALID")
            file = Path(node["path"]).resolve(strict=True)
            if (not file.is_file()
                    or not any(file.is_relative_to(root.resolve(strict=True)) for root in safe_roots)
                    or file.stat().st_size > 24 * 1024 * 1024):
                raise ValueError("SOURCE_PROVENANCE_TARGET_UNSAFE")
            targets[str(file)] = file
    else:
        raise ValueError("NOT_AN_OUTCOME_PROVENANCE_WORKER")
    entries = [(name, sha(target)) for name, target in sorted(targets.items())]
    return hashlib.sha256(json.dumps(entries, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


def telemetry_hour_bucket(at: datetime | None=None) -> str:
    """Bound freshness of live process observations to one UTC hour."""
    value=at or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("TELEMETRY_OBSERVATION_TIME_MUST_BE_AWARE")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")


def evidence_signature(board: dict, work_id: str) -> tuple[dict,str]:
    task=next((t for t in board["tasks"] if t.get("id")==work_id),None)
    if not task: raise ValueError("SOURCE_TASK_NOT_FOUND")
    # Evidence receipts and continuity notes grow as a task runs. They do NOT
    # change its executable contract. Hashing them made each added receipt
    # invalidate the earlier read-only proof and trigger unnecessary reruns.
    # All substantive task fields (including guards, approvals and owner) stay pinned.
    contract={k:v for k,v in task.items() if k not in ("evidence","resume_checkpoint")}
    inputs={"task_sha256":hashlib.sha256(json.dumps(contract,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
    if work_id=="CLN-009":
        inputs["path_guard"]=sha(GUARDS/"workspace_cleanup_path_guard.py")
        inputs["toolchain_guard"]=sha(GUARDS/"taky_toolchain_paths_guard.py")
    elif work_id=="MCP-002":
        inputs["executor_source_sha256"]=sha(Path(__file__))
        inputs["mcp_launcher_guard"]=sha(GUARDS/"taky_mcp_executable_preflight.py")
        inputs["process_telemetry_probe"]="MCP_PROCESS_TELEMETRY_V1"
        # A live CPU/process observation is not a timeless PASS. Retire the
        # existing local receipt at each UTC hour boundary, without rerunning
        # model calls or rewriting any earlier immutable evidence.
        inputs["telemetry_observation_utc_hour"]=telemetry_hour_bucket()
    elif work_id in LOCAL_READONLY_WORKERS:
        worker=Path(__file__).with_name("TAKY_ORCHESTRATION_LOCAL_WORKERS.py")
        inputs["worker_sha256"]=sha(worker)
        if work_id in ("MCP-001","SKL-001"):
            inputs["toolchain_guard"]=sha(GUARDS/"taky_toolchain_paths_guard.py")
        if work_id=="CLN-001":
            # Fast signature from Git metadata; full worktree enumeration happens
            # only in the executor, never for every queue-status read.
            from TAKY_ORCHESTRATION_LOCAL_WORKERS import ROOT, REPOS
            metadata=[]
            for repo_name in REPOS:
                git_marker=ROOT/repo_name/".git"
                head=git_marker/"HEAD" if git_marker.is_dir() else git_marker
                data=head.read_bytes() if head.is_file() else b"MISSING"
                metadata.append((repo_name,hashlib.sha256(data).hexdigest()))
            inputs["git_metadata_digest"]=hashlib.sha256(
                json.dumps(metadata,sort_keys=True).encode()).hexdigest()
    elif work_id in READ_ONLY_OUTCOME_OBSERVERS:
        observer = Path(__file__).with_name("TAKY_ORCHESTRATION_OUTCOME_WORKERS.py")
        inputs["worker_sha256"] = sha(observer)
        workbench = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
        inputs["outcome_reader_sha256"] = sha(
            workbench / "00_CONTROL" / "RECONCILE_EXECUTION_REALITY.py")
        inputs["outcome_receipt_sha256"] = sha(
            workbench / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
            / "PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json")
        if work_id in ("FAMILY-DURABLE-001", "OPS-001"):
            inputs["live_observed_inputs_sha256"] = live_outcome_provenance_fingerprint(
                work_id, workbench)
        if work_id in ("CLN-002","INT-001"):
            inputs["project_registry_sha256"] = sha(workbench / "00_CONTROL" / "PROJECT_REGISTRY.json")
            inputs["assignments_sha256"] = sha(workbench / "00_CONTROL" / "AI_WORK_ASSIGNMENTS.json")
            inputs["orchestration_reconciler_sha256"] = sha(Path(__file__).with_name("TAKY_ORCHESTRATION_RECONCILE.py"))
            inputs["project_current_shas"] = {
                project: sha(workbench / config["workbench_path"] / "PROJECT_CURRENT.json")
                for project, config in sorted(
                    read_json(workbench / "00_CONTROL" / "PROJECT_REGISTRY.json")["projects"].items())
            }
        if work_id == "OPS-001":
            inputs["frozen_source_sha256"] = sha(
                workbench / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
                / "SOURCE_FIRST_FROZEN_UNITS_V2_20261023.json")
            source_vault = TAKY.parent / "TAKY-SOURCE-VAULT"
            inputs["source_owner_reader_sha256"] = sha(
                source_vault / "BUILD_SITE_INDEX_OWNER_EVIDENCE_BUNDLE.py")
            inputs["source_owner_queue_sha256"] = sha(
                source_vault / "data/site_watch/indexing_review"
                / "INDEX_OWNER_EVIDENCE_BUNDLE_CURRENT.json")
            for label, filename in (
                ("source_first_gpt_review", "SITE_2E081_SOURCE_FIRST_GPT_INDEPENDENT_20261024.json"),
                ("source_first_codex_review", "SITE_2E081_SOURCE_FIRST_CODEX_INDEPENDENT_20261024.json"),
                ("source_first_comparison", "SITE_2E081_PRELIMINARY_SOURCE_COMPARISON_20261024.json"),
            ):
                inputs[label + "_sha256"] = sha(
                    workbench / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE" / filename)
    else:
        raise ValueError("LOCAL_EXECUTOR_NOT_BOUND")
    digest=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()[:20]
    return inputs,digest

def choose(board: dict, evidence: Path | None=None) -> dict:
    rows=board.get("tasks")
    if not isinstance(rows,list): raise ValueError("INVALID_PORTFOLIO")
    ids=[r.get("id") for r in rows]
    if len(ids)!=len(set(ids)): raise ValueError("DUPLICATE_PORTFOLIO_ID")
    states={r["id"]:r.get("status") for r in rows}
    considered=[]
    for t in rows:
        reason,unresolved=decision(t,states)
        considered.append({"task_id":t["id"],"title":t.get("title"),"status":t.get("status"),
            "priority":t.get("priority"),"route":reason,"unresolved":unresolved})
    if evidence is not None:
        for row in considered:
            if row["route"]!="READY_FOR_LOCAL_EXECUTION":continue
            try:
                inputs,digest=evidence_signature(board,row["task_id"])
            except (OSError,ValueError,KeyError,TypeError) as exc:
                # One stale source must not halt every independent local task.
                # It never becomes eligible on missing/unsafe provenance.
                row["route"]="LOCAL_INPUT_PROVENANCE_HOLD"
                row["next_action"]="RECHECK_THIS_TASK_INPUTS_WITH_CANONICAL_SOURCE"
                row["input_error_type"]=type(exc).__name__
                continue
            receipt=evidence/("TAKY_LOCAL_WORK_"+row["task_id"]+"_"+digest+".json")
            if receipt.is_file() or receipt.is_symlink() or getattr(
                    receipt,"is_junction",lambda:False)():
                # Corrupt/stale evidence cannot strand every independent
                # registered task: hold ONLY the affected work ID.
                try:
                    if receipt.is_symlink() or getattr(
                            receipt,"is_junction",lambda:False)():
                        raise ValueError("LOCAL_EVIDENCE_REPARSE")
                    proof=read_json(receipt)
                    if (proof.get("schema")!="TAKY_LOCAL_WORK_SLICE_V1"
                            or proof.get("task_id")!=row["task_id"]
                            or proof.get("inputs")!=inputs):
                        raise ValueError("EXISTING_EVIDENCE_ID_CONFLICT")
                    row["existing_evidence"]=str(receipt)
                    row["historical_only"]=True
                    row["live_runtime_state"]="NOT_RECHECKED"
                    if proof.get("state")=="LOCAL_SLICE_FINDINGS_NEED_ACTION":
                        row["route"]="LOCAL_SLICE_NEEDS_CORRECTION"
                        row["next_action"]="INSPECT_LOCAL_FINDINGS_THEN_RERUN_CHANGED_SCOPE"
                    elif proof.get("state")=="LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE":
                        row["route"]="LOCAL_SLICE_ALREADY_EVIDENCED"
                        row["next_action"]="INDEPENDENT_SCOPE_REVIEW_OR_NEXT_TASK"
                    else:
                        raise ValueError("UNRECOGNIZED_LOCAL_EVIDENCE_STATE")
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    row["route"]="LOCAL_EVIDENCE_INTEGRITY_HOLD"
                    row["input_error_type"]=type(exc).__name__
                    row["next_action"]="RECONCILE_EXISTING_UNTRUSTED_RECEIPT_NO_OVERWRITE"
    ready=[r for r in considered if r["route"]=="READY_FOR_LOCAL_EXECUTION"]
    ready.sort(key=lambda x:(PRIORITIES.get(x["priority"],9),
                             0 if x["status"]=="IMPLEMENTING" else 1,x["task_id"]))
    return {"schema":"TAKY_LOCAL_NEXT_WORK_V1","selected":ready[0] if ready else None,
            "eligible_count":len(ready),"considered":considered,
            "no_model_calls":True,"no_approval_or_hold_bypassed":True}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_checks(work_id: str, board: Path, evidence: Path, timeout: int=85,
               *, dependency_revision: str | None=None) -> dict:
    if work_id not in LOCAL_EXECUTORS: raise ValueError("UNSUPPORTED_LOCAL_EXECUTOR")
    # Admission and signed input identity MUST come from one same snapshot.
    # Previously a second board read could silently adopt a newly changed
    # approval flag after a successful eligibility check (TOCTOU).
    original_board=read_json(board)
    preflight=choose(original_board)
    row=next((r for r in preflight["considered"] if r["task_id"]==work_id),None)
    if row is None or row["route"]!="READY_FOR_LOCAL_EXECUTION":
        raise ValueError("TASK_NOT_DEPENDENCY_READY_OR_HELD")
    guard1=GUARDS/"workspace_cleanup_path_guard.py"
    guard2=GUARDS/"taky_toolchain_paths_guard.py"
    inputs,digest=evidence_signature(original_board,work_id)
    if dependency_revision is not None:
        # A caller-supplied digest is only a proposed revision. The canonical
        # local worker independently re-reads the source proof before executing.
        dep_module=str(Path(__file__).resolve().parents[1]/"ENFORCEMENT")
        if dep_module not in sys.path:
            sys.path.insert(0,dep_module)
        from taky_registered_goal_queue import registered_dependency_revision
        original_index={t.get("id"):t for t in original_board["tasks"]
                        if isinstance(t,dict)}
        observed=registered_dependency_revision(
            original_index[work_id].get("dependencies",[]),
            original_index,evidence)
        if observed!=dependency_revision:
            raise ValueError("REGISTERED_DEPENDENCY_SOURCE_NOT_PINNED")
        # A dependency-triggered diagnostic is a *different evidence scope*
        # from a previously cached precheck. Pin the canonical source revision
        # without changing the ordinary worker receipt format/identity.
        if (not isinstance(dependency_revision,str) or
                re.fullmatch(r"[0-9a-f]{64}",dependency_revision) is None
                or not row.get("unresolved")==[]):
            raise ValueError("DEPENDENCY_READONLY_PROBE_NOT_BOUND")
        inputs={**inputs,"registered_dependency_revision":dependency_revision}
        digest=hashlib.sha256(json.dumps(
            inputs,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20]
    output=evidence/("TAKY_LOCAL_WORK_"+work_id+"_"+digest+".json")
    if output.is_file():
        existing=read_json(output)
        if (existing.get("task_id")==work_id and existing.get("inputs")==inputs
            and existing.get("schema")=="TAKY_LOCAL_WORK_SLICE_V1"):
            return {"status":"REUSED_EXISTING_EVIDENCE","task_id":work_id,
                    "result":existing.get("state"),"evidence":str(output),
                    "no_model_calls":True}
        raise ValueError("EXISTING_EVIDENCE_ID_CONFLICT")
    # ONE durable dispatch claim for ALL callers: original CLI, scheduler,
    # registered V2 and dependency wake. A missing receipt after an attempted
    # worker is OUTCOME_UNKNOWN, never permission to execute it again.
    trust_dir=str(Path(__file__).resolve().parents[1]/"ENFORCEMENT")
    if trust_dir not in sys.path:
        sys.path.insert(0,trust_dir)
    from taky_registered_goal_queue import registered_dependency_revision
    task_index={t.get("id"):t for t in original_board["tasks"] if isinstance(t,dict)}
    deps=task_index[work_id].get("dependencies",[]) or []
    observed_revision=registered_dependency_revision(deps,task_index,evidence)
    if dependency_revision is not None and observed_revision!=dependency_revision:
        raise ValueError("DEPENDENCY_CLAIM_REVISION_DRIFT")
    # Pending prechecks deliberately use a different version key, preserving
    # limited inventory work without elevating it to a verified dependency.
    revision_key=("VERIFIED:"+observed_revision if observed_revision
                  else "PENDING_PRECHECK:"+digest)
    _canonical=(board.resolve()==DEFAULT_BOARD.resolve() and
                evidence.resolve()==EVIDENCE.resolve())
    expected_parent=TAKY if _canonical else board.parent.resolve()
    claims=(expected_parent/".local")
    if not claims.exists() and not _canonical:
        claims.mkdir()
    if (not claims.is_dir() or claims.is_symlink()
            or getattr(claims,"is_junction",lambda:False)()
            or claims.resolve().parent!=expected_parent.resolve()):
        raise ValueError("CANONICAL_DURABLE_CLAIM_SCOPE_UNAVAILABLE")
    import uuid
    token=hashlib.sha256((work_id+"|"+revision_key).encode()).hexdigest()[:24]
    claim=claims/("taky-canonical-worker-"+work_id+"-"+token+".json")
    claimed={"schema":"TAKY_CANONICAL_WORK_CLAIM_V1","work_id":work_id,
             "revision":revision_key,"input_digest":digest,
             "state":"CLAIMED_OUTCOME_UNKNOWN"}
    try:
        with claim.open("x",encoding="utf-8") as saved:
            json.dump(claimed,saved,ensure_ascii=False)
    except FileExistsError:
        raise ValueError("CANONICAL_WORK_ALREADY_CLAIMED_NO_RETRY")
    # Subprocess arguments are constants, no shell, no provider, bounded runtime.
    results=[]
    if work_id=="MCP-002":
        results=run_mcp_launcher_preflight(timeout)
    elif work_id in ALL_READONLY_WORKERS:
        results=ALL_READONLY_WORKERS[work_id](timeout)
    else:
        results=run_path_and_toolchain_checks(guard1,guard2,timeout)
    final_board=read_json(board)
    final_plan=choose(final_board)
    final_row=next((r for r in final_plan["considered"]
                    if r["task_id"]==work_id),None)
    if final_row is None or final_row["route"]!="READY_FOR_LOCAL_EXECUTION":
        raise ValueError("TASK_ADMISSION_REVOKED_DURING_AUDIT")
    final_inputs=evidence_signature(final_board,work_id)[0]
    if dependency_revision is not None:
        final_inputs={**final_inputs,
                      "registered_dependency_revision":dependency_revision}
    if inputs!=final_inputs:
        raise ValueError("INPUT_CHANGED_DURING_AUDIT")
    if dependency_revision is not None:
        # No current-local evidence may be published for a stale parent proof.
        final_index={t.get("id"):t for t in final_board["tasks"]
                     if isinstance(t,dict)}
        observed=registered_dependency_revision(
            final_index[work_id].get("dependencies",[]),
            final_index,evidence)
        if observed!=dependency_revision:
            raise ValueError("REGISTERED_DEPENDENCY_CHANGED_DURING_AUDIT")
    all_ok=all(r["status"]=="PASS" for r in results)
    payload={"schema":"TAKY_LOCAL_WORK_SLICE_V1","task_id":work_id,
        "state":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE" if all_ok else "LOCAL_SLICE_FINDINGS_NEED_ACTION",
        "executed_at":datetime.now(timezone.utc).isoformat(),
        "source_work_status_unchanged":True,"inputs":inputs,"checks":results,
        "pending_dependencies_at_execution":row.get("unresolved",[]),
        "work_owner_claimed_by_this_receipt":False,
        "no_model_calls":True,"no_external_provider_calls":True,
        "no_push_merge_deploy":True,"portfolio_done":False,
        "remaining_work":(
            "MCP protocol handshakes and live CPU rate limits remain unverified" if work_id=="MCP-002" else
            "Local file/skill/connector inventory is not independent portfolio completion" if work_id in LOCAL_READONLY_WORKERS else
            " ; ".join(str(c.get("next_action")) for c in results if c.get("next_action"))
            if work_id in READ_ONLY_OUTCOME_OBSERVERS else
            "Independent scope review and remaining CLN-009 consumers still unverified")}
    evidence.mkdir(parents=True,exist_ok=True)
    try:
        with output.open("x",encoding="utf-8") as stream:
            json.dump(payload,stream,ensure_ascii=False,indent=2)
    except FileExistsError:
        raise ValueError("CONCURRENT_EVIDENCE_WRITER")
    # Completion here proves only a durable LOCAL precheck, never portfolio
    # DONE. Keep the claim if any persistence/verification is ambiguous.
    claimed["state"]="LOCAL_PROBE_EVIDENCED_NOT_PORTFOLIO_DONE"
    claimed["evidence_sha256"]=hashlib.sha256(output.read_bytes()).hexdigest()
    temp_claim=claims/("taky-canonical-worker-update-"+uuid.uuid4().hex+".tmp")
    try:
        with temp_claim.open("x",encoding="utf-8") as out:
            json.dump(claimed,out,ensure_ascii=False)
        if claim.is_symlink() or getattr(claim,"is_junction",lambda:False)():
            raise ValueError("CANONICAL_CLAIM_REPARSE")
        os.replace(temp_claim,claim)
    finally:
        temp_claim.unlink(missing_ok=True)
    return {"status":payload["state"],"task_id":work_id,"evidence":str(output),
            "checks":results,"no_model_calls":True}

def run_path_and_toolchain_checks(guard1: Path,guard2: Path,timeout: int) -> list[dict]:
    results=[]
    commands=[[sys.executable,"-B","-X","utf8",str(guard1)]]
    cp=subprocess.run(commands[0],capture_output=True,text=True,
                      encoding="utf-8",errors="replace",timeout=timeout,check=False)
    if cp.returncode not in (0,2): raise ValueError("PATH_GUARD_PROCESS_ERROR")
    check=json.loads(cp.stdout)
    if check.get("status") not in ("PASS","FAIL") or check.get("no_changes_made") is not True:
        raise ValueError("PATH_GUARD_RESULT_INVALID")
    results.append({"name":"WORKSPACE_PATH_AUTHORITY","status":check["status"],
                    "errors":check.get("errors",[]),"evidence":check.get("evidence",{}),
                    "exit_code":cp.returncode})
    with tempfile.TemporaryDirectory(prefix="TAKY_LOCAL_TOOLCHAIN_AUDIT_") as td:
        temp_output=Path(td)/"audit.json"
        script=(
            "import importlib.util,sys; from pathlib import Path;"
            "spec=importlib.util.spec_from_file_location('scoped_toolchain_audit',sys.argv[1]);"
            "mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);"
            "mod.OUT=Path(sys.argv[2]);mod.main()"
        )
        tool=subprocess.run([sys.executable,"-B","-X","utf8","-c",script,
                             str(guard2),str(temp_output)],
                            capture_output=True,text=True,encoding="utf-8",
                            errors="replace",timeout=timeout,check=False)
        if tool.returncode != 0 or not temp_output.is_file():
            raise ValueError("TOOLCHAIN_GUARD_EXECUTION_FAILED")
        parsed=read_json(temp_output)
        if parsed.get("schema")!="TAKY_TOOLCHAIN_PATHS_GUARD_V1" or parsed.get("read_only") is not True:
            raise ValueError("TOOLCHAIN_PROOF_INVALID")
        results.append({"name":"CLAUDE_CODEX_MCP_PATHS","status":parsed.get("status"),
            "checked_paths":len(parsed.get("checks",{})),"skills":len(parsed.get("skills",[])),
            "broken":parsed.get("broken",[]),"external_calls":False})
    return results

def run_mcp_launcher_preflight(timeout: int) -> list[dict]:
    started=time.monotonic()
    source=GUARDS/"taky_mcp_executable_preflight.py"
    with tempfile.TemporaryDirectory(prefix="TAKY_LOCAL_MCP_PROBE_") as td:
        report=Path(td)/"launcher.json"
        code=(
            "import importlib.util,sys;from pathlib import Path;"
            "spec=importlib.util.spec_from_file_location('taky_launcher_probe',sys.argv[1]);"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "m.OUT=Path(sys.argv[2]);m.main()"
        )
        proc=subprocess.run([sys.executable,"-B","-X","utf8","-c",code,
                             str(source),str(report)],capture_output=True,text=True,
                            encoding="utf-8",errors="replace",timeout=timeout,check=False)
        if proc.returncode not in (0,2) or not report.is_file():
            raise ValueError("MCP_LAUNCHER_PROBE_FAILED")
        result=read_json(report)
        if result.get("schema")!="TAKY_MCP_EXECUTABLE_PREFLIGHT_V1" or result.get("external_call") is not False:
            raise ValueError("MCP_LAUNCHER_PROOF_INVALID")
        return [{"name":"MCP_LAUNCHER_REFERENCES",
                 "status":"PASS" if result.get("state")=="REFERENCES_PRESENT" else "HOLD",
                 "launcher_count":len(result.get("launchers",[])),
                 "missing":result.get("missing",[]),
                 "protocol_handshake_verified":False,
                 "cpu_limits_verified":False,
                 "cpu_budget":"UNSET_UNVERIFIED"},
                run_process_telemetry(max(0.0,timeout-(time.monotonic()-started)))]

TELEMETRY_PREFIXES = ("claude","codex","python")
TELEMETRY_MAX_ROWS = 100

def sample_processes(timeout: int) -> dict[int,dict]:
    # Constant PowerShell script, no shell, no command lines, no environment, no network.
    script=("$ErrorActionPreference='Stop';"
            "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
            "try {$rows=Get-Process -ErrorAction Stop | "
            "Where-Object {$_.ProcessName -match '^(claude|codex|python)'} | ForEach-Object {"
            "$st=$null;try{$st=$_.StartTime.ToUniversalTime().Ticks}catch{};"
            "[pscustomobject]@{pid=$_.Id;name=$_.ProcessName;cpu=$_.CPU;ws=$_.WorkingSet64;start=$st}"
            "}; @($rows) | ConvertTo-Json -Compress}"
            "catch {[Console]::Error.WriteLine('PROCESS_ENUMERATION_FAILED');exit 2}")
    cp=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",script],
                      capture_output=True,text=True,encoding="utf-8",errors="replace",
                      timeout=timeout,check=False)
    if cp.returncode!=0: raise ValueError("PROCESS_SAMPLE_FAILED")
    text=cp.stdout.strip()
    rows=json.loads(text) if text else []
    if isinstance(rows,dict): rows=[rows]
    found={}
    for r in rows:
        name=str(r.get("name",""))
        if not name.lower().startswith(TELEMETRY_PREFIXES): continue
        found[int(r["pid"])]={"name":name,"cpu":r.get("cpu"),"ws":r.get("ws"),"start":r.get("start")}
    return found

def run_process_telemetry(timeout: int, interval: float=1.0) -> dict:
    """Observation only: two bounded samples, no threshold, no MCP ownership claim."""
    base={"name":"MCP_PROCESS_TELEMETRY_OBSERVATION","observation_only":True,
          "target_name_prefixes":list(TELEMETRY_PREFIXES),"requested_interval_seconds":interval,
          "method":"powershell Get-Process two-sample","cpu_threshold_applied":False,
          "process_identity_proves_mcp_owner":False,"command_lines_collected":False,
          "cpu_budget":"UNSET_UNVERIFIED","cpu_limits_verified":False,
          "protocol_handshake_verified":False,"external_calls":False,
          "cpu_rate_is_estimate":True,"timing_method":"subprocess_midpoints_approximate"}
    if os.name!="nt":
        return {**base,"status":"HOLD","reason":"PLATFORM_NOT_WINDOWS_GET_PROCESS_UNAVAILABLE"}
    deadline=time.monotonic()+max(0.0,timeout)
    try:
        budget=deadline-time.monotonic()
        if budget<=0: raise TimeoutError("PROCESS_SAMPLE_TIME_BUDGET_EXHAUSTED")
        a0=time.perf_counter(); first=sample_processes(budget); a1=time.perf_counter()
        if deadline-time.monotonic()<=interval: raise TimeoutError("PROCESS_SECOND_SAMPLE_BUDGET_EXHAUSTED")
        time.sleep(interval)
        budget=deadline-time.monotonic()
        if budget<=0: raise TimeoutError("PROCESS_SECOND_SAMPLE_BUDGET_EXHAUSTED")
        b0=time.perf_counter(); second=sample_processes(budget); b1=time.perf_counter()
    except (OSError,ValueError,TimeoutError,subprocess.SubprocessError) as exc:
        return {**base,"status":"HOLD","reason":"PROCESS_SAMPLE_UNAVAILABLE:"+type(exc).__name__}
    measured=((b0+b1)/2)-((a0+a1)/2)
    me=os.getpid()
    rows=[]; reused=0; unverified_start=0; cpu_missing=0
    for pid in sorted(set(first)&set(second)):
        s1,s2=first[pid],second[pid]
        if s1["name"]!=s2["name"] or (s1["start"] is not None and s2["start"] is not None and s1["start"]!=s2["start"]):
            reused+=1; continue
        identity="START_TIME_MATCHED" if s1["start"] is not None and s2["start"] is not None else "START_TIME_UNAVAILABLE"
        if identity!="START_TIME_MATCHED": unverified_start+=1
        c1,c2=s1["cpu"],s2["cpu"]
        delta=None
        if identity=="START_TIME_MATCHED" and isinstance(c1,(int,float)) and isinstance(c2,(int,float)) and c2>=c1:
            delta=round(c2-c1,4)
        else:
            cpu_missing+=1
        rows.append({"pid":pid,"process_name":s2["name"],"identity_check":identity,
            "is_this_probe":pid==me,"cpu_seconds":c2 if isinstance(c2,(int,float)) else None,
            "cpu_seconds_delta":delta,
            "cpu_seconds_per_wall_second":round(delta/measured,4) if delta is not None and measured>0 else None,
            "resident_mb_first":round(s1["ws"]/1048576,1) if isinstance(s1["ws"],(int,float)) else None,
            "resident_mb":round(s2["ws"]/1048576,1) if isinstance(s2["ws"],(int,float)) else None})
    truncated=len(rows)>TELEMETRY_MAX_ROWS
    valid_cpu_rows=sum(p["cpu_seconds_delta"] is not None for p in rows)
    quality="PASS" if not rows or valid_cpu_rows>0 else "HOLD"
    return {**base,"status":quality,"cpu_delta_verified_rows":valid_cpu_rows,
            "sample_quality":"NO_MATCHING_PROCESS" if not first and not second else
                             "CPU_DELTA_UNVERIFIED" if quality!="PASS" else "CPU_DELTAS_AVAILABLE",
            "measured_interval_seconds":round(measured,3),
            "sample_durations_seconds":[round(a1-a0,3),round(b1-b0,3)],
            "processes":rows[:TELEMETRY_MAX_ROWS],"processes_truncated":truncated,
            "churn":{"first_sample_count":len(first),"second_sample_count":len(second),
                     "appeared_during_interval":len(set(second)-set(first)),
                     "exited_during_interval":len(set(first)-set(second)),
                     "pid_reuse_excluded":reused,"start_time_unverified":unverified_start,
                     "cpu_unavailable":cpu_missing},
            "note":"One short observation. CPU rates are estimates based on subprocess midpoints; no CPU limit or MCP owner is verified."}

def continue_local(board_path: Path=DEFAULT_BOARD, evidence: Path=EVIDENCE,
                   *, max_actions: int | None=None) -> dict:
    """Work until no new safe local task remains, not until a user says 'go'.

    Failures are reported and the next independent task is tried. Every task
    identity is attempted once per invocation; repeated model calls are absent.
    """
    if max_actions is not None and (type(max_actions) is not int or
                                     not 1<=max_actions<=8):
        raise ValueError("BOUNDED_CONTINUATION_LIMIT_INVALID")
    attempted=set()
    actions=[]
    while True:
        if max_actions is not None and len(attempted)>=max_actions:
            break
        board=read_json(board_path)
        plan=choose(board,evidence)
        candidates=[r for r in plan["considered"] if r["route"]=="READY_FOR_LOCAL_EXECUTION"
                    and r["task_id"] not in attempted]
        candidates.sort(key=lambda x:(PRIORITIES.get(x["priority"],9),
                                     0 if x["status"]=="IMPLEMENTING" else 1,x["task_id"]))
        if not candidates:break
        next_job=candidates[0]
        task_id=next_job["task_id"]
        attempted.add(task_id)
        try:
            outcome=run_checks(task_id,board_path,evidence)
            actions.append({"task_id":task_id,"status":outcome["status"],
                            "evidence":outcome.get("evidence"),
                            "completed_portfolio_task":False})
        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
            # Continue with other independent tasks, without fabricating evidence.
            actions.append({"task_id":task_id,"status":"LOCAL_EXECUTION_NEEDS_RECOVERY",
                            "error_type":type(exc).__name__,
                            "error_code":str(exc)[:150],
                            "completed_portfolio_task":False})
    current=choose(read_json(board_path),evidence)
    return {"schema":"TAKY_LOCAL_CONTINUATION_V1",
            "status":"BOUNDED_LOCAL_CONTINUATION_FINISHED",
            "actions":actions,
            "remaining_ready":current["eligible_count"],
            "max_actions":max_actions,
            "remaining_unbound":sum(x["route"]=="LOCAL_EXECUTOR_NOT_BOUND"
                                    for x in current["considered"]),
            "remaining_dep_wait":sum(x["route"]=="NEEDS_DEPENDENCY_EVIDENCE"
                                     for x in current["considered"]),
            "no_model_calls":True,"portfolio_done_claimed":False,
            "no_push_merge_deploy":True,
            "next_step":"REVIEW_EVIDENCE_AND_BIND_REAL_IMPLEMENTATION_WITH_EXISTING_AUTHORITY"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--board",type=Path,default=DEFAULT_BOARD)
    p.add_argument("--evidence",type=Path,default=EVIDENCE)
    p.add_argument("--perform",action="store_true")
    p.add_argument("--continue",dest="continue_batch",action="store_true")
    args=p.parse_args()
    if args.continue_batch:
        print(json.dumps(continue_local(args.board,args.evidence),ensure_ascii=False))
        return
    board=read_json(args.board)
    plan=choose(board,args.evidence)
    if not args.perform:
        print(json.dumps(plan,ensure_ascii=False))
        return
    selection=plan["selected"]
    if selection is None:
        print(json.dumps({"status":"NO_APPROVED_LOCAL_WORK_READY","no_model_calls":True,"plan":plan},ensure_ascii=False))
        return
    result=run_checks(selection["task_id"],args.board,args.evidence)
    result["selected_work"]=selection
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    main()
