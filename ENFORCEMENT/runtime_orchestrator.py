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
import math
from datetime import datetime, timezone
from pathlib import Path
from fnmatch import fnmatchcase

from c2s_preflight_bridge import run as run_c2s_preflight
from codex_task_contract_builder import build as build_codex_task_contract
from executor_transport import build_envelope as build_executor_envelope
from executor_adapter_registry import resolve as resolve_executor_adapter
from execution_checkpoint import (
    consume_approval,
    guard as guard_checkpoint,
    persist as persist_checkpoint,
)
from side_effect_ledger import guard as guard_side_effect, release_claim as release_side_effect_claim
from result_preview_gate import validate_preview, validate_release
from reference_intake_router import route as route_reference_intake
from reference_intake_executor import execute as execute_reference_intake
from reference_acquisition_adapter import acquire as acquire_reference
from learning_evidence_gap_broker import route_gap as route_learning_evidence_gap
from behavioral_eval import evaluate as evaluate_behavior
from trace_to_regression import build_case as build_regression_case
from producer_artifact_gate import preflight as producer_artifact_preflight, postflight as producer_artifact_postflight
from ai_open_quest_router import route as route_ai_open_quests

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
    "SOURCE_EXTERNAL_UNTRUSTED",
    "SOURCE_EXTERNAL_UNTRUSTED_RUNTIME_CONTENT",
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


def _target_ref_within_change_scope(target_ref: str, scopes: list[str]) -> bool:
    target = target_ref.replace("\\", "/").strip()
    for raw_scope in scopes:
        if not isinstance(raw_scope, str) or not raw_scope.strip():
            continue
        scope = raw_scope.replace("\\", "/").strip()
        if fnmatchcase(target, scope):
            return True
        base = scope.rstrip("/")
        if "*" not in scope and "?" not in scope and "[" not in scope:
            if target == base or target.startswith(base + "/"):
                return True
    return False


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    import hashlib
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        return None
    return [item.strip() for item in value]


def _rule_ref_ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            refs.append(item.strip())
            continue
        if isinstance(item, dict):
            candidate = (
                item.get("rule_ref")
                or item.get("source_id")
                or item.get("path")
            )
            if isinstance(candidate, str) and candidate.strip():
                refs.append(candidate.strip())
    return refs


def _delegation_parent_snapshot(record: dict) -> dict:
    return {
        "task_id": str(record.get("task_id", "")).strip(),
        "rule_refs": _rule_ref_ids(record.get("applicable_rule_refs")),
        "change_scope": list(record.get("allowed_change_scope") or []),
        "forbidden_actions": list(record.get("forbidden_actions") or []),
        "approval_scope": list(record.get("approval_scope") or []),
        "connection_scope": list(record.get("connection_scope") or []),
        "cost_ceiling": record.get("cost_ceiling"),
    }


def _runtime_authority_snapshot(
    record: dict,
    state: dict,
    delegation: dict | None = None,
) -> dict:
    delegation = delegation if isinstance(delegation, dict) else {}
    return {
        "task_id": state.get("task_id"),
        "action_class": state.get("action_class"),
        "execution_owner": state.get("execution_owner"),
        "primary_outcome": state.get("primary_outcome"),
        "next_action": state.get("next_action"),
        "protected_state": list(state.get("protected_state") or []),
        "allowed_change_scope": list(record.get("allowed_change_scope") or []),
        "forbidden_actions": list(record.get("forbidden_actions") or []),
        "approval_scope": list(record.get("approval_scope") or []),
        "connection_scope": list(record.get("connection_scope") or []),
        "cost_ceiling": record.get("cost_ceiling"),
        "delegation_child_id": delegation.get("child_id"),
        "delegation_contract_hash": delegation.get("contract_hash"),
    }


def validate_delegation_contract(record: dict, worker_context: dict) -> tuple[dict, list[str]]:
    failures: list[str] = []
    contract = record.get("delegation_contract")
    if not isinstance(contract, dict):
        return {
            "required": True,
            "valid": False,
            "child_id": None,
            "parent_contract_hash": None,
        }, ["DELEGATION_CONTRACT_REQUIRED"]

    parent = _delegation_parent_snapshot(record)
    expected_parent_hash = _canonical_hash(parent)
    parent_task_id = str(contract.get("parent_task_id", "")).strip()
    child_id = str(contract.get("child_id", "")).strip()

    if not parent_task_id or parent_task_id != parent["task_id"]:
        failures.append("DELEGATION_PARENT_TASK_ID_MISMATCH")
    if not child_id:
        failures.append("DELEGATION_CHILD_ID_MISSING")
    if contract.get("parent_contract_hash") != expected_parent_hash:
        failures.append("DELEGATION_PARENT_CONTRACT_HASH_MISMATCH")

    pairs = (
        ("inherited_rule_refs", "rule_refs", "DELEGATION_RULE_SCOPE_WIDENED"),
        ("inherited_change_scope", "change_scope", "DELEGATION_CHANGE_SCOPE_WIDENED"),
        ("inherited_approval_scope", "approval_scope", "DELEGATION_APPROVAL_SCOPE_WIDENED"),
        ("inherited_connection_scope", "connection_scope", "DELEGATION_CONNECTION_SCOPE_WIDENED"),
    )
    normalized: dict[str, list[str]] = {}
    for child_key, parent_key, code in pairs:
        child_values = _string_list(contract.get(child_key))
        parent_values = _string_list(parent.get(parent_key))
        if child_values is None:
            failures.append(f"DELEGATION_{child_key.upper()}_INVALID")
            child_values = []
        if parent_values is None:
            parent_values = []
        if not set(child_values).issubset(set(parent_values)):
            failures.append(code)
        normalized[child_key] = child_values

    inherited_forbidden = _string_list(contract.get("inherited_forbidden_actions"))
    parent_forbidden = _string_list(parent.get("forbidden_actions")) or []
    if inherited_forbidden is None:
        failures.append("DELEGATION_INHERITED_FORBIDDEN_ACTIONS_INVALID")
        inherited_forbidden = []
    if not set(parent_forbidden).issubset(set(inherited_forbidden)):
        failures.append("DELEGATION_FORBIDDEN_ACTION_DROPPED")

    child_ceiling = contract.get("inherited_cost_ceiling")
    parent_ceiling = parent.get("cost_ceiling")
    parent_is_number = (
        isinstance(parent_ceiling, (int, float))
        and not isinstance(parent_ceiling, bool)
        and math.isfinite(parent_ceiling)
    )
    child_is_number = (
        isinstance(child_ceiling, (int, float))
        and not isinstance(child_ceiling, bool)
        and math.isfinite(child_ceiling)
    )
    if parent_ceiling is not None and not parent_is_number:
        failures.append("DELEGATION_PARENT_COST_CEILING_INVALID")
    if parent_is_number:
        if not child_is_number:
            failures.append("DELEGATION_COST_CEILING_REQUIRED")
        elif child_ceiling > parent_ceiling:
            failures.append("DELEGATION_COST_SCOPE_WIDENED")
    elif child_ceiling is not None:
        failures.append(
            "DELEGATION_COST_CEILING_INVALID"
            if not child_is_number
            else "DELEGATION_COST_SCOPE_WIDENED"
        )

    return_contract = _string_list(contract.get("return_contract"))
    worker_return = _string_list(worker_context.get("return_fields"))
    if return_contract is None:
        failures.append("DELEGATION_RETURN_CONTRACT_INVALID")
        return_contract = []
    if worker_return is None or set(return_contract) != set(worker_return):
        failures.append("DELEGATION_RETURN_CONTRACT_MISMATCH")

    result = {
        "required": True,
        "valid": not failures,
        "parent_task_id": parent["task_id"],
        "parent_contract_hash": expected_parent_hash,
        "child_id": child_id or None,
        "inherited_rule_refs": normalized.get("inherited_rule_refs", []),
        "inherited_change_scope": normalized.get("inherited_change_scope", []),
        "inherited_forbidden_actions": inherited_forbidden,
        "inherited_approval_scope": normalized.get("inherited_approval_scope", []),
        "inherited_connection_scope": normalized.get("inherited_connection_scope", []),
        "inherited_cost_ceiling": child_ceiling,
        "return_contract": return_contract,
        "contract_hash": _canonical_hash(contract),
    }
    return result, failures


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
    try:
        ai_quest_advisory = route_ai_open_quests(effective_record)
    except Exception as exc:
        # Advisory only: quest discovery must never become an execution blocker.
        ai_quest_advisory = {
            "schema": "TAKY_AI_OPEN_QUEST_ROUTE_V1",
            "advisory": True,
            "selected_count": 0,
            "selected": [],
            "router_error": type(exc).__name__,
        }
    gate = run_c2s_preflight(effective_record, repo_root, coverage_record)
    state, runtime_failures = derive_runtime_state(effective_record)
    detected = list(dict.fromkeys(list(gate.get("detected", [])) + runtime_failures))

    # Explicit artifact-producing route: PRE before producer dispatch, POST for a
    # supplied actual output/evidence. This does NOT intercept hosted ChatGPT.
    artifact_gate_result = None
    artifact_contract = effective_record.get("artifact_contract")
    if effective_record.get("artifact_production") is True or artifact_contract is not None:
        if not isinstance(artifact_contract, dict):
            detected.append("ARTIFACT_PRE_CONTRACT_MISSING")
        elif artifact_contract.get("task_id") != effective_record.get("task_id"):
            detected.append("ARTIFACT_CONTRACT_CURRENT_TASK_MISMATCH")
        else:
            phase = effective_record.get("artifact_phase", "PRE")
            if phase == "PRE":
                artifact_gate_result = producer_artifact_preflight(artifact_contract, repo_root)
                detected.extend(artifact_gate_result.get("detected", []))
            elif phase == "POST":
                evidence = effective_record.get("artifact_evidence")
                receipt = effective_record.get("artifact_pre_receipt")
                if not isinstance(evidence, dict) or not isinstance(receipt, dict):
                    detected.append("ARTIFACT_POST_EVIDENCE_OR_RECEIPT_MISSING")
                else:
                    artifact_gate_result = producer_artifact_postflight(
                        artifact_contract, receipt, evidence, repo_root
                    )
                    detected.extend(artifact_gate_result.get("detected", []))
            else:
                detected.append("ARTIFACT_PHASE_INVALID")

    context_firewall_result = None
    worker_context_present = "worker_context" in effective_record
    worker_context = effective_record.get("worker_context")
    if worker_context_present and not isinstance(worker_context, dict):
        detected.append("CONTEXT_FIREWALL_WORKER_CONTEXT_INVALID")
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

    delegation_inheritance_result = {
        "required": False,
        "valid": True,
        "child_id": None,
        "parent_contract_hash": None,
    }
    if isinstance(worker_context, dict):
        delegation_inheritance_result, delegation_failures = validate_delegation_contract(
            effective_record,
            worker_context,
        )
        detected.extend(delegation_failures)
        if delegation_inheritance_result.get("valid") is True:
            effective_record["applicable_rule_refs"] = list(
                delegation_inheritance_result.get("inherited_rule_refs", [])
            )
            effective_record["allowed_change_scope"] = list(
                delegation_inheritance_result.get("inherited_change_scope", [])
            )
            effective_record["forbidden_actions"] = list(
                delegation_inheritance_result.get("inherited_forbidden_actions", [])
            )
            effective_record["approval_scope"] = list(
                delegation_inheritance_result.get("inherited_approval_scope", [])
            )
            effective_record["connection_scope"] = list(
                delegation_inheritance_result.get("inherited_connection_scope", [])
            )
            effective_record["cost_ceiling"] = delegation_inheritance_result.get(
                "inherited_cost_ceiling"
            )
            state["change_set"] = list(
                delegation_inheritance_result.get("inherited_change_scope", [])
            )
    elif worker_context_present or effective_record.get("delegation_contract") is not None:
        delegation_inheritance_result = {
            "required": True,
            "valid": False,
            "child_id": None,
            "parent_contract_hash": None,
        }
        detected.append("DELEGATION_WORKER_CONTEXT_INVALID")

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

    runtime_authority = _runtime_authority_snapshot(
        effective_record,
        state,
        delegation_inheritance_result,
    )
    runtime_authority_hash = _canonical_hash(runtime_authority)

    approval_checkpoint_result = None
    pending_approval_checkpoint_record = None
    approval_cfg = effective_record.get("approval_checkpoint")
    if state.get("action_class") == "HUMAN_APPROVAL":
        if not isinstance(approval_cfg, dict) or approval_cfg.get("required") is not True:
            detected.append("APPROVAL_CHECKPOINT_REQUIRED")
        else:
            namespace = approval_cfg.get("namespace")
            atomic_unit = approval_cfg.get("atomic_unit")
            action_kind = approval_cfg.get("action_kind") or "HUMAN_APPROVAL_ACTION"
            action_payload = approval_cfg.get("action_payload")
            if not isinstance(namespace, str) or not namespace.strip():
                detected.append("APPROVAL_CHECKPOINT_NAMESPACE_MISSING")
            if not isinstance(atomic_unit, str) or not atomic_unit.strip():
                detected.append("APPROVAL_CHECKPOINT_ATOMIC_UNIT_MISSING")
            if not isinstance(action_kind, str) or not action_kind.strip():
                detected.append("APPROVAL_CHECKPOINT_ACTION_KIND_MISSING")
            if not isinstance(action_payload, dict) or not action_payload:
                detected.append("APPROVAL_CHECKPOINT_ACTION_PAYLOAD_MISSING")
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
                        **runtime_authority,
                        "runtime_authority_hash": runtime_authority_hash,
                        "action_kind": action_kind.strip(),
                        "action_payload_hash": _canonical_hash(action_payload),
                    },
                }
                pending_approval_checkpoint_record = checkpoint_record

    approval_resume_result = None
    approval_consumption_result = None
    approval_evidence = effective_record.get("human_approval_evidence")
    resume_cfg = effective_record.get("approval_resume")
    if isinstance(resume_cfg, dict) and resume_cfg.get("required") is True:
        if not approval_evidence:
            detected.append("HUMAN_APPROVAL_EVIDENCE_MISSING_FOR_RESUME")
        namespace = resume_cfg.get("namespace")
        task_id = resume_cfg.get("task_id") or effective_record.get("task_id")
        checkpoint_hash = resume_cfg.get("expected_checkpoint_hash")
        atomic_unit = resume_cfg.get("expected_atomic_unit")
        resume_action_kind = resume_cfg.get("action_kind")
        resume_action_payload = resume_cfg.get("action_payload")
        current_task_id = effective_record.get("task_id")
        if not isinstance(namespace, str) or not namespace.strip():
            detected.append("APPROVAL_RESUME_NAMESPACE_MISSING")
        if not isinstance(task_id, str) or not task_id.strip():
            detected.append("APPROVAL_RESUME_TASK_ID_MISSING")
        elif task_id != current_task_id:
            detected.append("APPROVAL_RESUME_CURRENT_TASK_MISMATCH")
        if not isinstance(checkpoint_hash, str) or not checkpoint_hash.strip():
            detected.append("APPROVAL_RESUME_CHECKPOINT_HASH_MISSING")
        if not isinstance(atomic_unit, str) or not atomic_unit.strip():
            detected.append("APPROVAL_RESUME_ATOMIC_UNIT_MISSING")
        if not isinstance(resume_action_kind, str) or not resume_action_kind.strip():
            detected.append("APPROVAL_RESUME_ACTION_KIND_MISSING")
        if not isinstance(resume_action_payload, dict) or not resume_action_payload:
            detected.append("APPROVAL_RESUME_ACTION_PAYLOAD_MISSING")
        if not detected:
            approval_resume_result = guard_checkpoint(
                repo_root,
                namespace=namespace,
                task_id=task_id,
                expected_atomic_unit=atomic_unit,
                expected_checkpoint_hash=checkpoint_hash,
            )
            detected.extend(approval_resume_result.get("detected", []))
            if approval_resume_result.get("pass") is True:
                stored_binding = (
                    (approval_resume_result.get("checkpoint") or {}).get("approval_binding")
                    or {}
                )
                for key, current_value in runtime_authority.items():
                    if stored_binding.get(key) != current_value:
                        detected.append(
                            f"APPROVAL_RESUME_CURRENT_ROUTE_MISMATCH:{key}"
                        )
                stored_authority_hash = stored_binding.get("runtime_authority_hash")
                if not isinstance(stored_authority_hash, str) or not stored_authority_hash.strip():
                    detected.append("APPROVAL_RESUME_RUNTIME_AUTHORITY_FINGERPRINT_MISSING")
                elif stored_authority_hash != runtime_authority_hash:
                    detected.append("APPROVAL_RESUME_RUNTIME_AUTHORITY_FINGERPRINT_MISMATCH")
                if stored_binding.get("action_kind") != resume_action_kind.strip():
                    detected.append("APPROVAL_RESUME_CURRENT_ACTION_MISMATCH:action_kind")
                current_action_payload_hash = _canonical_hash(resume_action_payload)
                if stored_binding.get("action_payload_hash") != current_action_payload_hash:
                    detected.append(
                        "APPROVAL_RESUME_CURRENT_ACTION_MISMATCH:action_payload_hash"
                    )

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

    side_effect_guard_result = None
    side_effect_cfg = effective_record.get("side_effect_guard")
    if isinstance(side_effect_cfg, dict) and side_effect_cfg.get("required") is True:
        namespace = side_effect_cfg.get("namespace")
        task_id = side_effect_cfg.get("task_id") or effective_record.get("task_id")
        if task_id != effective_record.get("task_id"):
            detected.append("SIDE_EFFECT_GUARD_CURRENT_TASK_MISMATCH")
        effect_id = side_effect_cfg.get("effect_id")
        idempotency_key = side_effect_cfg.get("idempotency_key")
        action_payload_hash = side_effect_cfg.get("action_payload_hash")
        side_effect_action_kind = side_effect_cfg.get("action_kind")
        side_effect_target_ref = side_effect_cfg.get("target_ref")
        if isinstance(resume_cfg, dict) and resume_cfg.get("required") is True:
            approved_payload = resume_cfg.get("action_payload")
            approved_identity = {
                "action_kind": resume_cfg.get("action_kind"),
                "action_payload_hash": _canonical_hash(approved_payload),
                "target_ref": approved_payload.get("target_ref")
                if isinstance(approved_payload, dict) else None,
            }
            for key, approved_value in approved_identity.items():
                if not approved_value or side_effect_cfg.get(key) != approved_value:
                    detected.append(f"APPROVAL_SIDE_EFFECT_IDENTITY_MISMATCH:{key}")
        if isinstance(delegation_inheritance_result, dict) and delegation_inheritance_result.get("child_id"):
            delegated_forbidden = effective_record.get("forbidden_actions")
            if (
                isinstance(delegated_forbidden, list)
                and isinstance(side_effect_action_kind, str)
                and any(
                    isinstance(item, str)
                    and item.casefold() == side_effect_action_kind.casefold()
                    for item in delegated_forbidden
                )
            ):
                detected.append("SIDE_EFFECT_ACTION_FORBIDDEN_BY_DELEGATED_AUTHORITY")

            delegated_scope = effective_record.get("allowed_change_scope")
            if (
                isinstance(delegated_scope, list)
                and delegated_scope
                and isinstance(side_effect_target_ref, str)
                and side_effect_target_ref.strip()
                and not _target_ref_within_change_scope(
                    side_effect_target_ref,
                    delegated_scope,
                )
            ):
                detected.append("SIDE_EFFECT_TARGET_OUTSIDE_DELEGATED_CHANGE_SCOPE")

        required_text = (
            ("namespace", namespace),
            ("task_id", task_id),
            ("effect_id", effect_id),
            ("idempotency_key", idempotency_key),
            ("action_payload_hash", action_payload_hash),
            ("action_kind", side_effect_action_kind),
            ("target_ref", side_effect_target_ref),
        )
        for key, value in required_text:
            if not isinstance(value, str) or not value.strip():
                detected.append(f"SIDE_EFFECT_GUARD_{key.upper()}_MISSING")
        if not detected:
            side_effect_guard_result = guard_side_effect(
                repo_root,
                namespace=namespace,
                task_id=task_id,
                effect_id=effect_id,
                idempotency_key=idempotency_key,
                action_payload_hash=action_payload_hash,
                action_kind=side_effect_action_kind,
                target_ref=side_effect_target_ref,
                reserve=False,
            )
            detected.extend(side_effect_guard_result.get("detected", []))

    result_preview_guard_result = None
    preview_cfg = effective_record.get("result_preview_guard")
    release_intent = effective_record.get("release_intent") is True
    if release_intent and not (
        isinstance(preview_cfg, dict) and preview_cfg.get("required") is True
    ):
        detected.append("RESULT_PREVIEW_GUARD_REQUIRED_FOR_RELEASE")
    elif isinstance(preview_cfg, dict) and preview_cfg.get("required") is True:
        preview_record = preview_cfg.get("preview_record")
        release_request = preview_cfg.get("release_request")
        preview_local_errors: list[str] = []
        if not isinstance(preview_record, dict):
            preview_local_errors.append("RESULT_PREVIEW_RECORD_MISSING")
        if not isinstance(release_request, dict):
            preview_local_errors.append("RESULT_RELEASE_REQUEST_MISSING")
        if preview_local_errors:
            detected.extend(preview_local_errors)
            result_preview_guard_result = {
                "pass": False,
                "detected": preview_local_errors,
            }
        else:
            preview_result = validate_preview(preview_record, repo_root)
            release_result = (
                validate_release(preview_result, release_request, repo_root)
                if preview_result.get("pass") is True
                else {
                    "pass": False,
                    "detected": ["RESULT_RELEASE_PREVIEW_NOT_PASS"],
                    "release_binding_hash": None,
                    "release_binding": None,
                }
            )
            preview_detected = list(preview_result.get("detected", []))
            preview_detected.extend(release_result.get("detected", []))
            if preview_result.get("task_id") != effective_record.get("task_id"):
                preview_detected.append("RESULT_PREVIEW_CURRENT_TASK_MISMATCH")

            if release_result.get("pass") is True:
                if isinstance(resume_cfg, dict) and resume_cfg.get("required") is True:
                    if _canonical_hash(resume_cfg.get("action_payload")) != _canonical_hash(release_request):
                        preview_detected.append("RESULT_RELEASE_APPROVAL_PAYLOAD_MISMATCH")
                if isinstance(approval_cfg, dict) and approval_cfg.get("required") is True:
                    if _canonical_hash(approval_cfg.get("action_payload")) != _canonical_hash(release_request):
                        preview_detected.append("RESULT_RELEASE_CHECKPOINT_PAYLOAD_MISMATCH")
                if isinstance(side_effect_cfg, dict) and side_effect_cfg.get("required") is True:
                    if side_effect_cfg.get("action_payload_hash") != release_request.get("release_payload_hash"):
                        preview_detected.append("RESULT_RELEASE_SIDE_EFFECT_PAYLOAD_MISMATCH")
                    if side_effect_cfg.get("target_ref") != release_request.get("release_target"):
                        preview_detected.append("RESULT_RELEASE_SIDE_EFFECT_TARGET_MISMATCH")

            detected.extend(preview_detected)
            result_preview_guard_result = {
                "pass": not preview_detected,
                "detected": list(dict.fromkeys(preview_detected)),
                "preview": preview_result,
                "release": release_result,
            }

    reference_intake_result = None
    reference_acquisition_result = None
    reference_intake_execution = None
    reference_acquisition_plan = None
    reference_execution_pending = False
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
            else:
                reference_acquisition_plan = {
                    "source_url": str(effective_record.get("source_url")),
                    "destination": destination,
                    "max_bytes": int(
                        effective_record.get("reference_acquisition_max_bytes")
                        or 25 * 1024 * 1024
                    ),
                    "timeout_seconds": int(
                        effective_record.get("reference_acquisition_timeout_seconds")
                        or 20
                    ),
                }
        if (
            reference_intake_result.get("pass")
            and isinstance(effective_record.get("reference_intake_execution"), dict)
        ):
            reference_execution_pending = True

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
        task_contract_result = build_codex_task_contract(effective_record)
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

    side_effect_mutation_requested = (
        isinstance(side_effect_cfg, dict) and side_effect_cfg.get("required") is True
    )
    approval_resume_mutation_requested = (
        isinstance(resume_cfg, dict) and resume_cfg.get("required") is True
    )
    reference_mutation_requested = (
        reference_acquisition_plan is not None or reference_execution_pending
    )
    if pending_approval_checkpoint_record is not None and (
        side_effect_mutation_requested or approval_resume_mutation_requested
    ):
        detected.append("APPROVAL_CHECKPOINT_COMBINED_AUTHORIZATION_MUTATION_NOT_ALLOWED")
    if reference_mutation_requested and (
        pending_approval_checkpoint_record is not None
        or side_effect_mutation_requested
        or approval_resume_mutation_requested
    ):
        detected.append("AUTHORIZATION_MUTATION_EFFECTFUL_REFERENCE_NOT_ALLOWED")

    if not detected and pending_approval_checkpoint_record is not None:
        approval_checkpoint_result = persist_checkpoint(
            pending_approval_checkpoint_record,
            repo_root,
            append_history=True,
        )
        detected.extend(approval_checkpoint_result.get("detected", []))

    side_effect_claim_path = None
    if (
        not detected
        and isinstance(side_effect_cfg, dict)
        and side_effect_cfg.get("required") is True
    ):
        final_side_effect_guard = guard_side_effect(
            repo_root,
            namespace=side_effect_cfg.get("namespace"),
            task_id=side_effect_cfg.get("task_id") or effective_record.get("task_id"),
            effect_id=side_effect_cfg.get("effect_id"),
            idempotency_key=side_effect_cfg.get("idempotency_key"),
            action_payload_hash=side_effect_cfg.get("action_payload_hash"),
            action_kind=side_effect_cfg.get("action_kind"),
            target_ref=side_effect_cfg.get("target_ref"),
            reserve=True,
        )
        side_effect_guard_result = final_side_effect_guard
        detected.extend(final_side_effect_guard.get("detected", []))
        if final_side_effect_guard.get("pass") is True:
            side_effect_claim_path = final_side_effect_guard.get("claim_path")

    if (
        not detected
        and isinstance(resume_cfg, dict)
        and resume_cfg.get("required") is True
        and isinstance(approval_resume_result, dict)
        and approval_resume_result.get("pass") is True
    ):
        approval_consumption_result = consume_approval(
            repo_root,
            namespace=resume_cfg.get("namespace"),
            task_id=resume_cfg.get("task_id") or effective_record.get("task_id"),
            expected_atomic_unit=resume_cfg.get("expected_atomic_unit"),
            expected_checkpoint_hash=resume_cfg.get("expected_checkpoint_hash"),
            expected_action_kind=resume_cfg.get("action_kind"),
            expected_action_payload_hash=_canonical_hash(resume_cfg.get("action_payload")),
            evidence=approval_evidence,
        )
        detected.extend(approval_consumption_result.get("detected", []))
        if not approval_consumption_result.get("pass") and side_effect_claim_path:
            rollback = release_side_effect_claim(repo_root, side_effect_claim_path)
            if not rollback.get("pass"):
                detected.extend(rollback.get("detected", []))
            else:
                side_effect_claim_path = None

    if not detected and reference_acquisition_plan is not None:
        reference_acquisition_result = acquire_reference(
            reference_acquisition_plan["source_url"],
            destination_dir=reference_acquisition_plan["destination"],
            max_bytes=reference_acquisition_plan["max_bytes"],
            timeout_seconds=reference_acquisition_plan["timeout_seconds"],
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
            reference_execution_pending = True

    if (
        not detected
        and reference_execution_pending
        and isinstance(reference_intake_result, dict)
        and reference_intake_result.get("pass")
        and isinstance(effective_record.get("reference_intake_execution"), dict)
    ):
        reference_intake_execution = execute_reference_intake(
            effective_record,
            reference_intake_result,
            repo_root,
        )
        if not reference_intake_execution.get("pass"):
            detected.extend(reference_intake_execution.get("detected", []))

    detected = list(dict.fromkeys(detected))
    authorized = not detected
    authorized_action = None
    if authorized:
        if approval_resume_mutation_requested:
            approved_payload = resume_cfg.get("action_payload")
            authorized_action = {
                "source": "APPROVAL_RESUME",
                "action_kind": resume_cfg.get("action_kind"),
                "action_payload": approved_payload,
                "action_payload_hash": _canonical_hash(approved_payload),
            }
        elif side_effect_mutation_requested:
            authorized_action = {
                "source": "SIDE_EFFECT_GUARD",
                "action_kind": side_effect_cfg.get("action_kind"),
                "action_payload_hash": side_effect_cfg.get("action_payload_hash"),
                "target_ref": side_effect_cfg.get("target_ref"),
            }
        elif (
            isinstance(result_preview_guard_result, dict)
            and result_preview_guard_result.get("pass") is True
            and isinstance(preview_cfg, dict)
            and isinstance(preview_cfg.get("release_request"), dict)
        ):
            release_request = preview_cfg.get("release_request")
            authorized_action = {
                "source": "RESULT_RELEASE",
                "action_kind": "RELEASE",
                "action_payload": release_request,
                "action_payload_hash": _canonical_hash(release_request),
            }
        else:
            route_payload = {
                "next_action": state.get("next_action"),
                "runtime_authority_hash": runtime_authority_hash,
            }
            authorized_action = {
                "source": "RUNTIME_ROUTE",
                "action_kind": state.get("action_class"),
                "action_payload": route_payload,
                "action_payload_hash": _canonical_hash(route_payload),
            }
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
            "runtime_authority": runtime_authority,
            "runtime_authority_hash": runtime_authority_hash,
            "authorized_action": authorized_action,
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
        "approval_consumption": approval_consumption_result,
        "side_effect_guard": side_effect_guard_result,
        "result_preview_guard": result_preview_guard_result,
        "context_firewall": context_firewall_result,
        "delegation_inheritance": delegation_inheritance_result,
        "source_quarantine": quarantine_result,
        "synthesis_barrier": synthesis_barrier_result,
        "reference_intake_route": reference_intake_result,
        "reference_acquisition_result": reference_acquisition_result,
        "reference_intake_execution": reference_intake_execution,
        "learning_evidence_gap_route": learning_gap_result,
        "behavioral_eval": behavioral_eval_result,
        "regression_capture": regression_capture_result,
        "producer_artifact_gate": artifact_gate_result,
        "ai_open_quest_advisory": ai_quest_advisory,
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
