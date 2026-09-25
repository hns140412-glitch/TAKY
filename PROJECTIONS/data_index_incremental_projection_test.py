#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_incremental_projection import apply_incremental_projection_delta
from data_index_semantic_projection import load_fixture, validate_fixture

FIXTURE = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_semantic_projection.json"

payload, records = load_fixture(FIXTURE)
assert not validate_fixture(payload, records)
assert len(records) == 666

# 1. No-op delta keeps 666 untouched and performs no full reindex.
noop = apply_incremental_projection_delta(records)
assert noop["before_count"] == 666
assert noop["after_count"] == 666
assert noop["affected_count"] == 0
assert noop["full_reindex_performed"] is False
assert noop["raw_reread_performed"] is False
assert noop["current_pointer_mutated"] is False
assert noop["promotion_performed"] is False

# 2. Synthetic new normalized INDEX_L1 record updates only derived projection.
synthetic = {
    "source_id":"TEST_INCREMENTAL_SOURCE_001",
    "canonical_title":"Synthetic incremental indexing test source",
    "source_family":"TEST_INCREMENTAL_FAMILY",
    "source_type":"TEST_SOURCE",
    "authority_class":"REFERENCE_ONLY",
    "domain_facets":["test"],
    "controlled_terms":["incremental"],
    "keywords":["delta"],
    "entities":[],
    "short_summary":"Test-only normalized delta.",
    "detail_terms":[],
    "index_state":"VERIFIED",
    "review_state":None,
    "current_relation":"CANDIDATE",
    "detail_available":False,
}
added = apply_incremental_projection_delta(
    records,
    upserts=[synthetic],
    upstream_authority_changed=True,
)
assert added["after_count"] == 667
assert added["affected_source_ids"] == ["TEST_INCREMENTAL_SOURCE_001"]
assert added["affected_count"] == 1
assert added["promotion_decision_required"] is True
assert added["promotion_performed"] is False
assert added["current_pointer_mutated"] is False
assert "SEMANTIC_RETRIEVAL" in added["affected_projection_scopes"]

# 3. Changed source_id record replaces one row, not the whole corpus.
changed = dict(records[0])
changed["canonical_title"] = str(changed.get("canonical_title") or "") + " [changed-test]"
updated = apply_incremental_projection_delta(
    records,
    upserts=[changed],
    upstream_authority_changed=True,
)
assert updated["after_count"] == 666
assert updated["affected_source_ids"] == [changed["source_id"]]
assert updated["affected_count"] == 1
assert updated["full_reindex_performed"] is False

# 4. Projection removal requires explicit tombstone input and is still derived-only.
removed = apply_incremental_projection_delta(
    records,
    tombstone_source_ids={records[0]["source_id"]},
    upstream_authority_changed=True,
)
assert removed["after_count"] == 665
assert removed["affected_count"] == 1
assert removed["promotion_decision_required"] is True
assert removed["promotion_performed"] is False

# 5. Domain/learning decision fields cannot leak through an incremental delta.
bad = dict(synthetic)
bad["source_id"] = "TEST_BAD"
bad["function_ids"] = ["SHOULD_NOT_BE_HERE"]
try:
    apply_incremental_projection_delta(records, upserts=[bad])
except ValueError as exc:
    assert "decision fields are forbidden" in str(exc)
else:
    raise AssertionError("forbidden decision field was accepted")

print("data_index_incremental_projection: PASS")
