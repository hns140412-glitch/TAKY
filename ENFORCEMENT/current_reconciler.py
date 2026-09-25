#!/usr/bin/env python3
"""Deterministic CURRENT reconciler for TAKY Mining Engine V2.

Selection order:
1. explicit verified CURRENT pointer
2. strict state-progression dominance
3. same-state duplicate collapse
4. created/modified metadata tie-break for duplicates only
5. otherwise HOLD with a visible conflict

Filename/version labels alone never define CURRENT.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

FINGERPRINT_FIELDS = (
    "assessed_count",
    "review_required_count",
    "reviewed_through",
    "continue_from",
)


def _norm_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _norm_ts(value: Any) -> float:
    if not value:
        return 0.0
    raw = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return 0.0


def _fingerprint(candidate: dict) -> tuple:
    state = candidate.get("state_fingerprint") or {}
    return tuple(state.get(key) for key in FINGERPRINT_FIELDS)


def _progress_tuple(candidate: dict) -> tuple[int, int]:
    state = candidate.get("state_fingerprint") or {}
    assessed = state.get("assessed_count")
    review_required = state.get("review_required_count")
    if not isinstance(assessed, int) or not isinstance(review_required, int):
        return (-1, -(10**12))
    return (assessed, -review_required)


def _same_semantic_identity(candidates: list[dict]) -> bool:
    identities = {
        (candidate.get("schema"), candidate.get("semantic_role"))
        for candidate in candidates
    }
    return len(identities) <= 1


def reconcile(
    candidates: Iterable[dict],
    explicit_current_pointer: str | None = None,
) -> dict:
    items = [dict(candidate) for candidate in candidates]
    if not items:
        return {
            "status": "HOLD",
            "reason": "NO_CANDIDATES",
            "selected": None,
            "duplicates": [],
            "conflicts": [],
        }

    if not _same_semantic_identity(items):
        return {
            "status": "HOLD",
            "reason": "SEMANTIC_IDENTITY_CONFLICT",
            "selected": None,
            "duplicates": [],
            "conflicts": [candidate.get("file_id") for candidate in items],
        }

    by_id = {
        str(candidate.get("file_id")): candidate
        for candidate in items
        if candidate.get("file_id")
    }

    if explicit_current_pointer:
        pointed = by_id.get(explicit_current_pointer)
        if pointed is None:
            return {
                "status": "HOLD",
                "reason": "EXPLICIT_POINTER_NOT_FOUND",
                "selected": None,
                "duplicates": [],
                "conflicts": [explicit_current_pointer],
            }

        pointed_progress = _progress_tuple(pointed)
        dominators = [
            candidate
            for candidate in items
            if _progress_tuple(candidate) > pointed_progress
        ]
        if not dominators:
            return {
                "status": "SELECTED",
                "reason": "EXPLICIT_VERIFIED_POINTER",
                "selected": pointed,
                "duplicates": [
                    candidate
                    for candidate in items
                    if candidate.get("file_id") != pointed.get("file_id")
                    and _fingerprint(candidate) == _fingerprint(pointed)
                ],
                "conflicts": [],
            }

        # Verified strict progression may supersede a stale explicit pointer.
        items = dominators + [pointed]

    best_progress = max(_progress_tuple(candidate) for candidate in items)
    progressed = [
        candidate
        for candidate in items
        if _progress_tuple(candidate) == best_progress
    ]

    fingerprint_groups: dict[tuple, list[dict]] = {}
    for candidate in progressed:
        fingerprint_groups.setdefault(_fingerprint(candidate), []).append(candidate)

    if len(fingerprint_groups) > 1:
        return {
            "status": "HOLD",
            "reason": "STATE_FINGERPRINT_CONFLICT",
            "selected": None,
            "duplicates": [],
            "conflicts": [candidate.get("file_id") for candidate in progressed],
        }

    same_state = next(iter(fingerprint_groups.values()))
    selected = max(
        same_state,
        key=lambda candidate: (
            _norm_ts(candidate.get("modified_time")),
            _norm_ts(candidate.get("created_time")),
            _norm_text(candidate.get("file_id")),
        ),
    )
    duplicates = [
        candidate
        for candidate in same_state
        if candidate.get("file_id") != selected.get("file_id")
    ]

    if len(items) > len(same_state):
        reason = "STATE_PROGRESSION_DOMINANCE"
    elif duplicates:
        reason = "DUPLICATE_COLLAPSE_METADATA_TIEBREAK"
    else:
        reason = "SINGLE_CANDIDATE"

    return {
        "status": "SELECTED",
        "reason": reason,
        "selected": selected,
        "duplicates": duplicates,
        "conflicts": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = reconcile(
        payload.get("candidates", []),
        explicit_current_pointer=payload.get("explicit_current_pointer"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "SELECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
