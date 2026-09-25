#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_relation_expansion import hybrid_search_with_relations, load_relations
from data_index_semantic_projection import load_fixture, validate_fixture

SEM = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_semantic_projection.json"
REL = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_relation_projection.json"

payload, records = load_fixture(SEM)
assert not validate_fixture(payload, records)
relations = load_relations(REL)

assert relations["source_current"]["name"] == payload["source_current"]["name"]
assert relations["source_current"]["total"] == 666
assert relations["source_pair_count"] == 6
assert relations["edge_count"] == 12
assert all(e["type"] == "EXACT_DUPLICATE_OF" for e in relations["edges"])

pair = relations["edges"][0]
seed = pair["from"]
target = pair["to"]

# 1. D5 exact result is preserved; relation result is supplemental.
r = hybrid_search_with_relations(records, relations, seed, limit=10)
assert r["route"] == "EXACT_SHORT_CIRCUIT"
assert r["results"][0]["source_id"] == seed
assert r["relation_expansion_changes_rank"] is False
assert any(x["source_id"] == target and x["relation_type"] == "EXACT_DUPLICATE_OF" for x in r["related_results"])

# 2. No inferred family/temporal/title relation: unrelated exact lookup has no fabricated edge.
unrelated = next(x["source_id"] for x in records if x["source_id"] not in {e["from"] for e in relations["edges"]})
r2 = hybrid_search_with_relations(records, relations, unrelated, limit=10)
assert r2["results"][0]["source_id"] == unrelated
assert r2["related_result_count"] == 0

# 3. Structured filters remain binding on expansion.
seed_record = next(x for x in records if x["source_id"] == seed)
target_record = next(x for x in records if x["source_id"] == target)
if seed_record.get("authority_class") != target_record.get("authority_class"):
    r3 = hybrid_search_with_relations(
        records, relations, seed,
        filters={"authority": seed_record["authority_class"]},
        limit=10,
    )
    assert all(x["authority_class"] == seed_record["authority_class"] for x in r3["related_results"])

# 4. Projection remains non-authoritative and V24-derived.
assert r["projection_authoritative"] is False
assert r["relation_expansion_authoritative"] is False
assert r["pipeline"][-1] == "RELATION_EXPANSION"

print("data_index_relation_expansion: PASS")
