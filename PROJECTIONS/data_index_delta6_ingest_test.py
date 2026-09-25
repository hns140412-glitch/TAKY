#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"PROJECTIONS"))

from data_index_incremental_projection import apply_incremental_projection_delta
from data_index_semantic_projection import load_fixture, validate_fixture

BASE=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v24_semantic_projection.json"
DELTA=ROOT/"PROJECTIONS"/"fixtures"/"data_index_v24_plus_delta6_candidate_projection.json"

payload,records=load_fixture(BASE)
assert not validate_fixture(payload,records)
assert len(records)==666

d=json.loads(DELTA.read_text(encoding="utf-8"))
assert d["delta_count"]==6
assert d["candidate_total"]==672
assert d["projection_authoritative"] is False
ids=[r["source_id"] for r in d["records"]]
assert len(ids)==len(set(ids))==6
assert not set(ids).intersection({r["source_id"] for r in records})

res=apply_incremental_projection_delta(
    records,
    upserts=d["records"],
    upstream_authority_changed=True,
)
assert res["before_count"]==666
assert res["after_count"]==672
assert res["affected_count"]==6
assert res["full_reindex_performed"] is False
assert res["raw_reread_performed"] is False
assert res["current_pointer_mutated"] is False
assert res["promotion_performed"] is False
assert res["promotion_decision_required"] is True

families=[r["source_family"] for r in d["records"]]
assert families.count("LAZY_OWEN_CHATGPT_IMAGE_EDIT_PROMPT_CAROUSEL")==4
assert "MIDDLE_SCHOOL_SOCIAL_HANJA_VOCAB_2015" in families
assert "MIDDLE_SCHOOL_KOREAN_VOCAB_2015" in families

print("data_index_delta6_ingest: PASS")
