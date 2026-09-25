#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))

from data_index_hybrid_search import hybrid_search  # noqa: E402
from data_index_semantic_projection import load_fixture, validate_fixture  # noqa: E402

FIXTURE = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_semantic_projection.json"

CASES = [
    ("아이의 약한 부분을 찾아 복습 계획에 참고할 자료", {"KICE_ELEMENTARY_ASSESSMENT_2026","UNIT_ASSESSMENT_5_6","UNIT_ASSESSMENT_1_4"}, ()),
    ("도면 형상은 유지하면서 표현만 고급스럽게 만드는 참고자료", {"ARCHITECTURE_AI_PROMPT_AND_RENDERING_WORKFLOW_SOCIAL_REFERENCE","ARCHITECTURE_AI_RENDERING_SOCIAL_DISCUSSION_REFERENCE","AI_ARCHITECTURE_VISUALIZATION_SOCIAL_REFERENCE"}, ()),
    ("사용자가 직접 디버깅하지 않아도 상태를 복구하는 구조", {"AI_TROUBLESHOOTING_PROCESS_REDUCTION_CONVERSATION_REFERENCE","GIT_FETCH_TLS_RUNTIME_SESSION_BRIDGE_FAILURE_REFERENCE"}, ()),
    ("가족 일정과 아이 학습 계획을 함께 다루는 자료", {"FAMILY_WALL_PLANNER_SOCIAL_DESIGN_REFERENCE","LEARNING_APP_UI_AND_PLANNER_REFERENCE","READY_SET_ASSIGNMENT_ROUTER_AND_SCHEDULE_LOGIC_CHAT_REFERENCE","READY_SET_EXPLORER_WEEKLY_PLANNER_UI_REFERENCE"}, ()),
    ("단어를 외우게 하기보다 기억 단서를 연결하는 학습 자료", {"KANG_SEONGTAE_VOCAB_MAP","BA_PPA_FOLD_WORD_RETRIEVAL"}, ()),
    ("현재 법규가 아니라 과거 사례로만 봐야 하는 건축 자료", {"SADANG_STATION_AREA_REDEVELOPMENT_INTEGRATED_REVIEW_CASE","SEOUL_PUBLIC_HOUSING_INTEGRATED_REVIEW_CASE_REFERENCE","SEONGSU_OFFICE_BUILDING_REVIEW_LANDSCAPE_CASE_REFERENCE"}, ("2014","2016")),
]


def relevant(result, families, title_tokens):
    return result.get("source_family") in families or any(
        token in str(result.get("title") or "") for token in title_tokens
    )


payload, records = load_fixture(FIXTURE)
assert not validate_fixture(payload, records)
assert len(records) == 666

# 1. Exact source_id is never diluted by semantic fusion.
sid = records[0]["source_id"]
r = hybrid_search(records, sid, limit=10)
assert r["route"] == "EXACT_SHORT_CIRCUIT"
assert r["results"][0]["source_id"] == sid
assert r["results"][0]["channels"]["exact"] is True

# 2. Exact family request lifts family cap.
family = next(x["source_family"] for x in records if x.get("source_family") and sum(1 for y in records if y.get("source_family") == x.get("source_family")) >= 4)
r = hybrid_search(records, family, limit=10)
assert r["route"] == "EXACT_SHORT_CIRCUIT"
assert r["family_cap_applied"] is False
assert all(x["source_family"] == family for x in r["results"])

# 3. Vague D4 queries use lexical + semantic RRF and retain a relevant top-10 hit.
for query, families, title_tokens in CASES:
    r = hybrid_search(records, query, limit=10)
    assert r["route"] == "LEXICAL_SEMANTIC_RRF", (query, r["route"])
    assert any(relevant(x, families, title_tokens) for x in r["results"]), (query, r["results"])
    counts = Counter(x.get("source_family") for x in r["results"] if x.get("source_family"))
    assert max(counts.values(), default=0) <= 3, (query, counts)

# 4. Structured filter is applied before fusion.
authority = next(x["authority_class"] for x in records if x.get("authority_class"))
r = hybrid_search(records, "자료", filters={"authority": authority}, limit=10)
assert all(x["authority_class"] == authority for x in r["results"])

# 5. D5 remains derived/non-authoritative and does not claim neural embedding.
r = hybrid_search(records, CASES[0][0], limit=10)
assert r["projection_authoritative"] is False
assert r["embedding_claim"] is False
assert r["semantic_score_is_authority"] is False

print("data_index_hybrid_search: PASS")
