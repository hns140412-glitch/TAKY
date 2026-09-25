#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"PROJECTIONS"))

from data_index_semantic_projection import load_fixture, validate_fixture
from data_index_hybrid_search import hybrid_search
from data_index_raw_escalation import select_raw_candidates

SEM=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v25_semantic_projection.json"
REL=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v25_relation_projection.json"
DET=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v25_detail_projection.json"
RAW=ROOT/"C2S"/"DATA_INDEX_RAW_ESCALATION_TASK_CONTRACT_2026-09-25_V2.json"

payload,records=load_fixture(SEM)
assert not validate_fixture(payload,records)
assert payload["source_current"]["name"]=="DATA_UTILIZATION_INDEX_2026-09-25_V25.json"
assert payload["source_current"]["total"]==672
assert len(records)==672
ids=[r["source_id"] for r in records]
assert len(ids)==len(set(ids))==672

delta_ids={
"1tg5X0aoJkBUCXLcGmV-OEgTVDud65fcd",
"1j20aPIXSl8Ll6TbamvJVo7ez2iPt1wJB",
"1PKL4w7XOtKBPhPEejKkHoGkDRhOSrGv5",
"1esFLtkP-2QaQM7AoeSi0U7gWR7D5EFj7",
"1th-m_QOgy_P6clXhAZrQcdVAynqD4IGk",
"1RAQ13s0fMdE17Jk9-baOnBsochodEM1a",
}
assert delta_ids.issubset(set(ids))

# Exact retrieval must include promoted delta without semantic override.
for sid in delta_ids:
    r=hybrid_search(records,sid,limit=10)
    assert r["route"]=="EXACT_SHORT_CIRCUIT"
    assert r["results"][0]["source_id"]==sid

# Decision fields remain outside projection.
for row in records:
    for forbidden in ("function_ids","runtime_connection_state","value_statement","utilization_class","owner","consumers"):
        assert forbidden not in row

rel=json.loads(REL.read_text(encoding="utf-8"))
assert rel["source_current"]["name"]=="DATA_UTILIZATION_INDEX_2026-09-25_V25.json"
assert rel["source_current"]["total"]==672
assert rel["source_pair_count"]==6
assert rel["edge_count"]==12
assert rel["inferred_relations"] is False
assert set(rel["allowed_relation_types"])=={"EXACT_DUPLICATE_OF"}

det=json.loads(DET.read_text(encoding="utf-8"))
assert det["source_current"]["name"]=="DATA_UTILIZATION_INDEX_2026-09-25_V25.json"
assert det["detail_record_count"]==12
detail_ids={r["source_id"] for r in det["records"]}
assert delta_ids.issubset(detail_ids)
assert det["projection_authoritative"] is False
assert det["raw_reread"] is False

raw=json.loads(RAW.read_text(encoding="utf-8"))
assert raw["source_current"]=="DATA_UTILIZATION_INDEX_2026-09-25_V25.json"
assert raw["source_reindex_all"] is False
assert raw["automatic_raw_reread"] is False

held={"1bnDccQ1aDJf5Y7bDiA-9kUJ0LZ-c-sYy","114osqcmcJAaVDecmpkneNdCgcD4JRRto"}
blocked=select_raw_candidates(
    {"pipeline":["DETAIL_FETCH"],"results":[{"source_id":x,"title":x,"detail_available":False} for x in held],"related_results":[]},
    unresolved_source_ids=held,
)
assert blocked["candidate_count"]==0
assert blocked["blocked_count"]==2
assert blocked["raw_fetch_performed"] is False

print(json.dumps({
 "status":"PASS",
 "current":"V25",
 "corpus":672,
 "delta6_present":True,
 "detail_records":12,
 "relation_edges":12,
 "held_oversize":2,
 "source_reindex_all":False,
 "search_projection_authoritative":False
},ensure_ascii=False))
