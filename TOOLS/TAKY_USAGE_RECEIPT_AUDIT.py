#!/usr/bin/env python3
"""Read-only, bounded receipt audit for TAKY's existing usage board.

An executor exit, a cached quota snapshot, and a provider's real consumption
are different evidence. This module never claims saved credits or success
without a separately verified outcome. Does not call models or network.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import time
from pathlib import Path

DEFAULT_HISTORY = Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")
FAMILIES = ("TAKY_ROUTED_", "CODEX_CHAT_")
MAX_FILES = 100
MAX_RECEIPT_BYTES = 32_000


def timestamp(value):
    if not isinstance(value, str) or len(value) > 80:
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except ValueError:
        return None


def metric(value):
    try:
        if isinstance(value, bool):
            return None
        number = float(value)
        return round(number, 2) if 0 <= number <= 100 else None
    except (TypeError, ValueError, OverflowError):
        return None


def quota_pair(row):
    """Unattributed observation only, never a usage-saving estimate."""
    before = row.get("quota_before")
    after = row.get("quota_after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {"status": "QUOTA_VALUES_MISSING"}
    t0 = timestamp(row.get("quota_before_observed_at"))
    t1 = timestamp(row.get("quota_after_observed_at"))
    if not t0 or not t1:
        return {"status": "QUOTA_TIMESTAMPS_MISSING"}
    if t0 >= t1:
        return {"status": "SAME_OR_REVERSED_CACHED_SNAPSHOT"}
    started = timestamp(row.get("started_utc") or row.get("created_utc"))
    finished = timestamp(row.get("finished_utc"))
    if not started or not finished or t0 > started or t1 < finished or finished < started:
        return {"status": "QUOTA_NOT_BRACKETING_EXECUTION"}
    delta = {}
    for period in ("fiveHour", "week"):
        previous, current = metric(before.get(period)), metric(after.get(period))
        if previous is not None and current is not None:
            delta[period] = round(current - previous, 2)
    if not delta:
        return {"status": "QUOTA_VALUES_MISSING"}
    return {
        "status": "OBSERVED_DIFFERENCE_NOT_TASK_ATTRIBUTED",
        "observedDeltaPercentagePoints": delta,
        "periodResetAndConcurrentUsageNotVerified": True,
        "causalSavingsClaimAllowed": False,
    }


def audited_receipt(path, family):
    try:
        if not path.is_file() or path.stat().st_size > MAX_RECEIPT_BYTES:
            return None
        if path.stat().st_size == 0 and family == "TAKY_ROUTED_":
            ident = path.name.removeprefix(family).removesuffix(".json")
            if (len(ident) != 32 or any(c not in "0123456789abcdef" for c in ident.lower())
                    or path.name != family + ident + ".json"):
                return None
            age = max(0, time.time() - path.stat().st_mtime)
            return {"receipt": path.name, "executor": "UNCONFIRMED",
                    "outcome": ("STALE_UNFINALIZED_RESERVATION" if age >= 240
                                else "RESERVED_NO_FINAL_RECEIPT"),
                    "quota": {"status": "NO_RECEIPT_QUOTA_VALUES"},
                    "modelCallConfirmed": False}
        row = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(row, dict):
            return None
        ident = str(row.get("task_id") or row.get("id") or "")
        if (len(ident) != 32 or any(c not in "0123456789abcdef" for c in ident.lower())
                or path.name != family + ident + ".json"):
            return None
        if str(row.get("executor") or "") not in ("Claude", "Codex"):
            return None
        state = row.get("state") if family == "TAKY_ROUTED_" else row.get("status")
        if state not in ("STARTED", "FAILED", "ERROR", "OUTCOME_UNKNOWN", "COMPLETE_UNVERIFIED"):
            return None
        return {"receipt": path.name, "executor": row["executor"],
                "outcome": state, "quota": quota_pair(row)}
    except (OSError, ValueError, UnicodeError, TypeError):
        return None


def audit(history=DEFAULT_HISTORY, limit=MAX_FILES):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_FILES:
        raise ValueError("RECEIPT_AUDIT_LIMIT_INVALID")
    folder = Path(history)
    paths = []
    if folder.is_dir():
        for family in FAMILIES:
            for p in folder.glob(family + "*.json"):
                if p.is_file():
                    try:
                        paths.append((p.stat().st_mtime_ns, p, family))
                    except OSError:
                        pass
    paths.sort(key=lambda r: r[0], reverse=True)
    rows, invalid = [], 0
    for _, path, family in paths[:limit]:
        item = audited_receipt(path, family)
        if item is None:
            invalid += 1
        else:
            rows.append(item)
    outcomes = {s: sum(r["outcome"] == s for r in rows)
                for s in ("STARTED", "FAILED", "ERROR", "OUTCOME_UNKNOWN", "COMPLETE_UNVERIFIED",
                          "RESERVED_NO_FINAL_RECEIPT", "STALE_UNFINALIZED_RESERVATION")}
    quotas = {}
    for r in rows:
        state = r["quota"]["status"]
        quotas[state] = quotas.get(state, 0) + 1
    return {"schema": "TAKY_EXECUTION_RECEIPT_AUDIT_V1",
            "readOnly": True, "networkCalls": 0, "modelCalls": 0,
            "scanned": min(len(paths), limit), "validReceipts": len(rows),
            "invalidReceipts": invalid, "outcomes": outcomes,
            "quotaEvidenceStates": quotas,
            "verifiedSuccessfulOutcomes": 0,
            "verifiedCreditSavingsPercent": None,
            "verifiedTaskAttribution": False,
            "samples": rows[:10]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    p.add_argument("--limit", type=int, default=MAX_FILES)
    a = p.parse_args()
    print(json.dumps(audit(a.history, a.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
