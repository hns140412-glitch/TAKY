#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_hybrid_search import hybrid_search
from data_index_semantic_projection import load_fixture, validate_fixture
from data_index_raw_escalation import select_raw_candidates

AUTH = ROOT / "PROJECTIONS" / "fixtures" / "data_index_full_contract_authority_v1.json"
SEM = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_semantic_projection.json"
REL = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_relation_projection.json"
DET = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_detail_projection.json"
RAW_CONTRACT = ROOT / "C2S" / "DATA_INDEX_RAW_ESCALATION_TASK_CONTRACT_2026-09-25.json"
DETAIL_CONTRACT = ROOT / "C2S" / "DATA_INDEX_DETAIL_FETCH_TASK_CONTRACT_2026-09-25.json"
PARA_CORRECTION = ROOT / "C2S" / "DATA_INDEX_PARAPHRASE_REGRESSION_CORRECTION_2026-09-25.json"

auth = json.loads(AUTH.read_text(encoding="utf-8"))
expected = auth["expected"]
assert auth["projection_authoritative"] is False

payload, records = load_fixture(SEM)
assert not validate_fixture(payload, records)
assert len(records) == expected["corpus_total"] == 666
assert payload["source_current"]["name"] == expected["current_name"]
assert payload["source_current"]["id"] == expected["current_id"]
assert payload["projection_authoritative"] is False
assert payload["raw_reread"] is False
assert payload["historical_versions_included"] is False

# NO_SOURCE_LOSS + CURRENT_POINTER_INTEGRITY
source_ids = [r["source_id"] for r in records]
assert len(source_ids) == len(set(source_ids)) == 666

# EXACT_LOOKUP_PRECISION: exact source_id must short-circuit to itself.
sid = source_ids[0]
exact = hybrid_search(records, sid, limit=10)
assert exact["route"] == "EXACT_SHORT_CIRCUIT"
assert exact["results"][0]["source_id"] == sid
assert exact["results"][0]["channels"]["exact"] is True

# NO_LEARNING_POLICY_LEAKAGE_IN_INDEX / derived projection boundary.
for r in records:
    for forbidden in ("function_ids","runtime_connection_state","value_statement","utilization_class","owner","consumers"):
        assert forbidden not in r, (r["source_id"], forbidden)

# Relation projection is explicit-only; no family/temporal/title inference.
rel = json.loads(REL.read_text(encoding="utf-8"))
assert rel["projection_authoritative"] is False
assert rel["raw_reread"] is False
assert rel["source_pair_count"] == 6
assert rel["edge_count"] == 12
assert set(rel["allowed_relation_types"]) == {"EXACT_DUPLICATE_OF"}
assert rel["inferred_relations"] is False

# DETAIL is sparse/on-demand and cannot reread RAW or mutate authority.
det = json.loads(DET.read_text(encoding="utf-8"))
assert det["source_current"]["name"] == expected["current_name"]
assert det["detail_record_count"] == 6
assert det["projection_authoritative"] is False
assert det["raw_reread"] is False

detail_contract = json.loads(DETAIL_CONTRACT.read_text(encoding="utf-8"))
assert detail_contract["source_reindex_all"] is False
assert detail_contract["raw_reread"] is False
assert "DETAIL_FETCH_DOES_NOT_CHANGE_BASE_RANK" in detail_contract["guards"]
assert "DETAIL_FETCH_DOES_NOT_CHANGE_AUTHORITY" in detail_contract["guards"]

# RAW escalation is candidate-only; automatic/bulk RAW reread is forbidden.
raw_contract = json.loads(RAW_CONTRACT.read_text(encoding="utf-8"))
assert raw_contract["source_current"] == expected["current_name"]
assert raw_contract["source_reindex_all"] is False
assert raw_contract["automatic_raw_reread"] is False
assert raw_contract["output"] == "RAW_FETCH_CANDIDATES_ONLY"
assert "BULK_RAW_REREAD" in raw_contract["forbidden"]

oversize_results = {
    "pipeline": ["DETAIL_FETCH"],
    "results": [
        {"source_id": x, "title": x, "detail_available": False}
        for x in expected["held_oversize_ids"]
    ],
    "related_results": [],
}
blocked = select_raw_candidates(
    oversize_results,
    unresolved_source_ids=set(expected["held_oversize_ids"]),
)
assert blocked["candidate_count"] == 0
assert blocked["blocked_count"] == 2
assert blocked["raw_fetch_performed"] is False

# Paraphrase evidence must retain the real limitation instead of tuning it away.
para = json.loads(PARA_CORRECTION.read_text(encoding="utf-8"))
assert para["observed"]["lexical_hit_at_10"] == 0
assert para["observed"]["semantic_hit_at_10"] == 7
assert para["observed"]["hybrid_hit_at_10"] == 8
assert para["observed"]["failed_case"] == "PH-Q7"
assert para["observed"]["failed_case_hybrid_hit"] is True
assert para["corrected_gate"]["independent_generalization_claim"] is False
assert para["promotion"] == "FORBIDDEN_BY_THIS_CHECKPOINT"

# Authority-contract snapshot invariants.
assert expected["migration_mode"] == "INCREMENTAL_ON_TOUCH_OR_QUERY"
assert expected["full_reindex_required"] is False
assert expected["source_reindex_all"] is False
assert expected["search_projection_authoritative"] is False
assert expected["current_rule"] == "EXPLICIT_POINTER_PROMOTION_ONLY"
assert expected["netlify"] == "NONE"
assert expected["deployment"] == "NONE"
assert expected["role_boundary"]["mining_engine"] == "SOURCE_DISCOVERY_AND_ACQUISITION"
assert expected["role_boundary"]["indexing"] == "ORGANIZE_CLASSIFY_RELATE_AND_RETRIEVE"
assert expected["role_boundary"]["learning_engine"] == "DECIDE_HOW_INDEXED_EVIDENCE_IS_USED"

receipt = {
    "schema":"TAKY_DATA_INDEX_FULL_CONTRACT_REGRESSION_RECEIPT_V1",
    "status":"PASS",
    "current":expected["current_name"],
    "corpus_total":len(records),
    "source_reindex_all":False,
    "search_projection_authoritative":False,
    "relation_explicit_pairs":rel["source_pair_count"],
    "detail_records":det["detail_record_count"],
    "raw_fetch_performed":False,
    "paraphrase_semantic_hit_at_10":para["observed"]["semantic_hit_at_10"],
    "paraphrase_hybrid_hit_at_10":para["observed"]["hybrid_hit_at_10"],
    "promotion":"NOT_AUTHORIZED_BY_REGRESSION",
    "v25_created":False,
}
print(json.dumps(receipt, ensure_ascii=False, indent=2))
