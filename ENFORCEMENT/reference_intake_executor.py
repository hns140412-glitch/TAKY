#!/usr/bin/env python3
"""Controlled executor for reference-intake lifecycle persistence.

This module intentionally does not perform arbitrary network fetching. It
executes the durable handoff after a Mining/acquisition adapter has produced an
explicit acquisition result. Unknown or missing acquisition state fails closed.

Lifecycle is append-only:
REGISTERED -> INDEXED -> EVIDENCE_CANDIDATE -> terminal/review disposition.
PROMOTED is never emitted automatically by this executor.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ACQUISITION_STATES = {
    "ACQUIRED_AND_PRESERVED",
    "ACCESSIBLE_REMOTE_SOURCE",
    "RESOURCE_PAGE_VERIFIED__BINARY_URL_UNRESOLVED",
    "ACCESS_RESTRICTED",
    "HOLD",
}
DISPOSITIONS = {
    "REGISTERED",
    "INDEXED",
    "EVIDENCE_CANDIDATE",
    "REJECTED",
    "SUPERSEDED",
    "NEEDS_MORE_EVIDENCE",
    "HOLD",
}
LEDGER_RELATIVE_PATH = Path("CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json")


def _clean(value: object) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema": "TAKY_REFERENCE_INTAKE_DISPOSITION_LEDGER_V1",
            "append_only": True,
            "entries": [],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "TAKY_REFERENCE_INTAKE_DISPOSITION_LEDGER_V1":
        raise ValueError("INVALID_REFERENCE_INTAKE_LEDGER_SCHEMA")
    if data.get("append_only") is not True:
        raise ValueError("REFERENCE_INTAKE_LEDGER_MUST_BE_APPEND_ONLY")
    if not isinstance(data.get("entries"), list):
        raise ValueError("REFERENCE_INTAKE_LEDGER_ENTRIES_INVALID")
    return data


def _source_key(record: dict[str, Any]) -> str:
    return (
        _clean(record.get("source_id"))
        or _clean(record.get("source_url"))
        or _clean(record.get("source_locator"))
    )


def _event_id(source_key: str, state: str, at: str, ordinal: int) -> str:
    raw = f"{source_key}|{state}|{at}|{ordinal}".encode("utf-8")
    return "ri-" + hashlib.sha256(raw).hexdigest()[:20]


def _append(
    ledger: dict[str, Any],
    *,
    source_key: str,
    state: str,
    acquisition_state: str,
    at: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if state not in DISPOSITIONS:
        raise ValueError(f"INVALID_DISPOSITION:{state}")
    previous = None
    for item in reversed(ledger["entries"]):
        if item.get("source_key") == source_key:
            previous = item.get("state")
            break
    entry = {
        "event_id": _event_id(source_key, state, at, len(ledger["entries"])),
        "source_key": source_key,
        "state": state,
        "previous_state": previous,
        "acquisition_state": acquisition_state,
        "recorded_at": at,
        "details": details or {},
    }
    ledger["entries"].append(entry)
    return entry


def execute(
    record: dict[str, Any],
    route_result: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    if route_result.get("pass") is not True or route_result.get("route_type") != "REFERENCE_INTAKE_REVIEW":
        return {"pass": False, "detected": ["REFERENCE_INTAKE_ROUTE_REQUIRED"]}

    source_key = _source_key(record)
    if not source_key:
        return {"pass": False, "detected": ["REFERENCE_SOURCE_KEY_MISSING"]}

    execution = record.get("reference_intake_execution")
    if not isinstance(execution, dict):
        return {
            "pass": False,
            "detected": ["REFERENCE_INTAKE_EXECUTION_PAYLOAD_MISSING"],
            "next_handoff": "MINING_ACQUISITION_REQUIRED",
        }

    acquisition_state = _clean(execution.get("acquisition_state")).upper()
    if acquisition_state not in ACQUISITION_STATES:
        return {
            "pass": False,
            "detected": ["REFERENCE_ACQUISITION_STATE_INVALID"],
            "next_handoff": "MINING_ACQUISITION_REQUIRED",
        }

    if execution.get("requested_disposition") == "PROMOTED":
        return {
            "pass": False,
            "detected": ["REFERENCE_AUTO_PROMOTION_FORBIDDEN"],
            "next_handoff": "HUMAN_OR_DOMAIN_PROMOTION_REVIEW",
        }

    ledger_path = repo_root / LEDGER_RELATIVE_PATH
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = _load_ledger(ledger_path)
    at = _clean(execution.get("recorded_at")) or _now()
    emitted: list[dict[str, Any]] = []

    emitted.append(_append(
        ledger,
        source_key=source_key,
        state="REGISTERED",
        acquisition_state=acquisition_state,
        at=at,
        details={
            "source_id": record.get("source_id"),
            "source_url": record.get("source_url"),
            "source_locator": record.get("source_locator"),
            "domain": route_result.get("domain"),
            "consumer": route_result.get("consumer"),
        },
    ))

    if acquisition_state in {"ACCESS_RESTRICTED", "HOLD"}:
        emitted.append(_append(
            ledger,
            source_key=source_key,
            state="HOLD",
            acquisition_state=acquisition_state,
            at=at,
            details={"reason": execution.get("reason") or acquisition_state},
        ))
        ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "pass": True,
            "execution_status": "PERSISTED_HOLD",
            "emitted": emitted,
            "ledger_path": str(LEDGER_RELATIVE_PATH),
            "next_handoff": "WAIT_FOR_NEW_ACCESS_EVIDENCE",
            "canonical_promotion": False,
        }

    if acquisition_state == "RESOURCE_PAGE_VERIFIED__BINARY_URL_UNRESOLVED":
        emitted.append(_append(
            ledger,
            source_key=source_key,
            state="NEEDS_MORE_EVIDENCE",
            acquisition_state=acquisition_state,
            at=at,
            details={"reason": execution.get("reason") or "BINARY_URL_UNRESOLVED"},
        ))
        ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "pass": True,
            "execution_status": "PERSISTED_NEEDS_MORE_EVIDENCE",
            "emitted": emitted,
            "ledger_path": str(LEDGER_RELATIVE_PATH),
            "next_handoff": "MINING_ACQUISITION_REQUIRED",
            "canonical_promotion": False,
        }

    index_result = execution.get("index_result")
    indexed = isinstance(index_result, dict) and index_result.get("verified") is True
    if not indexed:
        ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "pass": True,
            "execution_status": "REGISTERED_AWAITING_INDEX",
            "emitted": emitted,
            "ledger_path": str(LEDGER_RELATIVE_PATH),
            "next_handoff": "INDEX_EXISTENCE_DUPLICATE_VERSION_CHECK",
            "canonical_promotion": False,
        }

    emitted.append(_append(
        ledger,
        source_key=source_key,
        state="INDEXED",
        acquisition_state=acquisition_state,
        at=at,
        details={
            "index_source_id": index_result.get("source_id") or record.get("source_id"),
            "index_version": index_result.get("index_version"),
            "duplicate_relation": index_result.get("duplicate_relation"),
            "version_relation": index_result.get("version_relation"),
            "source_ref": index_result.get("source_ref"),
        },
    ))

    requested = _clean(execution.get("requested_disposition")).upper()
    if requested in {"REJECTED", "SUPERSEDED", "NEEDS_MORE_EVIDENCE", "HOLD"}:
        reason = _clean(execution.get("reason"))
        if not reason:
            return {"pass": False, "detected": ["DISPOSITION_REASON_REQUIRED"]}
        emitted.append(_append(
            ledger,
            source_key=source_key,
            state=requested,
            acquisition_state=acquisition_state,
            at=at,
            details={"reason": reason},
        ))
        next_handoff = "STOP_OR_REOPEN_ON_NEW_EVIDENCE"
    else:
        emitted.append(_append(
            ledger,
            source_key=source_key,
            state="EVIDENCE_CANDIDATE",
            acquisition_state=acquisition_state,
            at=at,
            details={
                "consumer": route_result.get("consumer"),
                "domain": route_result.get("domain"),
                "source_ref": index_result.get("source_ref"),
            },
        ))
        next_handoff = "DOMAIN_CONSUMER_REQUERY"

    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "pass": True,
        "execution_status": "PERSISTED",
        "emitted": emitted,
        "ledger_path": str(LEDGER_RELATIVE_PATH),
        "next_handoff": next_handoff,
        "canonical_promotion": False,
    }
