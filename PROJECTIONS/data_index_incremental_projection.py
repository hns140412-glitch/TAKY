#!/usr/bin/env python3
"""TAKY incremental search-projection operations.

Applies normalized INDEX_L1 deltas to a derived search projection only.
Never mutates CURRENT, never rereads RAW, never performs full reindex.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

MODE = "INCREMENTAL_PROJECTION_V1"

ALLOWED_FIELDS = {
    "source_id","canonical_title","source_family","source_type","authority_class",
    "domain_facets","controlled_terms","keywords","entities","short_summary",
    "detail_terms","index_state","review_state","current_relation","detail_available"
}

FORBIDDEN_DECISION_FIELDS = {
    "value_statement","function_ids","runtime_connection_state",
    "utilization_class","owner","consumers"
}


def _validate_record(record: dict[str, Any]) -> None:
    if not record.get("source_id"):
        raise ValueError("source_id is required")
    leaked = FORBIDDEN_DECISION_FIELDS.intersection(record)
    if leaked:
        raise ValueError(f"decision fields are forbidden in projection delta: {sorted(leaked)}")
    unknown = set(record) - ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"unknown projection fields: {sorted(unknown)}")


def apply_incremental_projection_delta(
    records: list[dict[str, Any]],
    *,
    upserts: list[dict[str, Any]] | None = None,
    tombstone_source_ids: set[str] | None = None,
    upstream_authority_changed: bool = False,
) -> dict[str, Any]:
    upserts = upserts or []
    tombstone_source_ids = tombstone_source_ids or set()

    by_id = {r["source_id"]: deepcopy(r) for r in records}
    if len(by_id) != len(records):
        raise ValueError("existing projection contains duplicate source_id")

    affected: set[str] = set()
    scopes: set[str] = set()

    for record in upserts:
        _validate_record(record)
        sid = record["source_id"]
        previous = by_id.get(sid)
        by_id[sid] = deepcopy(record)
        if previous != record:
            affected.add(sid)
            scopes.add("SEMANTIC_RETRIEVAL")
            if previous is None or previous.get("source_family") != record.get("source_family"):
                scopes.add("STRUCTURED_AND_LEXICAL_RETRIEVAL")
            if previous is None or previous.get("detail_available") != record.get("detail_available"):
                scopes.add("DETAIL_FETCH_INDEX")

    for sid in sorted(tombstone_source_ids):
        if sid in by_id:
            del by_id[sid]
            affected.add(sid)
            scopes.update({"STRUCTURED_AND_LEXICAL_RETRIEVAL","SEMANTIC_RETRIEVAL","DETAIL_FETCH_INDEX"})

    updated = [by_id[sid] for sid in sorted(by_id)]

    return {
        "projection_authoritative": False,
        "mode": MODE,
        "full_reindex_performed": False,
        "raw_reread_performed": False,
        "current_pointer_mutated": False,
        "promotion_performed": False,
        "promotion_decision_required": bool(upstream_authority_changed and affected),
        "before_count": len(records),
        "after_count": len(updated),
        "affected_count": len(affected),
        "affected_source_ids": sorted(affected),
        "affected_projection_scopes": sorted(scopes),
        "records": updated,
    }
