#!/usr/bin/env python3
"""Controlled-runtime TAKY orchestrator.

This is the repository entrypoint for material TAKY execution.
It composes operational rule assimilation + preflight + optional C2S coverage,
then emits the only authorized next route. It does not invoke hosted ChatGPT
automatically and does not execute arbitrary shell commands.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from c2s_preflight_bridge import run as run_c2s_preflight
from codex_task_contract_builder import build as build_codex_task_contract
from executor_transport import build_envelope as build_executor_envelope
from executor_adapter_registry import resolve as resolve_executor_adapter
from execution_checkpoint import guard as guard_checkpoint, persist as persist_checkpoint
from reference_intake_router import route as route_reference_intake
from reference_intake_executor import execute as execute_reference_intake
from reference_acquisition_adapter import acquire as acquire_reference
from learning_evidence_gap_broker import route_gap as route_learning_evidence_gap
from behavioral_eval import evaluate as evaluate_behavior
from trace_to_regression import build_case as build_regression_case

PRIVILEGED_ACTIONS = {
    "GOVERNANCE_WRITE",
    "IMPLEMENTATION_WRITE",
    "IMPLEMENTATION_EXECUTE",
}

UNTRUSTED_SOURCE_CLASSES = {
    "UNTRUSTED_EXTERNAL",
    "PUBLIC_WEB",
    "COMMUNITY",
    "EXTERNAL_REFERENCE",
}

ROUTES = {
    "ORCHESTRATE": "ORCHESTRATOR",
    "ROUTE": "ORCHESTRATOR",
    "SPECIFY_ACCEPTANCE": "ORCHESTRATOR",
    "INSPECT": "VALIDATOR",
    "VALIDATION_ONLY": "VALIDATOR",
    "CROSS_VALIDATE": "VALIDATOR",
    "HANDOFF": "ORCHESTRATOR",
    "REWORK_REQUEST": "ORCHESTRATOR",
    "GOVERNANCE_WRITE": "ORCHESTRATOR",
    "IMPLEMENTATION_WRITE": "IMPLEMENTER",
    "IMPLEMENTATION_EXECUTE": "IMPLEMENTER",
    "HUMAN_APPROVAL": "HUMAN_APPROVER",
    "STATUS_REPORT": "ORCHESTRATOR",
}

def _nonempty(x):
    return isinstance(x, str) and bool(x.strip())

def _safe_repo_path(repo_root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        return None
    root = repo_root.resolve()
    candidate = (repo_root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate

def derive_runtime_state(record: dict) -> tuple[dict, list[str]]:
    failures: list[str] = []
    wm = record.get("working_model")
    if not isinstance(wm, dict):
        return {}, ["WORKING_MODEL_MISSING"]

    required = ["primary_outcome", "priority_order", "execution_implications",
                "rule_to_execution", "next_action", "stop_conditions"]
    for k in required:
        v = wm.get(k)
        if k in {"primary_outcome", "next_action"}:
            if not _nonempty(v):
                failures.append(f"WORKING_MODEL_{k.upper()}_MISSING")
        elif not isinstance(v, list) or not v:
            failures.append(f"WORKING_MODEL_{k.upper()}_MISSING")

    action = str(record.get("action_class", "")).strip().upper()
    owner = str(record.get("execution_owner", "")).strip().upper()
    expected_role = ROUTES.get(action)
    if expected_role is None:
        failures.append("RUNTIME_ROUTE_UNKNOWN")
    elif action not in {"STATUS_REPORT"} and not owner:
        failures.append("EXECUTION_OWNER_MISSING")

    state = {
        "task_id": record.get("task_id"),
        "primary_outcome": wm.get("primary_outcome"),
        "priority_order": wm.get("priority_order", []),
        "protected_state": wm.get("protected_state", []),
        "change_set": record.get("allowed_change_scope", []),
        "preserve_set": record.get(
            "preserve_change_scope",
            wm.get("protected_state", []),
        ),
        "next_action": wm.get("next_action"),
        "stop_conditions": wm.get("stop_conditions", []),
        "action_class": action,
        "route_role": expected_role,
        "execution_owner": owner,
        "material_taky_turn": bool(record.get("material_taky_turn", False)),
        "conversation_system_compile_required": bool(
            record.get("conversation_system_compile_required", False)
        ),
        "architecture_change_planned": bool(record.get("architecture_change_planned", False)),
        "shared_core_change_planned": bool(record.get("shared_core_change_planned", False)),
        "os_boundary_change_planned": bool(record.get("os_boundary_change_planned", False)),
        "cross_domain_architecture_change_planned": bool(
            record.get("cross_domain_architecture_change_planned", False)
        ),
        "ownership_move_planned": bool(record.get("ownership_move_planned", False)),
        "engineering_profile": str(record.get("engineering_profile", "")).strip().upper(),
        "source_trust_class": str(record.get("source_trust_class", "")).strip().upper(),
        "worker_context": record.get("worker_context"),
    }
    return state, failures

def run(record: dict, repo_root: Path, coverage_record: Path | None) -> dict:
    effective_record = dict(record)
    effective_record["material_taky_turn"] = True
    gate = run_c2s_preflight(effective_record, repo_root, coverage_record)
    state, runtime_failures = derive_runtime_state(effective_record)
    detected = list(dict.fromkeys(list(gate.get("detected", [])) + runtime_failures))

    context_firewall_result = None
    worker_context = effective_record.get("worker_context")
    if isinstance(worker_context, dict):
        isolated = worker_context.get("isolated") is True
        allowed_refs = worker_context.get("allowed_context_refs")
        return_fields = worker_context.get("return_fields")
        forbidden_payload_keys = {
            "full_conversation",
            "full_chat_history",
            "entire_history",
            "parent_runtime_state",
            "all_rules",
        }
        present_forbidden = sorted(
            key for key in forbidden_payload_keys
            if key in worker_context and worker_context.get(key) not in (None, "", [], {})
        )
        if not isolated:
            detected.append("CONTEXT_FIREWALL_ISOLATION_REQUIRED")
        if not isinstance(allowed_refs, list) or not allowed_refs or any(
            not isinstance(x, str) or not x.strip() for x in allowed_refs
        ):
            detected.append("CONTEXT_FIREWALL_ALLOWED_REFS_INVALID")
        if not isinstance(return_fields, list) or not return_fields or any(
            not isinstance(x, str) or not x.strip() for x in return_fields
        ):
            detected.append("CONTEXT_FIREWALL_RETURN_CONTRACT_INVALID")
        if present_forbidden:
            detected.append(
                "CONTEXT_FIREWALL_FORBIDDEN_BULK_CONTEXT:"
                + ",".join(present_forbidden)
            )
        context_firewall_result = {
            "required": True,
            "isolated": isolated,
            "allowed_context_refs": allowed_refs if isinstance(allowed_refs, list) else [],
            "return_fields": return_fields if isinstance(return_fields, list) else [],
            "forbidden_bulk_context": present_forbidden,
        }
    else:
        context_firewall_result = {
            "required": False,
            "isolated": None,
            "allowed_context_refs": [],
            "return_fields": [],
            "forbidden_bulk_context": [],
        }

    quarantine_result = None
    source_trust = state.get("source_trust_class")
    action_class = state.get("action_class")
    if source_trust in UNTRUSTED_SOURCE_CLASSES and action_class in PRIVILEGED_ACTIONS:
        clearance = effective_record.get("quarantine_clearance")
        clearance_ok = (
            isinstance(clearance, dict)
            and str(clearance.get("authority", "")).strip().upper() == "VALIDATOR"
            and bool(str(clearance.get("evidence_ref", "")).strip())
            and clearance.get("verified") is True
        )
        quarantine_result = {
            "required": True,
            "cleared": clearance_ok,
            "source_trust_class": source_trust,
            "action_class": action_class,
            "clearance_authority": (
                str(clearance.get("authority", "")).strip().upper()
                if isinstance(clearance, dict)
                else None
            ),
            "evidence_ref": (
                clearance.get("evidence_ref")
                if isinstance(clearance, dict)
                else None
            ),
        }
        if not clearance_ok:
            detected.append("UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE")
    else:
        quarantine_result = {
            "required": False,
            "cleared": True,
            "source_trust_class": source_trust,
            "action_class": action_class,
        }

    synthesis_barrier_result = None
    synthesis_cfg = effective_record.get("synthesis_barrier")
    if isinstance(synthesis_cfg, dict) and synthesis_cfg.get("required") is True:
        expected_children = synthesis_cfg.get("expected_children")
        child_results = synthesis_cfg.get("child_results")
        if not isinstance(expected_children, list) or not expected_children or any(
            not isinstance(x, str) or not x.strip() for x in expected_children
        ):
            detected.append("SYNTHESIS_EXPECTED_CHILDREN_INVALID")
            expected_children = []
        if not isinstance(child_results, list):
            detected.append("SYNTHESIS_CHILD_RESULTS_INVALID")
            child_results = []

        by_id = {}
        malformed = []
        for item in child_results:
            if not isinstance(item, dict):
                malformed.append("NON_OBJECT")
                continue
            child_id = str(item.get("child_id", "")).strip()
            status = str(item.get("status", "")).strip().upper()
            structured = item.get("structured_result")
            if not child_id or status != "COMPLETED" or not isinstance(structured, dict):
                malformed.append(child_id or "MISSING_ID")
                continue
            by_id[child_id] = item

        expected_set = set(expected_children)
        missing = [child_id for child_id in expected_children if child_id not in by_id]
        unexpected = sorted(child_id for child_id in by_id if child_id not in expected_set)
        if malformed:
            detected.append("SYNTHESIS_CHILD_RESULT_MALFORMED:" + ",".join(sorted(set(malformed))))
        if missing:
            detected.append("SYNTHESIS_CHILD_RESULTS_INCOMPLETE:" + ",".join(missing))
        if unexpected:
            detected.append("SYNTHESIS_UNEXPECTED_CHILD_RESULT:" + ",".join(unexpected))

        synthesis_barrier_result = {
            "required": True,
            "expected_children": expected_children,
            "completed_children": sorted(by_id),
            "missing_children": missing,
            "unexpected_children": unexpected,
            "structured_results": [
                by_id[child_id]["structured_result"]
                for child_id in expected_children
                if child_id in by_id
            ],
            "synthesis_ready": not malformed and not missing and not unexpected and bool(expected_children),
        }
    else:
        synthesis_barrier_result = {
            "required": False,
            "expected_children": [],
            "completed_children": [],
            "missing_children": [],
            "unexpected_children": [],
            "structured_results": [],
            "synthesis_ready": True,
        }

    approval_checkpoint_result = None
    approval_cfg = effective_record.get("approval_checkpoint")
    if state.get("action_class") == "HUMAN_APPROVAL":
        if not isinstance(approval_cfg, dict) or approval_cfg.get("required") is not True:
            detected.append("APPROVAL_CHECKPOINT_REQUIRED")
        else:
            namespace = approval_cfg.get("namespace")
            atomic_unit = approval_cfg.get("atomic_unit")
            if not isinstance(namespace, str) or not namespace.strip():
                detected.append("APPROVAL_CHECKPOINT_NAMESPACE_MISSING")
            if not isinstance(atomic_unit, str) or not atomic_unit.strip():
                detected.append("APPROVAL_CHECKPOINT_ATOMIC_UNIT_MISSING")
            if not detected:
                checkpoint_record = {
                    "checkpoint_version": "1.0",
                    "task_id": effective_record.get("task_id"),
                    "namespace": namespace,
                    "atomic_unit": atomic_unit,
                    "status": "BLOCKED",
                    "done": list(approval_cfg.get("done", [])),
                    "open": list(approval_cfg.get("open", [])),
                    "next": approval_cfg.get("resume_next") or state.get("next_action"),
                    "corrections": list(approval_cfg.get("corrections", [])),
                    "source_refs": list(approval_cfg.get("source_refs", [])),
                    "updated_at": approval_cfg.get("updated_at") or datetime.now(timezone.utc).isoformat(),
                    "approval_binding": {
                        "action_class": state.get("action_class"),
                        "execution_owner": state.get("execution_owner"),
                        "primary_outcome": state.get("primary_outcome"),
                        "next_action": state.get("next_action"),
                        "protected_state": state.get("protected_state", []),
                    },
                }
                approval_checkpoint_result = persist_checkpoint(
                    checkpoint_record,
                    repo_root,
                    append_history=True,
                )
                detected.extend(approval_checkpoint_result.get("detected", []))

    approval_resume_result = None
    resume_cfg = effective_record.get("approval_resume")
    if isinstance(resume_cfg, dict) and resume_cfg.get("required") is True:
        if not effective_record.get("human_approval_evidence"):
            detected.append("HUMAN_APPROVAL_EVIDENCE_MISSING_FOR_RESUME")
        namespace = resume_cfg.get("namespace")
        task_id = resume_cfg.get("task_id") or effective_record.get("task_id")
        checkpoint_hash = resume_cfg.get("expected_checkpoint_hash")
        if not isinstance(namespace, str) or not namespace.strip():
            detected.append("APPROVAL_RESUME_NAMESPACE_MISSING")
        if not isinstance(task_id, str) or not task_id.strip():
            detected.append("APPROVAL_RESUME_TASK_ID_MISSING")
        if not isinstance(checkpoint_hash, str) or not checkpoint_hash.strip():
            detected.append("APPROVAL_RESUME_CHECKPOINT_HASH_MISSING")
        if not detected:
            approval_resume_result = guard_checkpoint(
                repo_root,
                namespace=namespace,
                task_id=task_id,
                expected_atomic_unit=resume_cfg.get("expected_atomic_unit"),
                expected_checkpoint_hash=checkpoint_hash,
            )
            detected.extend(approval_resume_result.get("detected", []))

    checkpoint_guard_result = None
    checkpoint_cfg = effective_record.get("checkpoint_guard")
    if isinstance(checkpoint_cfg, dict) and checkpoint_cfg.get("required") is True:
        namespace = checkpoint_cfg.get("namespace")
        task_id = checkpoint_cfg.get("task_id")
        if not isinstance(namespace, str) or not namespace.strip():
            detected.append("CHECKPOINT_NAMESPACE_MISSING")
        if not isinstance(task_id, str) or not task_id.strip():
            detected.append("CHECKPOINT_TASK_ID_MISSING")
        if not detected:
            checkpoint_guard_result = guard_checkpoint(
                repo_root,
                namespace=namespace,
                task_id=task_id,
                expected_atomic_unit=checkpoint_cfg.get("expected_atomic_unit"),
                expected_checkpoint_hash=checkpoint_cfg.get("expected_checkpoint_hash"),
            )
            detected.extend(checkpoint_guard_result.get("detected", []))

    reference_intake_result = None
    reference_acquisition_result = None
    reference_intake_execution = None
    intent_text = str(effective_record.get("intent_text", "") or "")
    has_reference_source = any(
        effective_record.get(k)
        for k in ("has_reference_source", "source_url", "source_id", "source_locator")
    )
    if has_reference_source and any(term in intent_text.lower() for term in ("검토", "참고", "자료로", "분석")):
        reference_intake_result = route_reference_intake(effective_record)
        if not reference_intake_result.get("pass"):
            detected.extend(reference_intake_result.get("detected", []))
        elif (
            reference_intake_result.get("route_type") == "REFERENCE_INTAKE_REVIEW"
            and effective_record.get("reference_acquisition_execute") is True
            and not isinstance(effective_record.get("reference_intake_execution"), dict)
        ):
            destination = _safe_repo_path(
                repo_root,
                effective_record.get("reference_acquisition_destination") or "DATA/INBOX/ACQUIRED",
            )
            if destination is None:
                detected.append("REFERENCE_ACQUISITION_DESTINATION_INVALID")
            elif not effective_record.get("source_url"):
                detected.append("REFERENCE_ACQUISITION_SOURCE_URL_REQUIRED")
            elif not detected:
                reference_acquisition_result = acquire_reference(
                    str(effective_record.get("source_url")),
                    destination_dir=destination,
                    max_bytes=int(effective_record.get("reference_acquisition_max_bytes") or 25 * 1024 * 1024),
                    timeout_seconds=int(effective_record.get("reference_acquisition_timeout_seconds") or 20),
                )
                if not reference_acquisition_result.get("pass"):
                    detected.extend(reference_acquisition_result.get("detected", []))
                else:
                    effective_record["reference_intake_execution"] = {
                        "acquisition_state": reference_acquisition_result.get("acquisition_state"),
                        "reason": reference_acquisition_result.get("reason"),
                        "preserved_path": reference_acquisition_result.get("preserved_path"),
                        "sha256": reference_acquisition_result.get("sha256"),
                        "content_type": reference_acquisition_result.get("content_type"),
                        "content_length": reference_acquisition_result.get("content_length"),
                        "final_url": reference_acquisition_result.get("final_url"),
                    }
        if (
            reference_intake_result.get("pass")
            and isinstance(effective_record.get("reference_intake_execution"), dict)
            and not detected
        ):
            reference_intake_execution = execute_reference_intake(
                effective_record,
                reference_intake_result,
                repo_root,
            )
            if not reference_intake_execution.get("pass"):
                detected.extend(reference_intake_execution.get("detected", []))

    learning_gap_result = None
    gap = effective_record.get("learning_evidence_gap")
    if isinstance(gap, dict):
        gap_index_path = _safe_repo_path(repo_root, effective_record.get("learning_evidence_index_path"))
        if gap_index_path is None:
            detected.append("LEARNING_EVIDENCE_INDEX_PATH_INVALID")
        elif not gap_index_path.exists():
            detected.append("LEARNING_EVIDENCE_INDEX_PATH_MISSING")
        elif not detected:
            learning_gap_result = route_learning_evidence_gap(
                gap,
                index_path=gap_index_path,
                min_results=int(effective_record.get("learning_evidence_min_results") or 1),
                consumer="LEARNING_ENGINE",
            )
            if not learning_gap_result.get("pass"):
                detected.extend(learning_gap_result.get("detected", []))

    behavioral_eval_result = None
    behavioral_cfg = effective_record.get("behavioral_eval")
    if isinstance(behavioral_cfg, dict) and behavioral_cfg.get("required") is True:
        observations = behavioral_cfg.get("observed")
        assertions = behavioral_cfg.get("assertions")
        if not isinstance(observations, dict):
            detected.append("BEHAVIORAL_EVAL_OBSERVED_INVALID")
        elif not isinstance(assertions, list) or not assertions:
            detected.append("BEHAVIORAL_EVAL_ASSERTIONS_INVALID")
        elif not detected:
            behavioral_eval_result = evaluate_behavior(observations, assertions)
            detected.extend(behavioral_eval_result.get("detected", []))

    regression_capture_result = None
    regression_event = effective_record.get("regression_capture")
    if isinstance(regression_event, dict):
        regression_capture_result = build_regression_case(regression_event)
        detected.extend(regression_capture_result.get("detected", []))

    task_contract_result = None
    if not detected and state.get("action_class") == "SPECIFY_ACCEPTANCE" and state.get("execution_owner") == "CODEX":
        task_contract_result = build_codex_task_contract(record)
        detected.extend(task_contract_result.get("detected", []))

    dispatch_result = None
    adapter_result = None
    if not detected and isinstance(task_contract_result, dict) and task_contract_result.get("task_contract"):
        task_contract = task_contract_result["task_contract"]
        transport = record.get("executor_transport", "FILE_QUEUE")
        if (task_contract.get("executor_automation") or {}).get("target_repository_local") is True:
            registry_path = repo_root / "MASTER" / "EXECUTOR_ADAPTER_REGISTRY.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            adapter_result = resolve_executor_adapter(task_contract, transport, registry)
            detected.extend(adapter_result.get("detected", []))
        if not detected:
            dispatch_result = build_executor_envelope(
                task_contract,
                transport=transport,
                provider=record.get("executor_provider", "CODEX"),
            )
            detected.extend(dispatch_result.get("detected", []))

    detected = list(dict.fromkeys(detected))
    authorized = not detected
    return {
        "pass": authorized,
        "authorized_to_continue": authorized,
        "detected": detected,
        "runtime_state": state,
        "route": None if not authorized else {
            "role": state.get("route_role"),
            "execution_owner": state.get("execution_owner"),
            "action_class": state.get("action_class"),
            "next_action": state.get("next_action"),
        },
        "task_contract": (
            task_contract_result.get("task_contract")
            if authorized and isinstance(task_contract_result, dict)
            else None
        ),
        "dispatch_envelope": (
            dispatch_result.get("dispatch_envelope")
            if authorized and isinstance(dispatch_result, dict)
            else None
        ),
        "executor_adapter": (
            adapter_result.get("adapter")
            if authorized and isinstance(adapter_result, dict)
            else None
        ),
        "checkpoint_guard": checkpoint_guard_result,
        "approval_checkpoint": approval_checkpoint_result,
        "approval_resume_guard": approval_resume_result,
        "context_firewall": context_firewall_result,
        "source_quarantine": quarantine_result,
        "synthesis_barrier": synthesis_barrier_result,
        "reference_intake_route": reference_intake_result,
        "reference_acquisition_result": reference_acquisition_result,
        "reference_intake_execution": reference_intake_execution,
        "learning_evidence_gap_route": learning_gap_result,
        "behavioral_eval": behavioral_eval_result,
        "regression_capture": regression_capture_result,
        "claim_ceiling": "CONTROLLED_REPOSITORY_RUNTIME",
        "reference_intake_fetch_verified": bool(
            reference_acquisition_result and reference_acquisition_result.get("pass")
        ),
        "reference_intake_persistence_verified": bool(
            reference_intake_execution and reference_intake_execution.get("pass")
        ),
        "learning_gap_index_check_verified": bool(
            learning_gap_result and learning_gap_result.get("index_checked")
        ),
        "learning_direct_mining_verified": False,
        "hosted_chatgpt_auto_invocation_verified": False,
        "external_executor_invocation_verified": False,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--coverage-record", type=Path)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = run(record, args.repo_root, args.coverage_record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
