#!/usr/bin/env python3
"""TAKY executor transport envelope.

Creates and validates a provider-neutral dispatch envelope around a validated
implementation task contract. The built-in transport is FILE_QUEUE: it makes the
handoff machine-readable and integrity-bound without falsely claiming that an
external Codex service was invoked.

A future provider adapter can consume the same envelope and return a receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SUPPORTED_PROVIDERS = {"CODEX"}
SUPPORTED_TRANSPORTS = {"FILE_QUEUE", "GITHUB_ISSUE_QUEUE", "EXTERNAL_ADAPTER"}
EXECUTION_OUTCOME_STATES = {"NOT_STARTED", "RUNNING", "SUCCEEDED", "FAILED_CONFIRMED", "OUTCOME_UNKNOWN"}
EFFECT_CLASSES = {"READ_ONLY", "REPLAY_SAFE_MUTATION", "NON_IDEMPOTENT_MUTATION"}
RECONCILE_EFFECT_STATES = {"NOT_APPLIED", "APPLIED_CONFIRMED", "UNKNOWN"}

def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_json(value: dict) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def normalize_effect_policy(task_contract: dict) -> tuple[dict, list[str]]:
    raw = task_contract.get("effect_policy")
    if raw is None:
        return {
            "effect_class": "READ_ONLY",
            "request_fingerprint": None,
            "reconcile_before_retry": False,
            "retry_budget": 0,
            "compensation_ref": None,
        }, []
    if not isinstance(raw, dict):
        return {}, ["EFFECT_POLICY_INVALID"]

    detected: list[str] = []
    effect_class = str(raw.get("effect_class", "")).strip().upper()
    if effect_class not in EFFECT_CLASSES:
        detected.append(f"EFFECT_CLASS_INVALID:{effect_class or 'MISSING'}")

    fingerprint = raw.get("request_fingerprint")
    valid_fingerprint = (
        isinstance(fingerprint, str)
        and len(fingerprint) == 64
        and all(ch in "0123456789abcdef" for ch in fingerprint)
    )
    if effect_class != "READ_ONLY" and not valid_fingerprint:
        detected.append("EFFECT_REQUEST_FINGERPRINT_REQUIRED")
    elif effect_class == "READ_ONLY" and fingerprint not in (None, "") and not valid_fingerprint:
        detected.append("EFFECT_REQUEST_FINGERPRINT_INVALID")

    retry_budget = raw.get("retry_budget")
    if not isinstance(retry_budget, int) or isinstance(retry_budget, bool) or not 0 <= retry_budget <= 5:
        detected.append("EFFECT_RETRY_BUDGET_INVALID")

    reconcile = raw.get("reconcile_before_retry")
    if not isinstance(reconcile, bool):
        detected.append("EFFECT_RECONCILE_FLAG_INVALID")
    if effect_class == "NON_IDEMPOTENT_MUTATION" and reconcile is not True:
        detected.append("NON_IDEMPOTENT_RECONCILE_REQUIRED")

    compensation_ref = raw.get("compensation_ref")
    if compensation_ref is not None and (
        not isinstance(compensation_ref, str) or not compensation_ref.strip()
    ):
        detected.append("EFFECT_COMPENSATION_REF_INVALID")

    return {
        "effect_class": effect_class,
        "request_fingerprint": fingerprint,
        "reconcile_before_retry": reconcile,
        "retry_budget": retry_budget,
        "compensation_ref": compensation_ref,
    }, detected

def derive_operation_key(task_id: str, task_contract_sha256: str, effect_policy: dict) -> str:
    seed = {
        "task_id": task_id,
        "task_contract_sha256": task_contract_sha256,
        "effect_class": effect_policy.get("effect_class"),
        "request_fingerprint": effect_policy.get("request_fingerprint"),
    }
    return "taky-op-" + sha256_json(seed)[:32]

def build_envelope(task_contract: dict, transport: str = "FILE_QUEUE", provider: str = "CODEX") -> dict:
    provider = str(provider).strip().upper()
    transport = str(transport).strip().upper()
    detected: list[str] = []

    if provider not in SUPPORTED_PROVIDERS:
        detected.append(f"EXECUTOR_PROVIDER_UNSUPPORTED:{provider or 'MISSING'}")
    if transport not in SUPPORTED_TRANSPORTS:
        detected.append(f"EXECUTOR_TRANSPORT_UNSUPPORTED:{transport or 'MISSING'}")

    task_id = str(task_contract.get("task_id", "")).strip()
    if not task_id:
        detected.append("TASK_ID_MISSING")

    effect_policy, effect_failures = normalize_effect_policy(task_contract)
    detected.extend(effect_failures)

    if detected:
        return {"pass": False, "detected": detected, "dispatch_envelope": None}

    digest = sha256_json(task_contract)
    operation_key = derive_operation_key(task_id, digest, effect_policy)
    envelope = {
        "envelope_version": "2026-09-26.1",
        "task_id": task_id,
        "provider": provider,
        "transport": transport,
        "dispatch_status": "DISPATCH_READY",
        "task_contract_sha256": digest,
        "task_contract": task_contract,
        "effect_policy": effect_policy,
        "operation_key": operation_key,
        "dispatch_target_repository": (
            task_contract.get("repository")
            if (task_contract.get("executor_automation") or {}).get("target_repository_local") is True
            else None
        ),
        "dispatch_receipt": None,
        "execution_outcome": "NOT_STARTED",
        "external_executor_invocation_verified": False,
    }
    return {"pass": True, "detected": [], "dispatch_envelope": envelope}

def derive_execution_outcome(receipt: dict) -> dict:
    lifecycle = str(receipt.get("status", "")).strip().upper()
    requested = str(receipt.get("outcome_status", "")).strip().upper()
    post_condition_verified = receipt.get("post_condition_verified") is True

    if lifecycle == "ACCEPTED":
        outcome = "NOT_STARTED"
    elif lifecycle == "STARTED":
        outcome = "RUNNING"
    elif lifecycle == "COMPLETED":
        if requested in {"SUCCEEDED", "FAILED_CONFIRMED"} and post_condition_verified:
            outcome = requested
        else:
            outcome = "OUTCOME_UNKNOWN"
    else:
        outcome = "OUTCOME_UNKNOWN"

    return {
        "execution_outcome": outcome,
        "outcome_confirmed": outcome in {"SUCCEEDED", "FAILED_CONFIRMED"},
        "post_condition_verification_required": (
            lifecycle == "COMPLETED" and outcome == "OUTCOME_UNKNOWN"
        ),
        "blind_retry_permitted": False,
    }


def validate_receipt(envelope: dict, receipt: dict) -> dict:
    detected: list[str] = []
    if receipt.get("task_id") != envelope.get("task_id"):
        detected.append("DISPATCH_RECEIPT_TASK_ID_MISMATCH")
    if receipt.get("task_contract_sha256") != envelope.get("task_contract_sha256"):
        detected.append("DISPATCH_RECEIPT_CONTRACT_HASH_MISMATCH")
    if str(receipt.get("provider", "")).upper() != str(envelope.get("provider", "")).upper():
        detected.append("DISPATCH_RECEIPT_PROVIDER_MISMATCH")
    if not str(receipt.get("executor_run_id", "")).strip():
        detected.append("DISPATCH_RECEIPT_RUN_ID_MISSING")
    if str(receipt.get("status", "")).upper() not in {"ACCEPTED", "STARTED", "COMPLETED"}:
        detected.append("DISPATCH_RECEIPT_STATUS_INVALID")

    requested_outcome = str(receipt.get("outcome_status", "")).strip().upper()
    if requested_outcome and requested_outcome not in EXECUTION_OUTCOME_STATES:
        detected.append("EXECUTION_OUTCOME_STATUS_INVALID")

    effect_policy, effect_failures = normalize_effect_policy(envelope.get("task_contract") or {})
    detected.extend(effect_failures)
    if effect_policy.get("effect_class") != "READ_ONLY":
        if receipt.get("operation_key") != envelope.get("operation_key"):
            detected.append("DISPATCH_RECEIPT_OPERATION_KEY_MISMATCH")

    provider_operation_id = receipt.get("provider_operation_id")
    if provider_operation_id is not None and not str(provider_operation_id).strip():
        detected.append("PROVIDER_OPERATION_ID_INVALID")

    outcome = derive_execution_outcome(receipt)

    return {
        "pass": not detected,
        "detected": detected,
        "dispatch_verified": not detected,
        "effect_policy": effect_policy,
        "operation_key": envelope.get("operation_key"),
        "provider_operation_id": provider_operation_id,
        "reconciliation_required": outcome["execution_outcome"] == "OUTCOME_UNKNOWN",
        **outcome,
    }

def validate_retry(envelope: dict, previous_receipt: dict, retry_request: dict) -> dict:
    checked = validate_receipt(envelope, previous_receipt)
    detected = list(checked.get("detected", []))
    effect_policy = checked.get("effect_policy") or {}
    effect_class = effect_policy.get("effect_class")
    expected_key = envelope.get("operation_key")
    expected_fingerprint = effect_policy.get("request_fingerprint")

    if effect_class == "READ_ONLY":
        detected.append("SIDE_EFFECT_RETRY_CONTRACT_NOT_REQUIRED_FOR_READ_ONLY")

    if retry_request.get("operation_key") != expected_key:
        detected.append("RETRY_OPERATION_KEY_MISMATCH")
    if retry_request.get("request_fingerprint") != expected_fingerprint:
        detected.append("RETRY_REQUEST_FINGERPRINT_MISMATCH")

    retry_attempt = retry_request.get("retry_attempt")
    retry_budget = effect_policy.get("retry_budget")
    if (
        not isinstance(retry_attempt, int)
        or isinstance(retry_attempt, bool)
        or retry_attempt < 1
    ):
        detected.append("RETRY_ATTEMPT_INVALID")
    elif isinstance(retry_budget, int) and retry_attempt > retry_budget:
        detected.append("RETRY_BUDGET_EXCEEDED")

    outcome = checked.get("execution_outcome")
    if outcome == "SUCCEEDED":
        detected.append("RETRY_BLOCKED_EFFECT_ALREADY_CONFIRMED")
    elif outcome in {"NOT_STARTED", "RUNNING"}:
        detected.append("RETRY_BLOCKED_PREVIOUS_OPERATION_NOT_TERMINAL")
    elif outcome == "OUTCOME_UNKNOWN":
        reconciliation = retry_request.get("reconciliation")
        if not isinstance(reconciliation, dict) or reconciliation.get("performed") is not True:
            detected.append("RETRY_RECONCILIATION_REQUIRED")
        else:
            effect_state = str(reconciliation.get("effect_state", "")).strip().upper()
            if effect_state not in RECONCILE_EFFECT_STATES:
                detected.append("RETRY_RECONCILIATION_STATE_INVALID")
            elif effect_state == "APPLIED_CONFIRMED":
                detected.append("RETRY_BLOCKED_EFFECT_ALREADY_APPLIED")
            elif effect_state == "UNKNOWN":
                detected.append("RETRY_RECONCILIATION_INCONCLUSIVE")

            reconcile_fingerprint = reconciliation.get("request_fingerprint")
            if reconcile_fingerprint != expected_fingerprint:
                detected.append("RETRY_RECONCILIATION_FINGERPRINT_MISMATCH")

    return {
        "pass": not detected,
        "detected": detected,
        "retry_permitted": not detected,
        "operation_key": expected_key,
        "request_fingerprint": expected_fingerprint,
        "provider_operation_id": checked.get("provider_operation_id"),
        "execution_outcome": outcome,
        "retry_attempt": retry_attempt,
        "retry_budget": retry_budget,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build")
    p_build.add_argument("--task", type=Path, required=True)
    p_build.add_argument("--transport", default="FILE_QUEUE")
    p_build.add_argument("--provider", default="CODEX")
    p_build.add_argument("--output", type=Path)

    p_receipt = sub.add_parser("verify-receipt")
    p_receipt.add_argument("--envelope", type=Path, required=True)
    p_receipt.add_argument("--receipt", type=Path, required=True)

    p_retry = sub.add_parser("validate-retry")
    p_retry.add_argument("--envelope", type=Path, required=True)
    p_retry.add_argument("--receipt", type=Path, required=True)
    p_retry.add_argument("--retry-request", type=Path, required=True)

    args = ap.parse_args()

    if args.command == "build":
        task = json.loads(args.task.read_text(encoding="utf-8"))
        result = build_envelope(task, args.transport, args.provider)
        if result["pass"] and args.output:
            args.output.write_text(
                json.dumps(result["dispatch_envelope"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["pass"] else 1

    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if args.command == "verify-receipt":
        result = validate_receipt(envelope, receipt)
    else:
        retry_request = json.loads(args.retry_request.read_text(encoding="utf-8"))
        result = validate_retry(envelope, receipt, retry_request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
