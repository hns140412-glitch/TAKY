from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import secrets
from typing import Any, Dict, Mapping

from .enforcement import (
    FAILURE_CLASSES,
    action_digest,
    context_gate,
    cost_gate,
    done_gate,
    key_gate,
    record_failure,
    resolve_action,
    route_fingerprint,
    route_gate,
    stable_hash,
    verification_tier,
)
from .bridges import BridgeViolation, execute_with_receipt
from .orchestration import guidance_for_failure, role_assignment, validator_profile
from .state_store import initialize_runtime, load_bundle, save_runtime


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


def preflight(plan: Mapping[str, Any], trusted: Mapping[str, Any]) -> Dict[str, Any]:
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
    if isinstance(active, Mapping) and active.get("status") in {"PENDING", "SUCCESS"}:
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
    checks = [
        ("KEY", lambda: key_gate(trusted, plan)),
        ("CONTEXT", lambda: context_gate(trusted, plan["context"])),
        ("ROUTE", lambda: route_gate(scoped, plan["attempt"])),
        ("COST", lambda: cost_gate(trusted, action, plan["call"])),
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
            blocked = {
                "allowed": False,
                "blocked_by": name,
                "results": results,
                "receipt_id": None,
                "call_allowed": False,
                "mode": guidance["mode"],
                "reason": result.reason,
                "guidance": guidance,
                "orchestration": role_assignment(
                    action,
                    verification_tier=tier,
                ),
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
        "verification_tier": verification_tier(action),
        "orchestration": role_assignment(
            action,
            verification_tier=verification_tier(action),
        ),
        "execution_scope": execution_scope,
        "execution_key": execution_key,
        "route_fp": route_fp,
        "authority_digest": trusted.get("_authority_digest"),
        "call_allowed": call_allowed,
        "mode": "CALL_ALLOWED" if call_allowed else "LOCAL_ONLY",
        "attempt": dict(plan["attempt"]),
        "approval_uses": approval_uses,
    }


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
        "verification_tier": out.get("verification_tier", "STANDARD"),
        "orchestration": dict(out.get("orchestration", {})),
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
    }


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
        if out.get("allowed"):
            updated = persist_preflight(runtime, out)
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
        try:
            updated, result = execute_with_receipt(
                runtime,
                args.receipt_id,
                invocation,
                executor_id=args.executor_id,
            )
        except BridgeViolation as exc:
            print(json.dumps({
                "allowed": False,
                "state": "BLOCKED",
                "reason": str(exc),
            }, ensure_ascii=False))
            return 2
        save_runtime(
            updated,
            expected_version=runtime["runtime_version"],
            authority_digest_value=auth_digest,
        )
        print(json.dumps({
            "allowed": True,
            "state": "EXECUTOR_RETURNED_UNVERIFIED",
            "receipt_id": args.receipt_id,
            "result": result,
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
    if out.get("state") == "USER_CONFIRMED":
        rid = report.get("preflight_receipt")
        updated = consume_receipt(runtime, rid)
        save_runtime(
            updated,
            expected_version=runtime["runtime_version"],
            authority_digest_value=auth_digest,
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("allowed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
