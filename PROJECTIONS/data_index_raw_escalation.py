#!/usr/bin/env python3
"""TAKY guarded RAW escalation candidate selector.

This module NEVER fetches RAW. It only emits evidence-backed candidates after
hybrid -> relation -> detail escalation has been exhausted.
"""
from __future__ import annotations

from typing import Any

MODE = "RAW_ESCALATION_CANDIDATE_V1__NO_FETCH"

HELD_OVERSIZE_IDS = {
    "1bnDccQ1aDJf5Y7bDiA-9kUJ0LZ-c-sYy",
    "114osqcmcJAaVDecmpkneNdCgcD4JRRto",
}

ALLOWED_REASONS = {
    "RESULT_RELEVANT_BUT_DETAIL_UNAVAILABLE",
    "DETAIL_PRESENT_BUT_INSUFFICIENT_FOR_REQUEST",
    "STALE_OR_CONFLICT_REVALIDATION_REQUIRED",
}


def select_raw_candidates(
    search_result: dict[str, Any],
    *,
    unresolved_source_ids: set[str] | None = None,
    insufficient_detail_source_ids: set[str] | None = None,
    revalidation_source_ids: set[str] | None = None,
    allow_oversize_with_new_access_path: bool = False,
) -> dict[str, Any]:
    unresolved_source_ids = unresolved_source_ids or set()
    insufficient_detail_source_ids = insufficient_detail_source_ids or set()
    revalidation_source_ids = revalidation_source_ids or set()

    by_id: dict[str, dict[str, Any]] = {}
    for row in list(search_result.get("results") or []) + list(search_result.get("related_results") or []):
        sid = row.get("source_id")
        if sid and sid not in by_id:
            by_id[sid] = row

    candidates: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    requested = (
        unresolved_source_ids
        | insufficient_detail_source_ids
        | revalidation_source_ids
    )

    for sid in sorted(requested):
        row = by_id.get(sid)
        if not row:
            continue

        reasons: list[str] = []
        if sid in unresolved_source_ids and row.get("detail_available") is not True:
            reasons.append("RESULT_RELEVANT_BUT_DETAIL_UNAVAILABLE")
        if sid in insufficient_detail_source_ids and row.get("detail_available") is True:
            reasons.append("DETAIL_PRESENT_BUT_INSUFFICIENT_FOR_REQUEST")
        if sid in revalidation_source_ids:
            reasons.append("STALE_OR_CONFLICT_REVALIDATION_REQUIRED")

        if not reasons:
            continue

        if sid in HELD_OVERSIZE_IDS and not allow_oversize_with_new_access_path:
            blocked.append({
                "source_id": sid,
                "title": row.get("title"),
                "blocked_reason": "OVERSIZE_HOLD_REQUIRES_NEW_ACCESS_PATH",
                "raw_fetch_performed": False,
            })
            continue

        candidates.append({
            "source_id": sid,
            "title": row.get("title"),
            "source_family": row.get("source_family"),
            "authority_class": row.get("authority_class"),
            "current_relation": row.get("current_relation"),
            "reasons": sorted(set(reasons)),
            "raw_fetch_performed": False,
            "projection_authoritative": False,
        })

    return {
        "projection_authoritative": False,
        "raw_escalation_mode": MODE,
        "automatic_raw_reread": False,
        "raw_fetch_performed": False,
        "candidate_count": len(candidates),
        "blocked_count": len(blocked),
        "raw_fetch_candidates": candidates,
        "blocked_candidates": blocked,
        "pipeline": list(search_result.get("pipeline") or []) + ["RAW_FETCH_CANDIDATE_GATE"],
    }
