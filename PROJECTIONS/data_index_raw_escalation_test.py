#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_raw_escalation import select_raw_candidates

NO_DETAIL = "SRC_NO_DETAIL"
WITH_DETAIL = "SRC_WITH_DETAIL"
OVERSIZE = "1bnDccQ1aDJf5Y7bDiA-9kUJ0LZ-c-sYy"

search = {
    "projection_authoritative": False,
    "pipeline": ["STRUCTURED_FILTER", "LEXICAL_RETRIEVAL", "CONTROLLED_SEMANTIC_VECTOR", "RRF", "RELATION_EXPANSION", "DETAIL_FETCH"],
    "results": [
        {"source_id": NO_DETAIL, "title": "no detail", "detail_available": False, "source_family": "F1", "authority_class": "A", "current_relation": "CURRENT_INDEX_ENTRY"},
        {"source_id": WITH_DETAIL, "title": "with detail", "detail_available": True, "source_family": "F2", "authority_class": "B", "current_relation": "CURRENT_INDEX_ENTRY"},
        {"source_id": OVERSIZE, "title": "oversize", "detail_available": False, "source_family": None, "authority_class": None, "current_relation": "CURRENT_INDEX_ENTRY"},
    ],
    "related_results": [],
}

# 1. Relevant result without detail can become a RAW candidate, but no RAW is fetched.
r = select_raw_candidates(search, unresolved_source_ids={NO_DETAIL})
assert r["candidate_count"] == 1
assert r["raw_fetch_candidates"][0]["source_id"] == NO_DETAIL
assert r["raw_fetch_performed"] is False
assert r["raw_fetch_candidates"][0]["raw_fetch_performed"] is False

# 2. Existing DETAIL can escalate only when explicitly marked insufficient.
r2 = select_raw_candidates(search, insufficient_detail_source_ids={WITH_DETAIL})
assert r2["candidate_count"] == 1
assert r2["raw_fetch_candidates"][0]["reasons"] == ["DETAIL_PRESENT_BUT_INSUFFICIENT_FOR_REQUEST"]

# 3. Oversize held videos stay blocked without a new access path.
r3 = select_raw_candidates(search, unresolved_source_ids={OVERSIZE})
assert r3["candidate_count"] == 0
assert r3["blocked_count"] == 1
assert r3["blocked_candidates"][0]["blocked_reason"] == "OVERSIZE_HOLD_REQUIRES_NEW_ACCESS_PATH"

# 4. Candidate gate does not invent requests.
r4 = select_raw_candidates(search)
assert r4["candidate_count"] == 0
assert r4["blocked_count"] == 0

# 5. Revalidation is explicit and still performs no RAW read.
r5 = select_raw_candidates(search, revalidation_source_ids={WITH_DETAIL})
assert r5["candidate_count"] == 1
assert "STALE_OR_CONFLICT_REVALIDATION_REQUIRED" in r5["raw_fetch_candidates"][0]["reasons"]
assert r5["automatic_raw_reread"] is False

# 6. Search projection remains non-authoritative.
assert r["projection_authoritative"] is False
assert r["pipeline"][-1] == "RAW_FETCH_CANDIDATE_GATE"

print("data_index_raw_escalation: PASS")
