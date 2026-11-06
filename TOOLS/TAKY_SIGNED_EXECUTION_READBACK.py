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
import hashlib
from pathlib import Path

ORCH = Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                  separators=(",", ":")).encode("utf-8")).hexdigest()[:20]




def _verified_execution_evidence(runtime: dict, receipt_id: str,
                                 preflight: dict, call: dict) -> bool:
    """Verify a sealed TAKY2 execution verification claim, not user DONE.

    Called only on data obtained via trusted HMAC/anchor load_bundle(), or in
    explicit unit tests with fixture dictionaries. Never trust a WORKBENCH
    `execution_verified` boolean, model prose, or CLI exit code by itself.
    """
    completion = runtime.get("completion_registry", {}).get(receipt_id)
    if not isinstance(completion, dict):
        return False
    if runtime.get("execution_outcomes", {}).get(receipt_id) != "SUCCESS":
        return False
    if any(not isinstance(preflight.get(k), str) or
           not preflight.get(k) or completion.get(k) != preflight[k]
           for k in ("plan_digest", "action_digest", "call_digest", "authority_digest")):
        return False
    if (completion.get("key_match") is not True
            or completion.get("critical_gaps") != []
            or not isinstance(completion.get("verified_by"), str)
            or not completion["verified_by"].strip()
            or completion["verified_by"] == call.get("executor_id")):
        return False
    required, passed = completion.get("required_verifications"), completion.get("passed_verifications")
    if (not isinstance(required, list) or not required
            or not isinstance(passed, list)
            or not all(isinstance(x, str) for x in required + passed)
            or not set(required).issubset(set(passed))
            or not {"technical", "intent"}.issubset(set(passed))):
        return False
    refs, registry = completion.get("evidence_refs"), runtime.get("evidence_registry")
    if (not isinstance(refs, list) or not 1 <= len(refs) <= 20
            or not all(isinstance(ref, str) and ref for ref in refs)
            or len(set(refs)) != len(refs) or not isinstance(registry, dict)):
        return False
    for ref in refs:
        evidence = registry.get(ref)
        if not isinstance(evidence, dict):
            return False
        if not (
            evidence.get("verified") is True
            and evidence.get("acceptance_state") == "ACCEPTED"
            and evidence.get("receipt_id") == receipt_id
            and evidence.get("authority_digest_or_key_version") == preflight.get("authority_digest")
        ):
            return False
        is_independent = ("independent" in required
                          and ref == completion.get("independent_review_ref"))
        if is_independent:
            independent_evidence = runtime.get("independent_review_registry", {}).get(ref)
            if (not isinstance(independent_evidence, dict)
                    or evidence.get("result_digest") != call.get("result_digest")
                    or evidence.get("revision_or_hash") != independent_evidence.get("review_digest")
                    or evidence.get("validator") != independent_evidence.get("bridge_id")):
                return False
        elif (evidence.get("revision_or_hash") != call.get("result_digest")
              or evidence.get("validator") != completion.get("verified_by")):
            return False
    if "independent" in required:
        ref = completion.get("independent_review_ref")
        independent = runtime.get("independent_review_registry", {}).get(ref)
        if (ref not in refs or not isinstance(independent, dict)
                or independent.get("receipt_id") != receipt_id
                or independent.get("acceptance_state") != "ACCEPTED"
                or independent.get("target_result_digest") != call.get("result_digest")
                or independent.get("authority_digest") != preflight.get("authority_digest")
                or independent.get("reviewer_role") != completion.get("independent_reviewer_role")
                or independent.get("reviewer_actor") != completion.get("independent_reviewer_actor")
                or independent.get("reviewer_id") in {call.get("executor_id"), completion.get("verified_by")}):
            return False
    return True


def correlate(task_id: str, runtime: dict, expected_receipt_id: str | None = None,
              expected_call_manifest: dict | None = None):
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
    if expected_call_manifest is not None:
        if not isinstance(expected_call_manifest, dict) or (
                _digest(expected_call_manifest) != preflight.get("call_digest")):
            output["state"] = "SIGNED_CALL_MANIFEST_MISMATCH_HOLD"
            return output
        output["signedCallManifestBound"] = True
    state = str(call.get("status", ""))
    result = call.get("result")
    if isinstance(result, dict) and call.get("result_digest") != _digest(result):
        output["state"] = "SIGNED_RETURN_DIGEST_MISMATCH_HOLD"
        return output
    exit_code = result.get("returncode") if isinstance(result, dict) else None
    output.update({"executionLedgerState": state, "model": call.get("model"),
                   "provider": call.get("provider"),
                   "cliExitCode": exit_code if isinstance(exit_code, int) else None,
                   "resultDigest": call.get("result_digest"),
                   "outputObserved": bool(result.get("stdout")) if isinstance(result, dict) else False})
    if state == "RETURNED" and exit_code == 0:
        output["state"] = "CLI_RETURNED_UNVERIFIED"
        verified = _verified_execution_evidence(runtime, receipt_id, preflight, call)
        output["executionEvidenceVerified"] = verified
        output["executionVerificationState"] = (
            "SIGNED_EXECUTION_EVIDENCED_NOT_USER_DONE" if verified
            else "NO_BOUND_COMPLETION_EVIDENCE"
        )
    elif state in ("CALLING", "OUTCOME_UNKNOWN", "UNCERTAIN"):
        output["state"] = "EXECUTION_OUTCOME_UNKNOWN_NO_RETRY"
    elif state in ("FAILED", "ERROR"):
        output["state"] = "EXECUTION_FAILED"
    else:
        output["state"] = "EXECUTION_UNRESOLVED_NO_RETRY"
    return output


def read_signed(task_id: str, expected_receipt_id: str | None = None,
                expected_call_manifest: dict | None = None):
    if not (ORCH / "TAKY2" / "state" / "runtime.json").is_file():
        return {"state": "SIGNED_RUNTIME_UNAVAILABLE"}
    try:
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.state_store import load_bundle, RUNTIME_KEY_PATH
        if not RUNTIME_KEY_PATH.is_file():
            return {"state": "SIGNED_RUNTIME_KEY_MISSING_NO_REPAIR"}
        _, runtime, _ = load_bundle()
        return correlate(task_id, runtime, expected_receipt_id, expected_call_manifest)
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
