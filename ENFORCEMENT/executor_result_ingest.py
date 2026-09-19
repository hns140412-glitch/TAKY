#!/usr/bin/env python3
"""Validate executor-return evidence against the dispatched task envelope."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from executor_transport import sha256_json

def ingest(envelope: dict, result: dict) -> dict:
    detected: list[str] = []
    task = envelope.get("task_contract")
    if not isinstance(task, dict):
        return {"pass": False, "detected": ["DISPATCH_TASK_CONTRACT_MISSING"]}

    expected_hash = envelope.get("task_contract_sha256")
    actual_hash = sha256_json(task)
    if expected_hash != actual_hash:
        detected.append("DISPATCH_ENVELOPE_TAMPERED")

    if result.get("task_id") != envelope.get("task_id"):
        detected.append("EXECUTOR_RESULT_TASK_ID_MISMATCH")

    if result.get("task_contract_sha256") != expected_hash:
        detected.append("EXECUTOR_RESULT_CONTRACT_HASH_MISMATCH")

    provider = str(result.get("provider", "")).upper()
    if provider != str(envelope.get("provider", "")).upper():
        detected.append("EXECUTOR_RESULT_PROVIDER_MISMATCH")

    report = result.get("completion_report")
    if not isinstance(report, dict):
        detected.append("EXECUTOR_COMPLETION_REPORT_MISSING")
    elif report.get("task_id") != envelope.get("task_id"):
        detected.append("EXECUTOR_COMPLETION_REPORT_TASK_ID_MISMATCH")

    return {
        "pass": not detected,
        "detected": detected,
        "task_contract": task if not detected else None,
        "completion_report": report if not detected else None,
        "transport_claim": (
            "RESULT_INTEGRITY_BOUND"
            if not detected else "RESULT_REJECTED"
        ),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelope", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()

    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    out = ingest(envelope, result)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
