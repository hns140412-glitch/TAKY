#!/usr/bin/env python3
"""Read-only, fail-closed TAKY2 route health check for AI executor selection.

Quote availability and execution authorization are different conditions.
Inspect the *current signed* TAKY2 authority/runtime, before preparing an AI
request. Do not create preflight receipts or clear failed routes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ORCH = Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")
ACTIONS = {
    "Codex": ("verify:codex-packet", "codex"),
    "Claude": ("review:external-model", "claude"),
}
ALLOWED_REPOS = frozenset((
    r"D:\Git PWA\TAKY",
    r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH",
    r"D:\Git PWA\Play Camp",
    r"D:\Git PWA\Ready & Set",
    r"D:\Git PWA\Hide & Seek",
    r"D:\Git PWA\Snap & Pop",
    r"D:\Git PWA\TAKY-MOBILE",
    r"D:\Git PWA\SAVEY",
))


def route_health(executor: str, repo: str, authority: dict, runtime: dict):
    if executor not in ACTIONS or repo not in ALLOWED_REPOS:
        return {"status": "HOLD", "reason": "EXECUTOR_OR_REPOSITORY_UNAPPROVED"}
    from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
    ensure_trusted_taky2()
    from TAKY2.orchestrator import _execution_identity
    from TAKY2.enforcement import route_gate

    action_id, tool = ACTIONS[executor]
    action = authority.get("action_registry", {}).get(action_id)
    if not isinstance(action, dict):
        return {"status": "HOLD", "reason": "TRUSTED_ACTION_MISSING"}
    attempt = {"target": repo, "method_or_tool": tool}
    identity = _execution_identity(action, attempt)
    if identity is None:
        return {"status": "HOLD", "reason": "NO_TRUSTED_EXECUTION_SCOPE"}
    scope, route_fp, execution_key = identity
    active = runtime.get("active_attempts", {}).get(execution_key)
    if isinstance(active, dict):
        prior_receipt_id = active.get("receipt_id")
        call = runtime.get("execution_calls", {}).get(prior_receipt_id)
        settled = isinstance(call, dict) and call.get("status") in ("RETURNED", "FAILED")
        if active.get("status") not in ("FAILED", "RETURNED") and not settled:
            return {"status": "HOLD", "reason": "UNRESOLVED_GOVERNED_EXECUTION",
                    "provider": executor, "executionScope": scope,
                    "ownerState": active.get("status"),
                    "ownerReceiptId": prior_receipt_id}
    ledger = runtime.get("route_ledgers", {}).get(scope, {})
    decision = route_gate({"route_ledger": ledger, "capabilities": []}, attempt)
    if not decision.allowed:
        return {"status": "HOLD", "reason": "ROUTE_GATE_" + str(decision.state),
                "provider": executor, "executionScope": scope,
                "routeGateReason": decision.reason}
    return {"status": "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES",
            "provider": executor, "executionScope": scope,
            "routeGateState": decision.state,
            "modelCallConfirmed": False}


def signed_health(executor: str, repo: str):
    if executor not in ACTIONS or repo not in ALLOWED_REPOS:
        return {"status": "HOLD", "reason": "EXECUTOR_OR_REPOSITORY_UNAPPROVED"}
    if not (ORCH / "TAKY2" / "state" / "runtime.json").is_file():
        return {"status": "HOLD", "reason": "SIGNED_RUNTIME_MISSING"}
    try:
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.state_store import load_bundle, RUNTIME_KEY_PATH
        if not RUNTIME_KEY_PATH.is_file():
            return {"status": "HOLD", "reason": "SIGNED_RUNTIME_KEY_MISSING"}
        authority, runtime, _ = load_bundle()
        result = route_health(executor, repo, authority, runtime)
        result["signedStateIntegrity"] = "PASS"
        result["readOnly"] = True
        result["modelCalls"] = 0
        return result
    except Exception as exc:
        return {"status": "HOLD", "reason": "SIGNED_STATE_VERIFY_FAILED",
                "reasonClass": type(exc).__name__}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--executor", choices=tuple(ACTIONS), required=True)
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()
    print(json.dumps(signed_health(args.executor, args.repo), ensure_ascii=False))
