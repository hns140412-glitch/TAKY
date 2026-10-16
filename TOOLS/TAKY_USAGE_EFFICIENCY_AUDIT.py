#!/usr/bin/env python3
"""TAKY offline usage-efficiency ledger from signed execution and routed receipts.

Provider CLI tokens are *observed response metadata*, not quota usage, bills,
verified task success, or causal savings. Do not use this ledger to clear HOLD.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re

from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2

HISTORY = Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")
REVIEW_ID = re.compile(r"^pf:external-review-([a-f0-9]{32}):[a-f0-9]{16}$")
MAX_HISTORY_FILES = 100
MAX_RECEIPT_BYTES = 70_000
TOKEN_NAMES = ("input_tokens", "output_tokens", "cache_creation_input_tokens",
               "cache_read_input_tokens")


def _int_count(value):
    return value if type(value) is int and 0 <= value <= 10_000_000 else None


def _signed_claude_usage(call: dict) -> dict:
    """Accept only digest-bound, successful Claude JSON and numeric usage."""
    result = call.get("result")
    if (call.get("provider") != "anthropic" or call.get("model") != "sonnet"
            or call.get("status") != "RETURNED" or
            call.get("actual_calls") != 1 or
            not isinstance(result, dict) or result.get("returncode") != 0):
        return {"state": "NO_SUCCESSFUL_CLAUDE_USAGE_ENVELOPE"}
    ensure_trusted_taky2()
    from TAKY2.enforcement import stable_hash
    if stable_hash(result) != call.get("result_digest"):
        return {"state": "RESULT_DIGEST_MISMATCH"}
    raw = result.get("stdout")
    if not isinstance(raw, str) or not 0 < len(raw) <= 600_000:
        return {"state": "CLAUDE_PAYLOAD_MISSING_OR_OVERSIZE"}
    try:
        body = json.loads(raw)
    except (ValueError, TypeError):
        return {"state": "CLAUDE_PAYLOAD_NOT_JSON"}
    if not isinstance(body, dict) or body.get("is_error") is not False or body.get("subtype") != "success":
        return {"state": "CLAUDE_RESULT_NOT_SUCCESS"}
    usage = body.get("usage")
    if not isinstance(usage, dict):
        return {"state": "CLAUDE_USAGE_FIELDS_MISSING"}
    values = {key: _int_count(usage.get(key)) for key in TOKEN_NAMES}
    if any(v is None for v in values.values()):
        return {"state": "CLAUDE_USAGE_FIELDS_MISSING_OR_INVALID"}
    estimate = body.get("total_cost_usd")
    if (type(estimate) not in (int, float) or not math.isfinite(estimate) or
            not 0 <= estimate <= 1000):
        estimate = None
    return {"state": "SIGNED_CLAUDE_PROVIDER_USAGE_OBSERVED", "tokens": values,
            "reportedTokenTotal": sum(values.values()),
            "providerListPriceEstimateUsd": round(estimate, 7) if estimate is not None else None,
            "billingChargeVerified": False}


def _history_index(history: Path) -> dict[str, dict]:
    """Read small outer receipts only; never emit prompts or provider outputs."""
    out = {}
    if not history.is_dir():
        return out
    paths = sorted(history.glob("TAKY_ROUTED_*.json"),
                   key=lambda p: p.stat().st_mtime_ns, reverse=True)[:MAX_HISTORY_FILES]
    for path in paths:
        task_id = path.stem.removeprefix("TAKY_ROUTED_")
        if not re.fullmatch(r"[a-f0-9]{32}", task_id):
            continue
        try:
            if not 0 < path.stat().st_size <= MAX_RECEIPT_BYTES:
                continue
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or data.get("task_id") != task_id:
                continue
            if data.get("executor") not in ("Claude", "Codex"):
                continue
            out[task_id] = {
                "outerStatus": data.get("state"),
                "receiptId": data.get("taky2_signed_receipt_id"),
                "qaState": data.get("content_qa_state"),
                "qualityVerifiedClaimed": data.get("content_quality_verified"),
                "elapsedSeconds": data.get("elapsed_seconds"),
            }
        except (OSError, ValueError, TypeError, UnicodeError):
            continue
    return out


def audit_runtime(runtime: dict, history_index: dict[str, dict] | None = None) -> dict:
    if not isinstance(runtime, dict):
        raise ValueError("SIGNED_RUNTIME_INVALID")
    receipts = runtime.get("preflight_receipts")
    calls = runtime.get("execution_calls")
    if not isinstance(receipts, dict) or not isinstance(calls, dict):
        raise ValueError("SIGNED_RUNTIME_CALL_REGISTRY_INVALID")
    history_index = history_index or {}
    tally = Counter()
    usage_tally = Counter()
    rows = []
    sum_list_price = 0.0
    estimated_receipts = 0
    for rid, call in calls.items():
        if not isinstance(rid, str) or not isinstance(call, dict):
            continue
        pre = receipts.get(rid)
        if not isinstance(pre, dict) or pre.get("allowed") is not True:
            tally["notBoundToAllowedPreflight"] += 1
            continue
        tally["signedExecutionClaims"] += 1
        status = str(call.get("status") or "UNKNOWN")
        tally["executionState:" + status] += 1
        provider = call.get("provider")
        if provider in ("anthropic", "openai", "local"):
            tally["provider:" + provider] += 1
        actual = _int_count(call.get("actual_calls"))
        if actual is not None and actual > 0:
            tally["claimedActualModelOrToolInvocations"] += actual
        match = REVIEW_ID.fullmatch(rid)
        if not match or pre.get("task_id") != "external-review-" + match.group(1):
            continue
        task_id = match.group(1)
        tally["boundedExternalReviewExecutionClaims"] += 1
        envelope = _signed_claude_usage(call)
        usage_tally[envelope["state"]] += 1
        meta = history_index.get(task_id, {})
        attested = meta.get("receiptId") == rid
        qa = meta.get("qaState") if attested else None
        # A returned CLI, an all-green citation screen, or an outer quality
        # flag is NOT independent verification of the substantive task.
        row = {"taskId": task_id, "signedReceiptId": rid, "provider": provider,
               "executionState": status, "claimedCalls": actual,
               "outerReceiptBound": attested,
               "outerStatus": meta.get("outerStatus") if attested else None,
               "contentQaState": qa,
               "taskOutcomeVerified": False, "reworkCountVerified": None,
               "providerUsage": envelope}
        if envelope["state"] == "SIGNED_CLAUDE_PROVIDER_USAGE_OBSERVED":
            tally["claudeTokenizedReviewCalls"] += 1
            for key, value in envelope["tokens"].items():
                usage_tally["tokens:" + key] += value
            if envelope["providerListPriceEstimateUsd"] is not None:
                sum_list_price += envelope["providerListPriceEstimateUsd"]
                estimated_receipts += 1
        rows.append(row)
    rows.sort(key=lambda x: x["taskId"])
    return {
        "schema": "TAKY_USAGE_EFFICIENCY_SIGNED_AUDIT_V1",
        "readOnly": True, "modelCallsMadeByAudit": 0,
        "networkCalls": 0, "runtimeIntegrity": "SIGNED_STATE_CALLER_MUST_VERIFY",
        "scope": "All signed execution claims; per-task detail only for bounded external reviews",
        "totals": dict(sorted(tally.items())),
        "usageEvidence": dict(sorted(usage_tally.items())),
        "listPriceEstimateUsdForObservableReviews":
            round(sum_list_price, 7) if estimated_receipts else None,
        "listPriceEstimateReceiptCount": estimated_receipts,
        "actualIncrementalBillingUsd": None,
        "actualFiveHourQuotaDelta": None,
        "verifiedSuccessfulBoundedReviews": 0,
        "verifiedSuccessfulTasksAllScopes": None,
        "verifiedReworkCount": None,
        "verifiedAvoidedModelCalls": None,
        "verifiedConsumptionSavingsPercent": None,
        "sameTaskBaselineAvailable": False,
        "reasonSavingsUnverified":
            "No controlled baseline or task-attributed before/after quota; "
            "CLI response and reported list-price are not billing or accepted work.",
        "externalReviews": rows,
    }


def audit_signed(history=HISTORY) -> dict:
    ensure_trusted_taky2()
    from TAKY2.state_store import load_bundle, RUNTIME_KEY_PATH
    if not RUNTIME_KEY_PATH.is_file():
        return {"state": "SIGNED_RUNTIME_KEY_UNAVAILABLE_HOLD", "readOnly": True}
    try:
        _, runtime, _ = load_bundle()
    except Exception as exc:
        return {"state": "SIGNED_RUNTIME_INTEGRITY_HOLD",
                "errorClass": type(exc).__name__, "readOnly": True}
    out = audit_runtime(runtime, _history_index(Path(history)))
    out["runtimeIntegrity"] = "PASS"
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", type=Path, default=HISTORY)
    ns = ap.parse_args()
    print(json.dumps(audit_signed(ns.history), ensure_ascii=False, indent=2))
