from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import secrets
from typing import Any, Dict, Mapping

from .enforcement import (
    FAILURE_CLASSES,
    GateResult,
    action_digest,
    context_gate,
    cost_gate,
    done_gate,
    dry_run_gate,
    evaluate_savey_ai_economy,
    key_gate,
    record_failure,
    resolve_action,
    route_fingerprint,
    route_gate,
    safe_tool_gate,
    stable_hash,
    verification_tier,
)
from .bridges import (
    BridgeViolation,
    claim_execution_receipt,
    execute_with_receipt,
    reconcile_execution_claim,
)
from .orchestration import guidance_for_failure, role_assignment, validator_profile
from .state_store import (
    StateConflictError,
    initialize_runtime,
    load_bundle,
    save_runtime,
)
from .verify_from_review_receipt import verify_bound_review


def _gate_item(name: str, result) -> Dict[str, Any]:
    return {
        "gate": name,
        "allowed": result.allowed,
        "state": result.state,
        "reason": result.reason,
        "evidence": list(result.evidence),
        "validator_profile": validator_profile(name),
    }


def _empty_ledger() -> Dict[str, Any]:
    return {
        "route_budget": 3,
        "seen_routes": [],
        "failed_signatures": [],
        "transient_failures": {},
        "last_failure_by_route": {},
    }


def _scoped_trusted(
    trusted: Mapping[str, Any],
    execution_scope: str,
) -> Dict[str, Any]:
    scoped = dict(trusted)
    ledgers = trusted.get("route_ledgers", {})
    ledger = ledgers.get(execution_scope) if isinstance(ledgers, Mapping) else None
    scoped["route_ledger"] = ledger if isinstance(ledger, Mapping) else _empty_ledger()
    return scoped


def _escalation_packet(
    scoped: Mapping[str, Any],
    attempt: Mapping[str, Any],
    *,
    cause: str,
) -> Dict[str, Any]:
    ledger = scoped.get("route_ledger", {})
    failure_by_route = ledger.get("last_failure_by_route", {}) if isinstance(ledger, Mapping) else {}
    attempts = []
    if isinstance(failure_by_route, Mapping):
        for route_fp, item in failure_by_route.items():
            if not isinstance(item, Mapping):
                continue
            attempts.append({
                "route_fp": route_fp,
                "target": item.get("target"),
                "method_or_tool": item.get("method_or_tool"),
                "failure_class": item.get("class"),
            })
    budget = ledger.get("route_budget", 3) if isinstance(ledger, Mapping) else 3
    seen = ledger.get("seen_routes", []) if isinstance(ledger, Mapping) else []
    return {
        "cause": cause,
        "attempts": attempts,
        "remaining_options": [
            "provide materially new input that changes the route/signature",
            "explicitly approve an additional route when budget is exhausted",
        ],
        "recommendation": "prefer materially different evidence-backed route; do not repeat failed path",
        "user_decision_or_info": (
            "approve one additional route or provide materially new information"
            if isinstance(seen, list) and len(seen) >= budget
            else "provide only the missing decision/information required to unblock"
        ),
        "blocked_attempt": {
            "target": attempt.get("target"),
            "method_or_tool": attempt.get("method_or_tool"),
        },
    }


def _execution_identity(
    action: Mapping[str, Any],
    attempt: Mapping[str, Any],
) -> tuple[str, str, str] | None:
    scope = action.get("execution_scope")
    if not isinstance(scope, str) or not scope.strip():
        return None
    scope = scope.strip()
    route_fp = route_fingerprint(attempt)
    execution_key = stable_hash({"scope": scope, "route": route_fp})
    return scope, route_fp, execution_key



def _lowest_sufficient_model(action: Mapping[str, Any]) -> str | None:
    policy = action.get("call_policy", {})
    if not isinstance(policy, Mapping):
        return None
    allowed = policy.get("allowed_models")
    quality = policy.get("model_quality")
    minimum = policy.get("minimum_quality")
    if not isinstance(allowed, list) or not allowed:
        return None
    requirement_class = str(policy.get("requirement_class") or "").strip().upper()
    required_capability = str(policy.get("required_capability") or "").strip().upper()
    model_capabilities = policy.get("model_capabilities", {})
    if requirement_class == "CAPABILITY_REQUIRED" and not required_capability:
        return None
    if requirement_class == "QUALITY_REQUIRED":
        if not isinstance(quality, Mapping) or not isinstance(minimum, int):
            return None

    def capability_ok(name: str) -> bool:
        if requirement_class != "CAPABILITY_REQUIRED":
            return True
        if not isinstance(model_capabilities, Mapping):
            return False
        values = None
        for key, candidate in model_capabilities.items():
            if str(key or "").strip().lower() == name.strip().lower():
                values = candidate
                break
        if not isinstance(values, list):
            return False
        return required_capability in {
            str(v or "").strip().upper() for v in values if isinstance(v, str)
        }

    if isinstance(quality, Mapping) and isinstance(minimum, int):
        ranked = []
        for name in allowed:
            if isinstance(name, str) and isinstance(quality.get(name), int) and capability_ok(name):
                score = quality[name]
                if score >= minimum:
                    ranked.append((score, name))
        if ranked:
            ranked.sort(key=lambda x: (x[0], x[1]))
            return ranked[0][1]
    return next(
        (v for v in allowed if isinstance(v, str) and v.strip() and capability_ok(v)),
        None,
    )


def _safe_correction_for_failure(
    plan: Mapping[str, Any],
    action: Mapping[str, Any],
    gate: str,
    state: str,
    reason: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Correct only execution mechanics; never amend USER intent or authority."""
    gate = str(gate or "").upper()
    state = str(state or "").upper()
    reason_l = str(reason or "").lower()
    corrected = deepcopy(dict(plan))
    context = corrected.get("context")
    attempt = corrected.get("attempt")
    call = corrected.get("call")
    if not isinstance(context, dict) or not isinstance(attempt, dict) or not isinstance(call, dict):
        return None, None

    before = deepcopy({"context": context, "attempt": attempt, "call": call})
    policy = action.get("call_policy", {})
    if not isinstance(policy, Mapping):
        policy = {}

    if gate == "COST":
        if state == "SKIP_FULL_REREAD":
            call["context"] = "delta"
        elif state in {"REROUTE_LOWEST_SUFFICIENT", "REROUTE_QUALITY_FLOOR"}:
            changed = False
            if "model" in reason_l or "quality" in reason_l:
                model = _lowest_sufficient_model(action)
                if model and call.get("model") != model:
                    call["model"] = model
                    changed = True
            if "call count" in reason_l or "expected_calls" in reason_l:
                max_calls = policy.get("max_calls", 1)
                if isinstance(max_calls, int) and max_calls >= 1:
                    # Current receipt executor performs exactly one external invocation.
                    # Batch work inside that invocation instead of emitting a multi-call receipt.
                    corrected_calls = 1
                    call["expected_calls"] = corrected_calls
                    dr = call.get("dry_run_plan")
                    if isinstance(dr, dict):
                        dr["expected_calls"] = corrected_calls
                    changed = True
            if "effort" in reason_l:
                max_effort = policy.get("max_effort", "medium")
                if isinstance(max_effort, str):
                    call["effort"] = max_effort
                    changed = True
            if "batching" in reason_l:
                call["batch_size"] = 1
                changed = True
            if "parallel" in reason_l:
                call["parallel"] = False
                changed = True
            if "subagents" in reason_l:
                call["subagents"] = False
                changed = True
            # Do not force a local substitute merely because an external route is
            # constrained. Capability/quality-required work must preserve acceptance;
            # only explicit trusted sufficiency evidence may justify reuse/local skip.
            if not changed:
                return None, None
        elif state == "THROTTLE_HOLD":
            return None, {
                "status": "HOLD_FOR_REROUTE",
                "terminal": False,
                "reason": reason,
                "next_action": "choose a materially different route; do not repeat the throttled route",
            }
        else:
            return None, None
    elif gate == "CONTEXT" and "full" in reason_l:
        context["mode"] = "delta"
    else:
        return None, None

    after = {"context": context, "attempt": attempt, "call": call}
    if before == after:
        return None, None
    correction = {
        "status": "CORRECTED",
        "terminal": False,
        "gate": gate,
        "state": state,
        "reason": reason,
        "before": before,
        "after": deepcopy(after),
        "principle": "preserve USER intent; correct execution mechanics only",
    }
    return corrected, correction


def preflight(plan: Mapping[str, Any], trusted: Mapping[str, Any], *, _correction_depth: int = 0) -> Dict[str, Any]:
    if not isinstance(plan, Mapping):
        return {
            "allowed": False, "blocked_by": "PLAN", "results": [],
            "receipt_id": None, "call_allowed": False,
            "mode": "BLOCKED", "reason": "plan must be an object",
        }

    task_id = plan.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        return {
            "allowed": False, "blocked_by": "TASK", "results": [],
            "receipt_id": None, "call_allowed": False,
            "mode": "BLOCKED", "reason": "task_id required",
        }
    task_id = task_id.strip()

    for section in ("context", "attempt", "call"):
        if not isinstance(plan.get(section), Mapping):
            return {
                "allowed": False, "blocked_by": "PLAN", "results": [],
                "receipt_id": None, "call_allowed": False,
                "mode": "BLOCKED", "reason": f"{section} must be an object",
            }

    action = resolve_action(trusted, plan)
    if action is None:
        guidance = guidance_for_failure(
            "KEY",
            "BLOCKED",
            "unregistered action_id",
        )
        return {
            "allowed": False,
            "blocked_by": "KEY",
            "results": [],
            "receipt_id": None,
            "call_allowed": False,
            "mode": guidance["mode"],
            "reason": "unregistered action_id",
            "guidance": guidance,
            "orchestration": role_assignment({}, verification_tier="STANDARD"),
        }

    identity = _execution_identity(action, plan["attempt"])
    if identity is None:
        guidance = guidance_for_failure(
            "KEY",
            "BLOCKED",
            "trusted execution_scope missing",
        )
        return {
            "allowed": False,
            "blocked_by": "KEY",
            "results": [],
            "receipt_id": None,
            "call_allowed": False,
            "mode": guidance["mode"],
            "reason": "trusted execution_scope missing",
            "guidance": guidance,
            "orchestration": role_assignment(
                action,
                verification_tier=verification_tier(action),
            ),
        }
    execution_scope, route_fp, execution_key = identity

    active = trusted.get("active_attempts", {}).get(execution_key)
    settled_execution = False
    if isinstance(active, Mapping):
        prior_receipt = active.get("receipt_id")
        prior_call = trusted.get("execution_calls", {}).get(prior_receipt)
        settled_execution = (
            isinstance(prior_call, Mapping)
            and prior_call.get("status") in {"RETURNED", "FAILED"}
        )
    if (
        isinstance(active, Mapping)
        and active.get("status") not in {"FAILED", "RETURNED"}
        and not settled_execution
    ):
        reason = "unresolved attempt already owns this trusted route"
        guidance = guidance_for_failure("ROUTE", "BLOCKED", reason)
        return {
            "allowed": False,
            "blocked_by": "ROUTE",
            "results": [],
            "receipt_id": None,
            "call_allowed": False,
            "mode": guidance["mode"],
            "reason": reason,
            "guidance": guidance,
            "orchestration": role_assignment(
                action,
                verification_tier=verification_tier(action),
            ),
        }

    scoped = _scoped_trusted(trusted, execution_scope)

    # SAFE_TOOL is a deterministic precheck. It does not redefine the
    # canonical KEY/CONTEXT/ROUTE/COST/DONE HARD GATE model.
    safe_tool_result = safe_tool_gate(plan.get("tool_action"))
    if not safe_tool_result.allowed:
        guidance = guidance_for_failure("ROUTE", safe_tool_result.state, safe_tool_result.reason)
        return {
            "allowed": False,
            "blocked_by": "SAFE_TOOL",
            "results": [_gate_item("SAFE_TOOL", safe_tool_result)],
            "receipt_id": None,
            "call_allowed": False,
            "mode": guidance["mode"],
            "terminal": False,
            "reason": safe_tool_result.reason,
            "guidance": guidance,
            "orchestration": role_assignment(
                action,
                verification_tier=verification_tier(action),
            ),
            "safe_tool_evaluation": _gate_item("SAFE_TOOL", safe_tool_result),
        }

    economy_result = evaluate_savey_ai_economy(
        scoped,
        action,
        plan["call"],
        route_fp=route_fp,
    )
    dry_run_result = None
    if economy_result.allowed and economy_result.state != "SKIP_CALL":
        dry_run_result = dry_run_gate(scoped, action, plan["call"])
        if not dry_run_result.allowed:
            economy_result = dry_run_result
        else:
            economy_result = GateResult(
                True,
                economy_result.state,
                economy_result.reason,
                tuple(economy_result.evidence) + tuple(dry_run_result.evidence),
            )
    economy_evaluation = {
        "policy": "SAVEY_AI_ECONOMY",
        "owner": "DRIVER",
        "decision_sequence": [
            "NECESSITY",
            "REUSE_CACHE",
            "LOCAL_DETERMINISTIC",
            "LOWEST_SUFFICIENT_CAPABILITY",
            "DRY_RUN_PLAN",
            "BATCH_CONTEXT_REUSE",
            "THROTTLE",
            "EXECUTE",
            "VERIFY",
        ],
        "state": economy_result.state,
        "reason": economy_result.reason,
        "evidence": list(economy_result.evidence),
        "dry_run": (
            {
                "state": dry_run_result.state,
                "reason": dry_run_result.reason,
                "evidence": list(dry_run_result.evidence),
            }
            if dry_run_result is not None
            else None
        ),
    }
    checks = [
        ("KEY", lambda: key_gate(trusted, plan)),
        ("CONTEXT", lambda: context_gate(trusted, plan["context"])),
        ("ROUTE", lambda: route_gate(scoped, plan["attempt"])),
        ("COST", lambda: cost_gate(trusted, action, plan["call"], evaluation=economy_result)),
    ]

    results = []
    call_allowed = True
    for name, run in checks:
        result = run()
        results.append(_gate_item(name, result))
        if name == "COST" and result.state == "SKIP_CALL":
            call_allowed = False
        if not result.allowed:
            tier = verification_tier(action)
            guidance = guidance_for_failure(name, result.state, result.reason)

            # TAKY is a navigation/correction system, not a terminal blocking wall.
            # For deterministic execution-mechanics mistakes, correct once and
            # immediately re-run preflight. Authority/USER-intent changes are never
            # synthesized here.
            if _correction_depth < 1:
                corrected_plan, correction = _safe_correction_for_failure(
                    plan, action, name, result.state, result.reason
                )
                if corrected_plan is not None and correction is not None:
                    redirected = preflight(
                        corrected_plan,
                        trusted,
                        _correction_depth=_correction_depth + 1,
                    )
                    redirected = dict(redirected)
                    redirected["correction"] = correction
                    redirected["original_plan_digest"] = stable_hash(dict(plan))
                    redirected["corrected_plan_digest"] = stable_hash(dict(corrected_plan))
                    if redirected.get("allowed") is True:
                        redirected["mode"] = (
                            "CORRECTED_CALL_ALLOWED"
                            if redirected.get("call_allowed") is True
                            else "CORRECTED_LOCAL_ONLY"
                        )
                    return redirected

            blocked = {
                "allowed": False,
                "blocked_by": name,
                "results": results,
                "receipt_id": None,
                "call_allowed": False,
                "mode": guidance["mode"],
                "terminal": bool(guidance.get("terminal", False)),
                "reason": result.reason,
                "guidance": guidance,
                "orchestration": role_assignment(
                    action,
                    verification_tier=tier,
                ),
                "economy_evaluation": economy_evaluation,
            }
            if name == "ROUTE" and result.state == "USER_DECISION_REQUIRED":
                blocked["escalation_packet"] = _escalation_packet(
                    scoped,
                    plan["attempt"],
                    cause=result.reason,
                )
            return blocked

    approval_keys = []
    for item in results:
        for ev in item.get("evidence", []):
            if isinstance(ev, str) and ev.startswith("approval-key:"):
                key = ev[len("approval-key:"):]
                if key not in approval_keys:
                    approval_keys.append(key)

    approval_uses = {}
    approvals = trusted.get("approvals", {})
    for key in approval_keys:
        ref = approvals.get(key) if isinstance(approvals, Mapping) else None
        if isinstance(ref, str) and ref:
            approval_uses[key] = ref

    plan_digest = stable_hash(dict(plan))
    call_digest = stable_hash(dict(plan["call"]))
    receipt_id = f"pf:{task_id}:{secrets.token_hex(8)}"
    return {
        "allowed": True,
        "blocked_by": None,
        "results": results,
        "receipt_id": receipt_id,
        "task_id": task_id,
        "plan_digest": plan_digest,
        "call_digest": call_digest,
        "action_id": plan.get("action_id"),
        "action_digest": action_digest(action),
        "semantic_owner_ref": action.get("semantic_owner_ref"),
        "semantic_owner_scope": action.get("semantic_owner_scope"),
        "verification_tier": verification_tier(action),
        "orchestration": role_assignment(
            action,
            verification_tier=verification_tier(action),
        ),
        "economy_evaluation": economy_evaluation,
        "safe_tool_evaluation": _gate_item("SAFE_TOOL", safe_tool_result),
        "execution_scope": execution_scope,
        "execution_key": execution_key,
        "route_fp": route_fp,
        "authority_digest": trusted.get("_authority_digest"),
        "call_allowed": call_allowed,
        "mode": "CALL_ALLOWED" if call_allowed else "LOCAL_ONLY",
        "attempt": dict(plan["attempt"]),
        "approval_uses": approval_uses,
    }


CONTROL_ROLE_BY_GATE = {
    "SAFE_TOOL": "NAVIGATOR",
    "KEY": "GUARDIAN",
    "CONTEXT": "NAVIGATOR",
    "ROUTE": "NAVIGATOR",
    "COST": "DRIVER",
    "DONE": "GUARDIAN",
}


def control_incident_from_preflight(
    out: Mapping[str, Any],
    plan: Mapping[str, Any],
    trusted: Mapping[str, Any],
) -> Dict[str, Any] | None:
    if out.get("allowed") is True:
        return None
    gate = str(out.get("blocked_by") or "").upper()
    if gate not in CONTROL_ROLE_BY_GATE:
        return None
    action = resolve_action(trusted, plan) or {}
    results = out.get("results", [])
    last = results[-1] if isinstance(results, list) and results else {}
    guidance = out.get("guidance", {})
    incident_basis = {
        "task_id": plan.get("task_id"),
        "action_id": plan.get("action_id"),
        "gate": gate,
        "state": last.get("state") if isinstance(last, Mapping) else None,
        "reason": out.get("reason"),
        "execution_scope": action.get("execution_scope"),
        "authority_digest": trusted.get("_authority_digest"),
    }
    incident_id = "ci:" + stable_hash(incident_basis)
    unknown = None
    packet = out.get("escalation_packet")
    if isinstance(packet, Mapping):
        unknown = packet.get("user_decision_or_info")
    return {
        "incident_id": incident_id,
        "task_id": plan.get("task_id"),
        "action_id": plan.get("action_id"),
        "gate": gate,
        "control_role": CONTROL_ROLE_BY_GATE[gate],
        "cause": {
            "state": last.get("state") if isinstance(last, Mapping) else None,
            "reason": out.get("reason"),
        },
        "observed_evidence": (
            list(last.get("evidence", [])) if isinstance(last, Mapping) else []
        ),
        "decision": out.get("mode"),
        "route_chosen": (
            guidance.get("next_action") if isinstance(guidance, Mapping) else None
        ),
        "result": "CONTROL_INTERVENTION",
        "remaining_unknown": unknown,
        "semantic_owner_ref": action.get("semantic_owner_ref"),
        "semantic_owner_scope": action.get("semantic_owner_scope"),
        "authority_digest": trusted.get("_authority_digest"),
        "economy_evaluation": (
            dict(out.get("economy_evaluation", {}))
            if gate == "COST" and isinstance(out.get("economy_evaluation"), Mapping)
            else None
        ),
    }


def persist_control_incident(
    runtime: Mapping[str, Any],
    out: Mapping[str, Any],
    plan: Mapping[str, Any],
    trusted: Mapping[str, Any],
) -> Dict[str, Any]:
    incident = control_incident_from_preflight(out, plan, trusted)
    updated = deepcopy(dict(runtime))
    if incident is None:
        return updated
    registry = updated.setdefault("control_incidents", {})
    incident_id = incident["incident_id"]
    existing = registry.get(incident_id)
    occurrence_count = (
        int(existing.get("occurrence_count", 0)) + 1
        if isinstance(existing, Mapping)
        else 1
    )
    incident["occurrence_count"] = occurrence_count
    registry[incident_id] = incident
    return updated


DONE_CONTROL_INCIDENT_STATES = {"REWORK", "PARTIAL", "BLOCKED", "NOT_DONE"}


def control_incident_from_done(
    runtime: Mapping[str, Any],
    report: Mapping[str, Any],
    out: Mapping[str, Any],
) -> Dict[str, Any] | None:
    state = str(out.get("state") or "").upper()
    if out.get("allowed") is True or state not in DONE_CONTROL_INCIDENT_STATES:
        return None
    receipt_id = report.get("preflight_receipt")
    receipt = (
        runtime.get("preflight_receipts", {}).get(receipt_id)
        if isinstance(receipt_id, str)
        else None
    )
    authority_digest = (
        receipt.get("authority_digest")
        if isinstance(receipt, Mapping)
        else runtime.get("authority_digest")
    )
    reason = out.get("reason")
    incident_basis = {
        "receipt_id": receipt_id,
        "gate": "DONE",
        "state": state,
        "reason": reason,
        "authority_digest": authority_digest,
    }
    route_by_state = {
        "REWORK": "repair critical gaps/key mismatch, then reverify before DONE",
        "PARTIAL": "complete missing verification/evidence, then retry DONE",
        "BLOCKED": "repair DONE contract/evidence bindings before retry",
        "NOT_DONE": "supply current receipt-bound completion/evidence before retry",
    }
    return {
        "incident_id": "ci:" + stable_hash(incident_basis),
        "receipt_id": receipt_id,
        "task_id": receipt.get("task_id") if isinstance(receipt, Mapping) else None,
        "action_id": receipt.get("action_id") if isinstance(receipt, Mapping) else None,
        "gate": "DONE",
        "control_role": CONTROL_ROLE_BY_GATE["DONE"],
        "cause": {
            "state": state,
            "reason": reason,
        },
        "observed_evidence": list(out.get("evidence", [])),
        "decision": state,
        "route_chosen": route_by_state[state],
        "result": "CONTROL_INTERVENTION",
        "remaining_unknown": reason,
        "semantic_owner_ref": (
            receipt.get("semantic_owner_ref") if isinstance(receipt, Mapping) else None
        ),
        "semantic_owner_scope": (
            receipt.get("semantic_owner_scope") if isinstance(receipt, Mapping) else None
        ),
        "authority_digest": authority_digest,
        "economy_evaluation": None,
    }


def persist_done_control_incident(
    runtime: Mapping[str, Any],
    report: Mapping[str, Any],
    out: Mapping[str, Any],
) -> Dict[str, Any]:
    incident = control_incident_from_done(runtime, report, out)
    updated = deepcopy(dict(runtime))
    if incident is None:
        return updated
    registry = updated.setdefault("control_incidents", {})
    incident_id = incident["incident_id"]
    existing = registry.get(incident_id)
    occurrence_count = (
        int(existing.get("occurrence_count", 0)) + 1
        if isinstance(existing, Mapping)
        else 1
    )
    incident["occurrence_count"] = occurrence_count
    registry[incident_id] = incident
    return updated


def persist_preflight(runtime: Mapping[str, Any], out: Mapping[str, Any]) -> Dict[str, Any]:
    updated = deepcopy(dict(runtime))
    receipt_id = out.get("receipt_id")
    if not (out.get("allowed") and isinstance(receipt_id, str) and receipt_id):
        return updated

    receipt = {
        "allowed": True,
        "task_id": out.get("task_id"),
        "plan_digest": out.get("plan_digest"),
        "call_digest": out.get("call_digest"),
        "action_id": out.get("action_id"),
        "action_digest": out.get("action_digest"),
        "semantic_owner_ref": out.get("semantic_owner_ref"),
        "semantic_owner_scope": out.get("semantic_owner_scope"),
        "verification_tier": out.get("verification_tier", "STANDARD"),
        "orchestration": dict(out.get("orchestration", {})),
        "economy_evaluation": deepcopy(dict(out.get("economy_evaluation", {}))),
        "execution_scope": out.get("execution_scope"),
        "execution_key": out.get("execution_key"),
        "route_fp": out.get("route_fp"),
        "authority_digest": out.get("authority_digest"),
        "call_allowed": bool(out.get("call_allowed")),
        "approval_uses": dict(out.get("approval_uses", {})),
        "gate_receipts": deepcopy(list(out.get("results", []))),
        "consumed": False,
    }
    updated.setdefault("preflight_receipts", {})[receipt_id] = receipt

    consumed = updated.setdefault("consumed_approvals", {})
    for key, ref in out.get("approval_uses", {}).items():
        if isinstance(key, str) and isinstance(ref, str) and key and ref:
            consumed[key] = ref

    scope = out["execution_scope"]
    ledgers = updated.setdefault("route_ledgers", {})
    ledger = ledgers.setdefault(scope, _empty_ledger())
    seen = ledger.setdefault("seen_routes", [])
    route_fp = out["route_fp"]
    if route_fp not in seen:
        seen.append(route_fp)

    updated.setdefault("active_attempts", {})[out["execution_key"]] = {
        "receipt_id": receipt_id,
        "task_id": out["task_id"],
        "action_id": out["action_id"],
        "semantic_owner_ref": out.get("semantic_owner_ref"),
        "semantic_owner_scope": out.get("semantic_owner_scope"),
        "execution_scope": scope,
        "attempt": dict(out["attempt"]),
        "route_fp": route_fp,
        "status": "PENDING",
    }
    return updated


def record_outcome(
    runtime: Mapping[str, Any],
    receipt_id: str,
    outcome: str,
) -> Dict[str, Any]:
    updated = deepcopy(dict(runtime))
    active = updated.setdefault("active_attempts", {})
    match_key = None
    match = None
    for execution_key, item in active.items():
        if isinstance(item, Mapping) and item.get("receipt_id") == receipt_id:
            match_key = execution_key
            match = item
            break
    if match is None:
        raise ValueError("receipt has no active attempt")
    if match.get("status") == "OUTCOME_UNKNOWN":
        raise ValueError("unknown execution outcome requires evidence-bound resolution")

    attempt = match.get("attempt", {})
    outcomes = updated.setdefault("execution_outcomes", {})

    if outcome == "SUCCESS":
        outcomes[receipt_id] = "SUCCESS"
        active[match_key]["status"] = "SUCCESS"
        return updated

    if outcome not in FAILURE_CLASSES:
        raise ValueError("unknown failure outcome")

    scope = match.get("execution_scope")
    ledgers = updated.setdefault("route_ledgers", {})
    ledger = ledgers.setdefault(scope, _empty_ledger())
    ledgers[scope] = record_failure(ledger, attempt, outcome)
    outcomes[receipt_id] = outcome
    active.pop(match_key, None)
    return updated


def finalize(report: Mapping[str, Any], trusted: Mapping[str, Any]) -> Dict[str, Any]:
    result = done_gate(trusted, report)
    return {
        "allowed": result.allowed,
        "state": result.state,
        "reason": result.reason,
        "evidence": list(result.evidence),
        "validator_profile": validator_profile("DONE"),
    }


def persist_done_gate_receipt(
    runtime: Mapping[str, Any],
    report: Mapping[str, Any],
    out: Mapping[str, Any],
) -> Dict[str, Any]:
    updated = deepcopy(dict(runtime))
    receipt_id = report.get("preflight_receipt")
    receipt = updated.get("preflight_receipts", {}).get(receipt_id)
    authority_digest = (
        receipt.get("authority_digest")
        if isinstance(receipt, Mapping)
        else updated.get("authority_digest")
    )
    decision_id = "done:" + stable_hash({
        "receipt_id": receipt_id,
        "report": dict(report),
        "state": out.get("state"),
        "authority_digest": authority_digest,
    })
    updated.setdefault("done_gate_receipts", {})[decision_id] = {
        "decision_id": decision_id,
        "receipt_id": receipt_id,
        "allowed": bool(out.get("allowed")),
        "state": out.get("state"),
        "reason": out.get("reason"),
        "evidence": list(out.get("evidence", [])),
        "validator_profile": deepcopy(dict(out.get("validator_profile", {}))),
        "authority_digest": authority_digest,
        "semantic_owner_ref": receipt.get("semantic_owner_ref") if isinstance(receipt, Mapping) else None,
        "semantic_owner_scope": receipt.get("semantic_owner_scope") if isinstance(receipt, Mapping) else None,
        "report_digest": stable_hash(dict(report)),
    }
    return updated


def consume_receipt(runtime: Mapping[str, Any], receipt_id: str) -> Dict[str, Any]:
    updated = deepcopy(dict(runtime))
    receipt = updated.setdefault("preflight_receipts", {}).get(receipt_id)
    if isinstance(receipt, dict):
        receipt["consumed"] = True
        execution_key = receipt.get("execution_key")
        if execution_key:
            updated.setdefault("active_attempts", {}).pop(execution_key, None)
    return updated


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser(description="TAKY 2.0 hard-gate runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-state")

    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("plan_json")

    p_exec = sub.add_parser("execute")
    p_exec.add_argument("receipt_id")
    p_exec.add_argument("invocation_json")
    p_exec.add_argument("--executor-id", default="TAKY2_EXECUTOR_WRAPPER")

    p_fail = sub.add_parser("record-failure")
    p_fail.add_argument("receipt_id")
    p_fail.add_argument("failure_class")

    p_verify = sub.add_parser("verify-review")
    p_verify.add_argument("target_receipt")
    p_verify.add_argument("review_receipt")

    p_done = sub.add_parser("done")
    p_done.add_argument("report_json")

    args = parser.parse_args()

    if args.cmd == "init-state":
        initialize_runtime()
        print(json.dumps({"allowed": True, "state": "RUNTIME_INITIALIZED"}))
        return 0

    trusted, runtime, auth_digest = load_bundle()

    if args.cmd == "preflight":
        plan = _load_json(args.plan_json)
        out = preflight(plan, trusted)
        updated = (
            persist_preflight(runtime, out)
            if out.get("allowed")
            else persist_control_incident(runtime, out, plan, trusted)
        )
        if updated != runtime:
            save_runtime(
                updated,
                expected_version=runtime["runtime_version"],
                authority_digest_value=auth_digest,
            )
        print(json.dumps(out, ensure_ascii=False, indent=2))
        if not out.get("allowed"):
            return 2
        return 0 if out.get("call_allowed") else 3

    if args.cmd == "execute":
        invocation = _load_json(args.invocation_json)
        reserved_runtime = None
        checkpoint_box = {}
        try:
            reserved_candidate, claim_token = claim_execution_receipt(
                runtime,
                args.receipt_id,
                executor_id=args.executor_id,
            )
            reserved_runtime = save_runtime(
                reserved_candidate,
                expected_version=runtime["runtime_version"],
                authority_digest_value=auth_digest,
            )

            def persist_calling(candidate):
                saved = save_runtime(
                    candidate,
                    expected_version=reserved_runtime["runtime_version"],
                    authority_digest_value=auth_digest,
                )
                checkpoint_box["runtime"] = saved
                return saved

            updated, result = execute_with_receipt(
                reserved_runtime,
                args.receipt_id,
                invocation,
                executor_id=args.executor_id,
                preclaimed=True,
                claim_token=claim_token,
                pre_run_checkpoint=persist_calling,
            )
        except Exception as exc:
            reconcile_base = checkpoint_box.get("runtime") or reserved_runtime
            if isinstance(reconcile_base, dict):
                try:
                    reconciled = reconcile_execution_claim(
                        reconcile_base,
                        args.receipt_id,
                        reconciler_id="TAKY_EXECUTE_CLI",
                        reason=str(exc),
                    )
                    save_runtime(
                        reconciled,
                        expected_version=reconcile_base["runtime_version"],
                        authority_digest_value=auth_digest,
                    )
                except Exception:
                    pass
            print(json.dumps({
                "allowed": False,
                "state": "BLOCKED",
                "reason": str(exc),
            }, ensure_ascii=False))
            return 2
        try:
            save_runtime(
                updated,
                expected_version=updated["runtime_version"],
                authority_digest_value=auth_digest,
            )
        except StateConflictError as exc:
            _, latest_runtime, latest_digest = load_bundle()
            latest_call = latest_runtime.get("execution_calls", {}).get(args.receipt_id)
            if isinstance(latest_call, Mapping) and latest_call.get("status") in {"CLAIMED", "CALLING"}:
                reconciled = reconcile_execution_claim(
                    latest_runtime,
                    args.receipt_id,
                    reconciler_id="TAKY_EXECUTE_CAS_RECONCILER",
                    reason="result persistence conflict: " + str(exc),
                )
                save_runtime(
                    reconciled,
                    expected_version=latest_runtime["runtime_version"],
                    authority_digest_value=latest_digest,
                )
            print(json.dumps({
                "allowed": False,
                "state": "EXECUTION_OUTCOME_UNKNOWN",
                "receipt_id": args.receipt_id,
                "reason": "runtime changed before external result could be durably persisted",
            }, ensure_ascii=False))
            return 2
        execution_ok = result.get("returncode") in {None, 0}
        print(json.dumps({
            "allowed": execution_ok,
            "state": "EXECUTOR_RETURNED_UNVERIFIED" if execution_ok else "EXECUTOR_FAILED",
            "receipt_id": args.receipt_id,
            "result": result,
        }, ensure_ascii=False, indent=2))
        return 0 if execution_ok else 2

    if args.cmd == "verify-review":
        try:
            updated = verify_bound_review(
                runtime,
                args.target_receipt,
                args.review_receipt,
            )
        except BridgeViolation as exc:
            print(json.dumps({
                "allowed": False,
                "state": "VERIFICATION_BLOCKED",
                "reason": str(exc),
            }, ensure_ascii=False))
            return 2
        save_runtime(
            updated,
            expected_version=runtime["runtime_version"],
            authority_digest_value=auth_digest,
        )
        completion = updated.get("completion_registry", {}).get(args.target_receipt, {})
        print(json.dumps({
            "allowed": True,
            "state": "EXECUTION_VERIFIED",
            "target_receipt": args.target_receipt,
            "review_receipt": args.review_receipt,
            "evidence_refs": completion.get("evidence_refs", []),
        }, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "record-failure":
        if args.failure_class not in FAILURE_CLASSES:
            print(json.dumps({
                "allowed": False,
                "state": "BLOCKED",
                "reason": "record-failure accepts failure classes only",
            }))
            return 2
        updated = record_outcome(runtime, args.receipt_id, args.failure_class)
        save_runtime(
            updated,
            expected_version=runtime["runtime_version"],
            authority_digest_value=auth_digest,
        )
        print(json.dumps({
            "allowed": True,
            "state": "FAILURE_RECORDED",
            "outcome": args.failure_class,
        }))
        return 0

    report = _load_json(args.report_json)
    out = finalize(report, trusted)
    updated = persist_done_gate_receipt(runtime, report, out)
    updated = persist_done_control_incident(updated, report, out)
    if out.get("state") == "USER_CONFIRMED":
        rid = report.get("preflight_receipt")
        updated = consume_receipt(updated, rid)
    save_runtime(
        updated,
        expected_version=runtime["runtime_version"],
        authority_digest_value=auth_digest,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("allowed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
