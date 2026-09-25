#!/usr/bin/env python3
"""TAKY D5 hybrid search projection.

Pipeline:
CURRENT-derived fixture -> structured filter -> exact short-circuit
-> lexical + controlled semantic vector -> RRF -> family diversification.

This layer is rebuildable and non-authoritative. Relation expansion / DETAIL /
RAW escalation are intentionally outside this D5 slice.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ENFORCEMENT"))
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_search import exact_scores, lexical_scores, normalize_record, rrf_fuse  # noqa: E402
from data_index_semantic_projection import (  # noqa: E402
    MODE as SEMANTIC_MODE,
    apply_filters,
    load_fixture,
    semantic_search,
    validate_fixture,
)

MODE = "D5_RRF_HYBRID_V1"


def _legacy_view(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": record.get("source_id"),
        "title": record.get("canonical_title"),
        "source_family": record.get("source_family"),
        "source_type": record.get("source_type"),
        "authority_level": record.get("authority_class"),
        "domain_facets": record.get("domain_facets") or [],
        "controlled_terms": record.get("controlled_terms") or [],
        "keywords": record.get("keywords") or [],
        "entities": record.get("entities") or [],
        "current_relation": record.get("current_relation"),
    }


def _family_diversify(
    ranked: list[tuple[str, float]],
    by_id: dict[str, dict[str, Any]],
    cap: int,
) -> list[tuple[str, float]]:
    if cap <= 0:
        return ranked
    counts: defaultdict[str, int] = defaultdict(int)
    out: list[tuple[str, float]] = []
    for sid, score in ranked:
        family = by_id[sid].get("source_family")
        key = str(family) if family else f"__NO_FAMILY__:{sid}"
        if counts[key] >= cap:
            continue
        counts[key] += 1
        out.append((sid, score))
    return out


def hybrid_search(
    records: list[dict[str, Any]],
    query: str,
    *,
    filters: dict[str, str] | None = None,
    limit: int = 10,
    family_cap: int = 3,
) -> dict[str, Any]:
    filters = filters or {}
    candidates = apply_filters(records, filters)
    by_id = {r["source_id"]: r for r in candidates}
    legacy = [normalize_record(_legacy_view(r)) for r in candidates]

    exact = exact_scores(legacy, query)
    strong_exact = {sid: score for sid, score in exact.items() if score >= 0.9}
    explicit_family = "family" in filters or any(
        query.strip().lower() == str(r.get("source_family") or "").lower()
        for r in candidates
    )

    if strong_exact:
        ranked = sorted(strong_exact.items(), key=lambda kv: (-kv[1], kv[0]))
        if not explicit_family:
            ranked = _family_diversify(ranked, by_id, family_cap)
        channel_scores = {"exact": strong_exact, "lexical": {}, "semantic": {}}
        route = "EXACT_SHORT_CIRCUIT"
    else:
        lexical = lexical_scores(legacy, query)
        semantic_result = semantic_search(candidates, query, limit=max(1, len(candidates)))
        semantic = {
            r["source_id"]: float(r["semantic_score"])
            for r in semantic_result["results"]
            if r.get("semantic_score", 0) > 0
        }
        fused = rrf_fuse([lexical, semantic])
        ranked = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))
        if not explicit_family:
            ranked = _family_diversify(ranked, by_id, family_cap)
        channel_scores = {"exact": exact, "lexical": lexical, "semantic": semantic}
        route = "LEXICAL_SEMANTIC_RRF"

    results: list[dict[str, Any]] = []
    for sid, score in ranked[:limit]:
        r = by_id[sid]
        results.append({
            "source_id": sid,
            "title": r.get("canonical_title"),
            "source_family": r.get("source_family"),
            "source_type": r.get("source_type"),
            "authority_class": r.get("authority_class"),
            "current_relation": r.get("current_relation"),
            "detail_available": r.get("detail_available"),
            "score": round(score, 8),
            "channels": {
                "exact": sid in channel_scores["exact"],
                "lexical": sid in channel_scores["lexical"],
                "semantic": sid in channel_scores["semantic"],
            },
        })

    return {
        "projection_authoritative": False,
        "hybrid_mode": MODE,
        "semantic_mode": SEMANTIC_MODE,
        "embedding_claim": False,
        "semantic_score_is_authority": False,
        "route": route,
        "pipeline": (
            ["STRUCTURED_FILTER", "EXACT_SHORT_CIRCUIT"]
            if route == "EXACT_SHORT_CIRCUIT"
            else ["STRUCTURED_FILTER", "LEXICAL_RETRIEVAL", "CONTROLLED_SEMANTIC_VECTOR", "RRF", "FAMILY_DIVERSIFICATION"]
        ),
        "query": query,
        "filters": filters,
        "candidate_count": len(candidates),
        "family_cap": None if explicit_family else family_cap,
        "family_cap_applied": not explicit_family,
        "result_count": len(results),
        "results": results,
    }


def _parse_filters(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid filter {value!r}; expected key=value")
        key, expected = value.split("=", 1)
        key, expected = key.strip(), expected.strip()
        if not key or not expected:
            raise ValueError(f"invalid filter {value!r}; expected non-empty key=value")
        out[key] = expected
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--filter", action="append", default=[])
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--family-cap", type=int, default=3)
    args = ap.parse_args()
    if args.limit < 1:
        ap.error("--limit must be >= 1")
    if args.family_cap < 0:
        ap.error("--family-cap must be >= 0")

    payload, records = load_fixture(args.fixture)
    errors = validate_fixture(payload, records)
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(
        hybrid_search(
            records,
            args.query,
            filters=_parse_filters(args.filter),
            limit=args.limit,
            family_cap=args.family_cap,
        ),
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
