from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping

from .enforcement import VALID_EVIDENCE_TYPES, record_failure, required_verifications_for_tier, stable_hash


class BridgeViolation(RuntimeError):
    pass


def _empty_ledger() -> dict[str, Any]:
    return {
        "route_budget": 3,
        "seen_routes": [],
        "failed_signatures": [],
        "transient_failures": {},
        "last_failure_by_route": {},
    }


def _receipt(runtime: Mapping[str, Any], receipt_id: str) -> Mapping[str, Any]:
    receipt = runtime.get("preflight_receipts", {}).get(receipt_id)
    if not isinstance(receipt, Mapping) or receipt.get("allowed") is not True:
        raise BridgeViolation("valid preflight receipt required")
    if receipt.get("consumed"):
        raise BridgeViolation("preflight receipt already consumed")
    return receipt


def _active_attempt(runtime: Mapping[str, Any], receipt: Mapping[str, Any]) -> Mapping[str, Any]:
    execution_key = receipt.get("execution_key")
    active = runtime.get("active_attempts", {}).get(execution_key)
    if not isinstance(active, Mapping) or active.get("receipt_id") != receipt.get("receipt_id", active.get("receipt_id")):
        # Persisted receipts do not duplicate receipt_id inside the receipt body in older states.
        if not isinstance(active, Mapping):
            raise BridgeViolation("receipt has no active attempt")
    return active


def bind_account_attestation(
    runtime: Mapping[str, Any],
    authority: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    if not callable(verifier):
        raise BridgeViolation("account evidence verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("verifier_id required")
    if verifier(evidence) is not True:
        raise BridgeViolation("account evidence verification failed")

    target = authority.get("key", {}).get("AUTHORIZED_TARGET", {})
    expected_account = target.get("value") if isinstance(target, Mapping) else None
    account = evidence.get("account")
    source = evidence.get("source")
    evidence_ref = evidence.get("evidence_ref")
    session_id = evidence.get("session_id")

    if not all(isinstance(v, str) and v.strip() for v in (expected_account, account, source, evidence_ref, session_id)):
        raise BridgeViolation("authenticated account evidence is incomplete")
    if account != expected_account:
        raise BridgeViolation("authenticated account does not match authorized target")
    if evidence.get("authenticated") is not True:
        raise BridgeViolation("authenticated session evidence required")

    updated = deepcopy(dict(runtime))
    updated.setdefault("runtime", {})["account_attestation"] = {
        "account": account,
        "verified": True,
        "source": source,
        "evidence_ref": evidence_ref,
        "session_id": session_id,
        "verified_by": verifier_id.strip(),
    }
    return updated


def _argv_identity(invocation: Mapping[str, Any]) -> str:
    argv = invocation.get("argv")
    if not isinstance(argv, list) or not argv or not isinstance(argv[0], str):
        return ""
    return Path(argv[0]).stem.strip().lower()


def subprocess_runner(invocation: Mapping[str, Any]) -> dict[str, Any]:
    argv = invocation.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(x, str) and x for x in argv)
    ):
        raise BridgeViolation("argv must be a non-empty string list")
    completed = subprocess.run(
        argv,
        shell=False,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def execute_with_receipt(
    runtime: Mapping[str, Any],
    receipt_id: str,
    invocation: Mapping[str, Any],
    *,
    runner: Callable[[Mapping[str, Any]], Mapping[str, Any]] = subprocess_runner,
    executor_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = _receipt(runtime, receipt_id)
    if not isinstance(executor_id, str) or not executor_id.strip():
        raise BridgeViolation("executor_id required")
    if not isinstance(invocation, Mapping):
        raise BridgeViolation("invocation must be an object")

    call = invocation.get("call")
    if not isinstance(call, Mapping):
        raise BridgeViolation("invocation call binding required")
    if stable_hash(dict(call)) != receipt.get("call_digest"):
        raise BridgeViolation("actual invocation call does not match receipt")

    provider = str(invocation.get("provider") or "").strip().lower()
    model = str(call.get("model") or "").strip().lower()
    if not provider or not model:
        raise BridgeViolation("actual provider/model required")

    if receipt.get("call_allowed") is not True:
        if provider != "local" or model != "local":
            raise BridgeViolation("LOCAL_ONLY receipt cannot invoke external provider")

    execution_key = receipt.get("execution_key")
    active = runtime.get("active_attempts", {}).get(execution_key)
    if not isinstance(active, Mapping) or active.get("receipt_id") != receipt_id:
        raise BridgeViolation("receipt has no matching active attempt")
    if active.get("status") != "PENDING":
        raise BridgeViolation("active attempt is not pending")

    expected_tool = str(active.get("attempt", {}).get("method_or_tool") or "").strip().lower()
    actual_tool = str(invocation.get("method_or_tool") or "").strip().lower()
    if expected_tool and actual_tool != expected_tool:
        raise BridgeViolation("actual executor route does not match receipt")

    argv_tool = _argv_identity(invocation)
    aliases = {
        "python": {"python", "python3", "py"},
        "python3": {"python", "python3", "py"},
        "py": {"python", "python3", "py"},
        "powershell": {"powershell", "pwsh"},
        "pwsh": {"powershell", "pwsh"},
        "git": {"git"},
        "claude": {"claude"},
        "codex": {"codex"},
    }
    if actual_tool in aliases and argv_tool and argv_tool not in aliases[actual_tool]:
        raise BridgeViolation("argv executable does not match receipt-bound route")
    if receipt.get("call_allowed") is not True and argv_tool in {"claude", "codex", "openai"}:
        raise BridgeViolation("LOCAL_ONLY receipt cannot invoke external model CLI")
    if receipt.get("call_allowed") is True and model != "local" and provider == "local":
        raise BridgeViolation("external-model receipt requires non-local provider")

    result = dict(runner(invocation))
    result_digest = stable_hash(result)

    updated = deepcopy(dict(runtime))
    calls = updated.setdefault("execution_calls", {})
    if receipt_id in calls:
        raise BridgeViolation("receipt already has an executor call")
    calls[receipt_id] = {
        "executor_id": executor_id.strip(),
        "provider": provider,
        "model": model,
        "actual_calls": 1,
        "method_or_tool": actual_tool,
        "result_digest": result_digest,
        "result": result,
        "status": "RETURNED",
    }
    # Executor is intentionally forbidden from writing SUCCESS/completion/evidence.
    return updated, result


def verify_execution(
    runtime: Mapping[str, Any],
    receipt_id: str,
    *,
    verifier: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
    verifier_id: str,
) -> dict[str, Any]:
    receipt = _receipt(runtime, receipt_id)
    call_record = runtime.get("execution_calls", {}).get(receipt_id)
    if not isinstance(call_record, Mapping):
        raise BridgeViolation("executor result missing")
    if not callable(verifier):
        raise BridgeViolation("independent verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("verifier_id required")
    if verifier_id.strip() == call_record.get("executor_id"):
        raise BridgeViolation("executor cannot self-certify")

    verdict = verifier(call_record, receipt)
    if not isinstance(verdict, Mapping):
        raise BridgeViolation("verifier verdict must be an object")

    orchestration = receipt.get("orchestration", {})
    if not isinstance(orchestration, Mapping):
        raise BridgeViolation("receipt orchestration binding missing")
    expected_verifier_role = orchestration.get("verifier")
    if verdict.get("verifier_role") != expected_verifier_role:
        raise BridgeViolation("verification must be owned by receipt-bound CODEX role")

    evidence_ref = verdict.get("evidence_ref")
    evidence_type = verdict.get("evidence_type")
    if not isinstance(evidence_ref, str) or not evidence_ref:
        raise BridgeViolation("verifier evidence_ref required")
    if evidence_type not in VALID_EVIDENCE_TYPES:
        raise BridgeViolation("unsupported verifier evidence type")

    updated = deepcopy(dict(runtime))
    outcomes = updated.setdefault("execution_outcomes", {})
    active = updated.setdefault("active_attempts", {})
    execution_key = receipt.get("execution_key")

    if verdict.get("passed") is not True:
        outcomes[receipt_id] = "VALIDATION"
        active_item = active.get(execution_key)
        scope = receipt.get("execution_scope")
        if isinstance(active_item, Mapping) and isinstance(scope, str) and scope:
            ledgers = updated.setdefault("route_ledgers", {})
            ledger = ledgers.setdefault(scope, _empty_ledger())
            ledgers[scope] = record_failure(
                ledger,
                active_item.get("attempt", {}),
                "VALIDATION",
            )
        if execution_key in active:
            active.pop(execution_key, None)
        return updated

    required = verdict.get("required_verifications", ["technical", "intent"])
    passed = verdict.get("passed_verifications", [])
    gaps = verdict.get("critical_gaps", [])
    if not isinstance(required, list) or not isinstance(passed, list) or not isinstance(gaps, list):
        raise BridgeViolation("verification lists are malformed")
    minimum = required_verifications_for_tier(
        receipt.get("verification_tier", "STANDARD")
    )
    if not minimum.issubset(set(required)):
        raise BridgeViolation("verifier under-specifies required verification tier")
    if "independent" in set(required):
        expected_reviewer = orchestration.get("independent_reviewer")
        if verdict.get("independent_reviewer") != expected_reviewer:
            raise BridgeViolation(
                "independent verification must be owned by receipt-bound CLAUDE role"
            )
    if verdict.get("key_match") is not True:
        raise BridgeViolation("verifier did not confirm Key match")
    if gaps:
        raise BridgeViolation("verifier reports critical gaps")
    if set(required) - set(passed):
        raise BridgeViolation("verifier has missing required checks")

    outcomes[receipt_id] = "SUCCESS"
    if execution_key in active:
        active[execution_key]["status"] = "SUCCESS"

    updated.setdefault("evidence_registry", {})[evidence_ref] = {
        "type": evidence_type,
        "verified": True,
        "verified_by": verifier_id.strip(),
        "verifier_role": verdict.get("verifier_role"),
        "independent_reviewer": verdict.get("independent_reviewer"),
        "receipt_id": receipt_id,
        "plan_digest": receipt.get("plan_digest"),
        "action_digest": receipt.get("action_digest"),
        "call_digest": receipt.get("call_digest"),
        "result_digest": call_record.get("result_digest"),
    }
    updated.setdefault("completion_registry", {})[receipt_id] = {
        "plan_digest": receipt.get("plan_digest"),
        "action_digest": receipt.get("action_digest"),
        "call_digest": receipt.get("call_digest"),
        "key_match": True,
        "critical_gaps": [],
        "required_verifications": list(required),
        "passed_verifications": list(passed),
        "verifier_role": verdict.get("verifier_role"),
        "independent_reviewer": verdict.get("independent_reviewer"),
        "user_confirmation_ref": None,
        "verified_by": verifier_id.strip(),
    }
    return updated


def record_user_confirmation(
    runtime: Mapping[str, Any],
    receipt_id: str,
    event: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    _receipt(runtime, receipt_id)
    if not callable(verifier):
        raise BridgeViolation("USER event verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("USER event verifier_id required")
    if verifier(event) is not True:
        raise BridgeViolation("USER event verification failed")
    if event.get("actor") != "USER" or event.get("explicit") is not True:
        raise BridgeViolation("only explicit USER confirmation is trusted")
    if event.get("kind") != "confirmation" or event.get("receipt_id") != receipt_id:
        raise BridgeViolation("USER confirmation is not bound to receipt")

    event_ref = event.get("event_ref")
    if not isinstance(event_ref, str) or not event_ref.strip():
        raise BridgeViolation("event_ref required")
    if runtime.get("execution_outcomes", {}).get(receipt_id) != "SUCCESS":
        raise BridgeViolation("cannot confirm an unverified execution")
    completion = runtime.get("completion_registry", {}).get(receipt_id)
    if not isinstance(completion, Mapping):
        raise BridgeViolation("completion record required before confirmation")

    updated = deepcopy(dict(runtime))
    events = updated.setdefault("user_events", {})
    if event_ref in events:
        raise BridgeViolation("user event_ref already exists")
    events[event_ref] = {
        "actor": "USER",
        "kind": "confirmation",
        "receipt_id": receipt_id,
        "explicit": True,
        "verified_by": verifier_id.strip(),
    }
    updated["completion_registry"][receipt_id]["user_confirmation_ref"] = event_ref
    return updated


def record_user_stop(
    runtime: Mapping[str, Any],
    receipt_id: str,
    event: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    receipt = _receipt(runtime, receipt_id)
    if not callable(verifier):
        raise BridgeViolation("USER stop verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("USER stop verifier_id required")
    if verifier(event) is not True:
        raise BridgeViolation("USER stop verification failed")
    if (
        event.get("actor") != "USER"
        or event.get("kind") != "stop"
        or event.get("explicit") is not True
        or event.get("receipt_id") != receipt_id
    ):
        raise BridgeViolation("explicit receipt-bound USER stop required")

    event_ref = event.get("event_ref")
    if not isinstance(event_ref, str) or not event_ref.strip():
        raise BridgeViolation("event_ref required")

    updated = deepcopy(dict(runtime))
    events = updated.setdefault("user_events", {})
    if event_ref in events:
        raise BridgeViolation("user event_ref already exists")
    events[event_ref] = {
        "actor": "USER",
        "kind": "stop",
        "receipt_id": receipt_id,
        "explicit": True,
        "verified_by": verifier_id.strip(),
    }

    updated.setdefault("execution_outcomes", {})[receipt_id] = "ABANDONED"
    execution_key = receipt.get("execution_key")
    if execution_key:
        updated.setdefault("active_attempts", {}).pop(execution_key, None)
    stored_receipt = updated.setdefault("preflight_receipts", {}).get(receipt_id)
    if isinstance(stored_receipt, dict):
        stored_receipt["consumed"] = True
        stored_receipt["abandoned_by"] = event_ref
    completion = updated.setdefault("completion_registry", {}).get(receipt_id)
    if isinstance(completion, dict):
        completion["abandoned_by"] = event_ref
    return updated
