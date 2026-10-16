#!/usr/bin/env python3
"""Read-only TAKY2 signed-runtime receipt correlation by original task ID.

CLI success is not proof of model quality, economic savings, or acceptance.
Reads only existing TAKY2 signed runtime; never sends prompts, starts CLIs,
changes receipts, or retries any unknown work.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ORCH = Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")


def correlate(task_id: str, runtime: dict, expected_receipt_id: str | None = None):
    if not isinstance(task_id, str) or not re.fullmatch(r"[a-f0-9]{32}", task_id):
        raise ValueError("INVALID_TASK_ID")
    prefix = "pf:external-review-" + task_id + ":"
    receipts = runtime.get("preflight_receipts", {})
    calls = runtime.get("execution_calls", {})
    if not isinstance(receipts, dict) or not isinstance(calls, dict):
        return {"state": "INVALID_SIGNED_RUNTIME_RECORD"}
    matches = [(key, value) for key, value in receipts.items()
               if key.startswith(prefix) and isinstance(value, dict)
               and value.get("task_id") == "external-review-" + task_id]
    if len(matches) == 0:
        return {"state": "SIGNED_PREFLIGHT_NOT_FOUND", "modelSuccessVerified": False}
    if len(matches) != 1:
        return {"state": "MULTIPLE_PREFLIGHTS_HOLD_NO_RETRY", "attemptCount": len(matches),
                "modelSuccessVerified": False}
    receipt_id, preflight = matches[0]
    if expected_receipt_id is not None and receipt_id != expected_receipt_id:
        return {"state": "RECEIPT_ID_MISMATCH_HOLD", "modelSuccessVerified": False}
    call = calls.get(receipt_id)
    output = {"state": "PREFLIGHT_ONLY", "receiptId": receipt_id,
              "preflightAllowed": preflight.get("allowed") is True,
              "callAllowed": preflight.get("call_allowed") is True,
              "modelSuccessVerified": False,
              "creditSavingsMeasured": False}
    if not isinstance(call, dict):
        prior_outcome = runtime.get("execution_outcomes", {}).get(receipt_id)
        if prior_outcome == "PREINVOKE_RELEASED":
            output["state"] = "PREINVOKE_RELEASED"
        elif prior_outcome is not None:
            output["state"] = "PREFLIGHT_TERMINAL_WITHOUT_CALL"
        return output
    state = str(call.get("status", ""))
    result = call.get("result")
    exit_code = result.get("returncode") if isinstance(result, dict) else None
    output.update({"executionLedgerState": state, "model": call.get("model"),
                   "provider": call.get("provider"),
                   "cliExitCode": exit_code if isinstance(exit_code, int) else None,
                   "resultDigest": call.get("result_digest"),
                   "outputObserved": bool(result.get("stdout")) if isinstance(result, dict) else False})
    if state == "RETURNED" and exit_code == 0:
        output["state"] = "CLI_RETURNED_UNVERIFIED"
    elif state in ("CALLING", "OUTCOME_UNKNOWN", "UNCERTAIN"):
        output["state"] = "EXECUTION_OUTCOME_UNKNOWN_NO_RETRY"
    elif state in ("FAILED", "ERROR"):
        output["state"] = "EXECUTION_FAILED"
    else:
        output["state"] = "EXECUTION_UNRESOLVED_NO_RETRY"
    return output


def read_signed(task_id: str, expected_receipt_id: str | None = None):
    if not (ORCH / "TAKY2" / "state" / "runtime.json").is_file():
        return {"state": "SIGNED_RUNTIME_UNAVAILABLE"}
    try:
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.state_store import load_bundle, RUNTIME_KEY_PATH
        if not RUNTIME_KEY_PATH.is_file():
            return {"state": "SIGNED_RUNTIME_KEY_MISSING_NO_REPAIR"}
        _, runtime, _ = load_bundle()
        return correlate(task_id, runtime, expected_receipt_id)
    except Exception as exc:
        return {"state": "SIGNED_RUNTIME_VERIFY_FAILED",
                "reasonClass": type(exc).__name__,
                "modelSuccessVerified": False}


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("--task-id", required=True)
    a.add_argument("--receipt-id")
    opts = a.parse_args()
    print(json.dumps(read_signed(opts.task_id, opts.receipt_id), ensure_ascii=False, indent=2))
