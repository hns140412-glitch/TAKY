#!/usr/bin/env python3
"""Route Learning evidence gaps through Indexing before Mining.

Learning may emit a gap but cannot authorize Mining. This broker performs the
Index existence check first. Only an insufficient index result can produce a
MINING_REQUEST. No acquisition or canonical promotion happens here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_index_search import load_index, search

VERSION = "TAKY_LEARNING_EVIDENCE_GAP_BROKER_V1"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _query_from_gap(gap: dict[str, Any]) -> str:
    terms = gap.get("query_terms")
    if isinstance(terms, list):
        values = [_clean(x) for x in terms if _clean(x)]
        if values:
            return " ".join(values)
    scope = gap.get("scope") if isinstance(gap.get("scope"), dict) else {}
    return " ".join(
        x for x in (
            _clean(scope.get("subject")),
            _clean(scope.get("concept_skill_target")),
            _clean(gap.get("gap_type")),
        )
        if x
    )


def route_gap(
    gap: dict[str, Any],
    *,
    index_path: Path,
    min_results: int = 1,
    consumer: str = "LEARNING_ENGINE",
) -> dict[str, Any]:
    if not isinstance(gap, dict):
        return {"pass": False, "detected": ["EVIDENCE_GAP_REQUIRED"]}
    if gap.get("owner") != "LEARNING_ENGINE_CORE":
        return {"pass": False, "detected": ["EVIDENCE_GAP_OWNER_INVALID"]}
    if gap.get("index_check_required") is not True:
        return {"pass": False, "detected": ["INDEX_EXISTENCE_CHECK_REQUIRED"]}
    if gap.get("mining_request_authorized") is True:
        return {"pass": False, "detected": ["LEARNING_MINING_AUTHORIZATION_FORBIDDEN"]}

    query = _query_from_gap(gap)
    if not query:
        return {"pass": False, "detected": ["EVIDENCE_GAP_QUERY_EMPTY"]}

    if min_results < 1:
        return {"pass": False, "detected": ["MIN_RESULTS_INVALID"]}

    records = load_index(index_path)
    result = search(records, query, filters={}, limit=max(min_results, 5), relation_depth=1)
    hits = result.get("results", [])

    if len(hits) >= min_results:
        return {
            "pass": True,
            "version": VERSION,
            "gap_id": gap.get("gap_id"),
            "index_checked": True,
            "index_sufficient": True,
            "decision": "INDEX_REQUERY",
            "mining_request": None,
            "retrieval": result,
            "invariant": "INDEX_FIRST__MINING_ONLY_IF_INSUFFICIENT",
        }

    request = {
        "request_type": "DOMAIN_EVIDENCE_GAP_MINING_REQUEST",
        "requester": consumer,
        "gap_id": gap.get("gap_id"),
        "gap_type": gap.get("gap_type"),
        "priority": gap.get("priority"),
        "scope": gap.get("scope") or {},
        "query_terms": gap.get("query_terms") or [],
        "existing_source_refs": gap.get("existing_source_refs") or [],
        "requested_capability": gap.get("requested_capability") or "LEARNING_EVIDENCE_SUPPORT",
        "index_check": {
            "performed": True,
            "result_count": len(hits),
            "minimum_required": min_results,
            "semantic_mode": result.get("semantic_mode"),
        },
        "constraints": [
            "MINING_DISCOVERS_AND_ACQUIRES_ONLY",
            "INDEXING_OWNS_PERSISTENT_CLASSIFICATION",
            "LEARNING_OWNS_FINAL_EVIDENCE_USE_DECISION",
            "NO_CANONICAL_PROMOTION",
        ],
    }
    return {
        "pass": True,
        "version": VERSION,
        "gap_id": gap.get("gap_id"),
        "index_checked": True,
        "index_sufficient": False,
        "decision": "MINING_REQUEST",
        "mining_request": request,
        "retrieval": result,
        "invariant": "INDEX_FIRST__MINING_ONLY_IF_INSUFFICIENT",
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=Path, required=True)
    ap.add_argument("--index", type=Path, required=True)
    ap.add_argument("--min-results", type=int, default=1)
    args = ap.parse_args()

    gap = json.loads(args.gap.read_text(encoding="utf-8"))
    result = route_gap(gap, index_path=args.index, min_results=args.min_results)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
