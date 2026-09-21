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
from pathlib import Path

from c2s_preflight_bridge import run as run_c2s_preflight
from codex_task_contract_builder import build as build_codex_task_contract
from executor_transport import build_envelope as build_executor_envelope
from executor_adapter_registry import resolve as resolve_executor_adapter

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
    elif action not in {"STATUS_REPORT"}:
        # execution_owner is the actual actor/tool owner, while route_role is the
        # capability family that must own the next step.
        if not owner:
            failures.append("EXECUTION_OWNER_MISSING")

    state = {
        "task_id": record.get("task_id"),
        "primary_outcome": wm.get("primary_outcome"),
        "priority_order": wm.get("priority_order", []),
        "protected_state": wm.get("protected_state", []),
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
    }
    return state, failures

def run(record: dict, repo_root: Path, coverage_record: Path | None) -> dict:
    # Entering the controlled TAKY runtime is itself a material TAKY-governed turn.
    # Do not depend on the caller/user to opt into TAKY governance.
    effective_record = dict(record)
    effective_record["material_taky_turn"] = True
    gate = run_c2s_preflight(effective_record, repo_root, coverage_record)
    state, runtime_failures = derive_runtime_state(effective_record)
    detected = list(dict.fromkeys(list(gate.get("detected", [])) + runtime_failures))

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
        "claim_ceiling": "CONTROLLED_REPOSITORY_RUNTIME",
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
