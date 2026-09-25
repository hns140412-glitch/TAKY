#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"PROJECTIONS"))
from data_index_semantic_projection import load_fixture, validate_fixture
from data_index_hybrid_search import hybrid_search
from data_index_raw_escalation import select_raw_candidates

SEM=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v26_semantic_projection.json"
DET=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v26_detail_projection.json"
REL=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v26_relation_projection.json"
RAW=ROOT/"C2S"/"DATA_INDEX_RAW_ESCALATION_TASK_CONTRACT_2026-09-25_V3.json"

payload,records=load_fixture(SEM)
assert not validate_fixture(payload,records)
assert payload["source_current"]["name"]=="DATA_UTILIZATION_INDEX_2026-09-25_V26.json"
assert payload["source_current"]["total"]==679
assert len(records)==679
ids=[r["source_id"] for r in records]
assert len(ids)==len(set(ids))==679
delta7={
"1s1JJ5yjIy5E9iDEbC4Ug4UWKDw17a-sC","1QO6O7gTvHs3ez-vxvp0XmALnaRROYtFs",
"1SkileVnnKE0pi6-nK7x-AlF8ZtcLe6hN","1URWZqQZ6vnm_ZJGyXKVGnIUTY13wZB-f",
"12LxIgO4r-IS7D_Dew6X4PADdUsCoNR-6","1CN28Wr_oON9zIymCun55QB3J9QtXteoc",
"1LxKJytS0AsAbdOT5p9RTegMuIfdonTs5"}
assert delta7.issubset(set(ids))
for sid in delta7:
 r=hybrid_search(records,sid,limit=10)
 assert r["route"]=="EXACT_SHORT_CIRCUIT"
 assert r["results"][0]["source_id"]==sid

det=json.loads(DET.read_text(encoding="utf-8"))
assert det["source_current"]["total"]==679
assert det["detail_record_count"]==19
assert delta7.issubset({r["source_id"] for r in det["records"]})
rel=json.loads(REL.read_text(encoding="utf-8"))
assert rel["source_current"]["total"]==679
assert rel["source_pair_count"]==6 and rel["edge_count"]==12
assert rel["inferred_relations"] is False
raw=json.loads(RAW.read_text(encoding="utf-8"))
assert raw["source_current"]=="DATA_UTILIZATION_INDEX_2026-09-25_V26.json"
assert raw["source_reindex_all"] is False and raw["automatic_raw_reread"] is False
held={"1bnDccQ1aDJf5Y7bDiA-9kUJ0LZ-c-sYy","114osqcmcJAaVDecmpkneNdCgcD4JRRto"}
blocked=select_raw_candidates({"pipeline":["DETAIL_FETCH"],"results":[{"source_id":x,"title":x,"detail_available":False} for x in held],"related_results":[]},unresolved_source_ids=held)
assert blocked["candidate_count"]==0 and blocked["blocked_count"]==2
print(json.dumps({"status":"PASS","current":"V26","corpus":679,"delta7_present":True,"detail_records":19,"relation_edges":12,"held_oversize":2},ensure_ascii=False))
