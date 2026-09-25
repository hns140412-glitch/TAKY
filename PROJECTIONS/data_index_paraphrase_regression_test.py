#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))
sys.path.insert(0, str(ROOT / "ENFORCEMENT"))

from data_index_hybrid_search import hybrid_search
from data_index_semantic_projection import load_fixture, semantic_search, validate_fixture
from data_index_search import normalize_record, search as lexical_search

SEMANTIC_FIXTURE = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_semantic_projection.json"
PARAPHRASE_FIXTURE = ROOT / "PROJECTIONS" / "fixtures" / "data_index_d4_paraphrase_regression_v1.json"


def legacy_view(record):
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
    }


def relevant(result, case):
    if result.get("source_family") in set(case.get("families") or []):
        return True
    title = str(result.get("title") or "")
    return any(token in title for token in case.get("title_contains") or [])


payload, records = load_fixture(SEMANTIC_FIXTURE)
assert not validate_fixture(payload, records)
assert len(records) == 666

bench = json.loads(PARAPHRASE_FIXTURE.read_text(encoding="utf-8"))
assert bench["benchmark_kind"] == "PSEUDO_HELD_OUT_PARAPHRASE__NOT_INDEPENDENT_GENERALIZATION_PROOF"
assert bench["authored_stress_queries_reused"] is False
cases = bench["cases"]
assert len(cases) >= 8

legacy = [normalize_record(legacy_view(r)) for r in records]
semantic_hits = 0
hybrid_hits = 0
semantic_only_wins = 0
report = []

for case in cases:
    q = case["query"]
    lex = lexical_search(legacy, q, limit=10, relation_depth=0)
    sem = semantic_search(records, q, limit=10)
    hyb = hybrid_search(records, q, limit=10)

    lex_hit = any(relevant(x, case) for x in lex["results"])
    sem_hit = any(relevant(x, case) for x in sem["results"])
    hyb_hit = any(relevant(x, case) for x in hyb["results"])

    semantic_hits += int(sem_hit)
    hybrid_hits += int(hyb_hit)
    semantic_only_wins += int(sem_hit and not lex_hit)

    report.append({
        "id": case["id"],
        "query": q,
        "lexical_hit_at_10": lex_hit,
        "semantic_hit_at_10": sem_hit,
        "hybrid_hit_at_10": hyb_hit,
        "hybrid_route": hyb["route"],
    })

# Regression thresholds: controlled semantic and hybrid must retain all expected
# paraphrase families; at least some cases must demonstrate semantic recovery
# beyond lexical matching. This does NOT prove independent generalization.
assert semantic_hits >= len(cases) - 1, report\nassert hybrid_hits == len(cases), report\nassert semantic_only_wins >= 6, report
assert all(x["hybrid_route"] == "LEXICAL_SEMANTIC_RRF" for x in report), report

print(json.dumps({
    "schema":"TAKY_DATA_INDEX_D4_PARAPHRASE_REGRESSION_RECEIPT_V1",
    "benchmark_kind":bench["benchmark_kind"],
    "case_count":len(cases),
    "semantic_hit_at_10":semantic_hits,\n    "semantic_standalone_perfect":semantic_hits == len(cases),\n    "semantic_known_limitations":[x["id"] for x in report if not x["semantic_hit_at_10"]],\n    "hybrid_hit_at_10":hybrid_hits,
    "semantic_only_wins":semantic_only_wins,
    "independent_generalization_claim":False,
    "promotion":"FORBIDDEN_BY_THIS_TEST",
    "cases":report
}, ensure_ascii=False, indent=2))
