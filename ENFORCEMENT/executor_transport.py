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

def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_json(value: dict) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

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

    if detected:
        return {"pass": False, "detected": detected, "dispatch_envelope": None}

    digest = sha256_json(task_contract)
    envelope = {
        "envelope_version": "2026-09-19.1",
        "task_id": task_id,
        "provider": provider,
        "transport": transport,
        "dispatch_status": "DISPATCH_READY",
        "task_contract_sha256": digest,
        "task_contract": task_contract,
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

    outcome = derive_execution_outcome(receipt)

    return {
        "pass": not detected,
        "detected": detected,
        "dispatch_verified": not detected,
        **outcome,
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
    result = validate_receipt(envelope, receipt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
