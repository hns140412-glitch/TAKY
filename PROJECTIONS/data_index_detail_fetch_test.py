#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_detail_fetch import fetch_detail_for_results, load_detail_fixture

FIX = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_detail_projection.json"
payload = load_detail_fixture(FIX)

assert payload["source_current"]["name"] == "DATA_UTILIZATION_INDEX_2026-09-25_V24.json"
assert payload["detail_record_count"] == 6
assert payload["raw_reread"] is False

first = payload["records"][0]
sid = first["source_id"]

search = {
    "projection_authoritative": False,
    "pipeline": ["STRUCTURED_FILTER","EXACT_SHORT_CIRCUIT","RELATION_EXPANSION"],
    "results": [
        {
            "source_id": sid,
            "title": first["canonical_title"],
            "source_family": first["source_family"],
            "authority_class": first["authority_class"],
            "current_relation": first["current_relation"],
            "detail_available": True,
            "score": 1.0,
        },
        {
            "source_id": "NO_DETAIL",
            "title": "x",
            "detail_available": False,
            "score": 0.5,
        }
    ],
    "related_results": []
}

# 1. Only detail_available=true result is escalated.
r = fetch_detail_for_results(search, payload)
assert r["detail_result_count"] == 1
assert r["detail_results"][0]["source_id"] == sid
assert r["detail_results"][0]["detail_l2"] == first["detail_l2"]

# 2. Base rank/results are untouched.
assert r["results"] == search["results"]
assert r["detail_fetch_changes_rank"] is False

# 3. No RAW escalation occurs.
assert r["raw_read_performed"] is False
assert r["detail_results"][0]["raw_read_performed"] is False

# 4. Explicit source selection narrows detail fetch.
r2 = fetch_detail_for_results(search, payload, source_ids={"NO_DETAIL"})
assert r2["detail_result_count"] == 0

# 5. Projection remains non-authoritative.
assert r["detail_fetch_authoritative"] is False
assert r["pipeline"][-1] == "DETAIL_FETCH"

print("data_index_detail_fetch: PASS")
