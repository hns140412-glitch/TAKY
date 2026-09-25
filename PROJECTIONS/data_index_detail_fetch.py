#!/usr/bin/env python3
"""TAKY on-demand DETAIL fetch escalation over search results.

Uses only existing CURRENT V24 DETAIL_L2-derived fixture. Does not reread RAW,
does not change rank, and does not change authority.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODE = "DETAIL_FETCH_ESCALATION_V1_EXISTING_DETAIL_ONLY"


def load_detail_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("projection_authoritative") is not False:
        raise ValueError("detail projection must be non-authoritative")
    if payload.get("raw_reread") is not False:
        raise ValueError("raw_reread must be false")
    return payload


def fetch_detail_for_results(
    search_result: dict[str, Any],
    detail_payload: dict[str, Any],
    *,
    include_related: bool = False,
    source_ids: set[str] | None = None,
) -> dict[str, Any]:
    detail_by_id = {
        r["source_id"]: r for r in detail_payload.get("records", [])
        if isinstance(r, dict) and r.get("source_id")
    }
    requested = source_ids or set()

    base_results = list(search_result.get("results") or [])
    related_results = list(search_result.get("related_results") or []) if include_related else []

    candidates = base_results + related_results
    fetched: list[dict[str, Any]] = []

    for result in candidates:
        sid = result.get("source_id")
        if not sid:
            continue
        if requested and sid not in requested:
            continue
        if result.get("detail_available") is not True:
            continue
        detail = detail_by_id.get(sid)
        if not detail:
            continue
        fetched.append({
            "source_id": sid,
            "title": detail.get("canonical_title"),
            "source_family": detail.get("source_family"),
            "source_type": detail.get("source_type"),
            "authority_class": detail.get("authority_class"),
            "current_relation": detail.get("current_relation"),
            "detail_l2": detail.get("detail_l2"),
            "projection_authoritative": False,
            "raw_read_performed": False,
        })

    out = dict(search_result)
    out["detail_fetch_mode"] = MODE
    out["detail_fetch_authoritative"] = False
    out["detail_fetch_changes_rank"] = False
    out["raw_read_performed"] = False
    out["detail_result_count"] = len(fetched)
    out["detail_results"] = fetched
    out["pipeline"] = list(search_result.get("pipeline") or []) + ["DETAIL_FETCH"]
    return out
