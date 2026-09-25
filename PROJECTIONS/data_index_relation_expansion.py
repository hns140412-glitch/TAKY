#!/usr/bin/env python3
"""TAKY relation expansion over D5 results.

Only explicit evidence-backed relation edges are followed. D5 ranked results
remain unchanged; related results are returned separately and are
non-authoritative.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_index_hybrid_search import hybrid_search
from data_index_semantic_projection import apply_filters

MODE = "RELATION_EXPANSION_V1_EXPLICIT_ONLY"
ALLOWED_RELATIONS = {"EXACT_DUPLICATE_OF"}


def load_relations(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("projection_authoritative") is not False:
        raise ValueError("relation projection must be non-authoritative")
    if payload.get("inferred_relations") is not False:
        raise ValueError("inferred relations are forbidden in this slice")
    bad = [
        e for e in payload.get("edges", [])
        if e.get("type") not in ALLOWED_RELATIONS
    ]
    if bad:
        raise ValueError(f"unsupported relation types: {sorted({e.get('type') for e in bad})}")
    return payload


def expand_relations(
    base_result: dict[str, Any],
    records: list[dict[str, Any]],
    relation_payload: dict[str, Any],
    *,
    per_seed: int = 3,
) -> dict[str, Any]:
    by_id = {r["source_id"]: r for r in records}
    filters = base_result.get("filters") or {}
    adjacency: dict[str, list[dict[str, Any]]] = {}
    for edge in relation_payload.get("edges", []):
        adjacency.setdefault(edge["from"], []).append(edge)

    base_ids = {r["source_id"] for r in base_result.get("results", [])}
    related: list[dict[str, Any]] = []
    seen: set[str] = set()

    for seed_rank, seed in enumerate(base_result.get("results", []), start=1):
        seed_id = seed["source_id"]
        emitted = 0
        for edge in adjacency.get(seed_id, []):
            if emitted >= per_seed:
                break
            target_id = edge["to"]
            if target_id in base_ids or target_id in seen:
                continue
            target = by_id.get(target_id)
            if not target:
                continue
            if filters and not apply_filters([target], filters):
                continue
            seen.add(target_id)
            emitted += 1
            related.append({
                "source_id": target_id,
                "title": target.get("canonical_title"),
                "source_family": target.get("source_family"),
                "source_type": target.get("source_type"),
                "authority_class": target.get("authority_class"),
                "current_relation": target.get("current_relation"),
                "detail_available": target.get("detail_available"),
                "relation_type": edge["type"],
                "related_from_source_id": seed_id,
                "related_from_rank": seed_rank,
                "relation_hash_evidence": edge.get("hash"),
                "projection_authoritative": False,
            })

    out = dict(base_result)
    out["relation_expansion_mode"] = MODE
    out["relation_expansion_authoritative"] = False
    out["relation_expansion_changes_rank"] = False
    out["related_result_count"] = len(related)
    out["related_results"] = related
    out["pipeline"] = list(base_result.get("pipeline") or []) + ["RELATION_EXPANSION"]
    return out


def hybrid_search_with_relations(
    records: list[dict[str, Any]],
    relation_payload: dict[str, Any],
    query: str,
    *,
    filters: dict[str, str] | None = None,
    limit: int = 10,
    family_cap: int = 3,
    per_seed: int = 3,
) -> dict[str, Any]:
    base = hybrid_search(
        records,
        query,
        filters=filters,
        limit=limit,
        family_cap=family_cap,
    )
    return expand_relations(base, records, relation_payload, per_seed=per_seed)
