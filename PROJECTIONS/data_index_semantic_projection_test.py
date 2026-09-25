#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PROJECTIONS"))
sys.path.insert(0, str(ROOT / "ENFORCEMENT"))

from data_index_semantic_projection import (  # noqa: E402
    MODE,
    load_fixture,
    semantic_search,
    validate_fixture,
)
from data_index_search import normalize_record, search as lexical_search  # noqa: E402

FIXTURE = ROOT / "PROJECTIONS" / "fixtures" / "data_index_v24_semantic_projection.json"

CASES = [
    {
        "id": "D4-Q1",
        "query": "아이의 약한 부분을 찾아 복습 계획에 참고할 자료",
        "families": {
            "KICE_ELEMENTARY_ASSESSMENT_2026",
            "UNIT_ASSESSMENT_5_6",
            "UNIT_ASSESSMENT_1_4",
        },
    },
    {
        "id": "D4-Q2",
        "query": "도면 형상은 유지하면서 표현만 고급스럽게 만드는 참고자료",
        "families": {
            "ARCHITECTURE_AI_PROMPT_AND_RENDERING_WORKFLOW_SOCIAL_REFERENCE",
            "ARCHITECTURE_AI_RENDERING_SOCIAL_DISCUSSION_REFERENCE",
            "AI_ARCHITECTURE_VISUALIZATION_SOCIAL_REFERENCE",
        },
    },
    {
        "id": "D4-Q3",
        "query": "사용자가 직접 디버깅하지 않아도 상태를 복구하는 구조",
        "families": {
            "AI_TROUBLESHOOTING_PROCESS_REDUCTION_CONVERSATION_REFERENCE",
            "GIT_FETCH_TLS_RUNTIME_SESSION_BRIDGE_FAILURE_REFERENCE",
        },
    },
    {
        "id": "D4-Q4",
        "query": "가족 일정과 아이 학습 계획을 함께 다루는 자료",
        "families": {
            "FAMILY_WALL_PLANNER_SOCIAL_DESIGN_REFERENCE",
            "LEARNING_APP_UI_AND_PLANNER_REFERENCE",
            "READY_SET_ASSIGNMENT_ROUTER_AND_SCHEDULE_LOGIC_CHAT_REFERENCE",
            "READY_SET_EXPLORER_WEEKLY_PLANNER_UI_REFERENCE",
        },
    },
    {
        "id": "D4-Q5",
        "query": "단어를 외우게 하기보다 기억 단서를 연결하는 학습 자료",
        "families": {
            "KANG_SEONGTAE_VOCAB_MAP",
            "BA_PPA_FOLD_WORD_RETRIEVAL",
        },
    },
    {
        "id": "D4-Q6",
        "query": "현재 법규가 아니라 과거 사례로만 봐야 하는 건축 자료",
        "families": {
            "SADANG_STATION_AREA_REDEVELOPMENT_INTEGRATED_REVIEW_CASE",
            "SEOUL_PUBLIC_HOUSING_INTEGRATED_REVIEW_CASE_REFERENCE",
            "SEONGSU_OFFICE_BUILDING_REVIEW_LANDSCAPE_CASE_REFERENCE",
        },
        "title_contains": ("2014", "2016"),
    },
]


def _legacy_view(record: dict) -> dict:
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


def _is_relevant(result: dict, case: dict) -> bool:
    if result.get("source_family") in case.get("families", set()):
        return True
    title = str(result.get("title") or "")
    return any(token in title for token in case.get("title_contains", ()))


def main() -> int:
    payload, records = load_fixture(FIXTURE)
    errors = validate_fixture(payload, records)
    assert not errors, errors
    assert len(records) == 666
    assert MODE == "CONTROLLED_CONCEPT_VECTOR_V1__NOT_NEURAL_EMBEDDING"

    legacy = [normalize_record(_legacy_view(r)) for r in records]
    report = []
    semantic_wins = 0

    for case in CASES:
        lexical = lexical_search(legacy, case["query"], limit=10, relation_depth=0)
        semantic = semantic_search(records, case["query"], limit=10)
        lexical_hits = [x for x in lexical["results"] if _is_relevant(x, case)]
        semantic_hits = [x for x in semantic["results"] if _is_relevant(x, case)]
        if semantic_hits and not lexical_hits:
            semantic_wins += 1
        report.append({
            "id": case["id"],
            "query": case["query"],
            "lexical_result_count": lexical["result_count"],
            "lexical_relevant_hit_at_10": bool(lexical_hits),
            "lexical_top3": [
                {"title": x.get("title"), "source_family": x.get("source_family")}
                for x in lexical["results"][:3]
            ],
            "semantic_result_count": semantic["result_count"],
            "semantic_relevant_hit_at_10": bool(semantic_hits),
            "semantic_first_relevant_rank": next(
                (i for i, x in enumerate(semantic["results"], start=1) if _is_relevant(x, case)),
                None,
            ),
            "semantic_top3": [
                {
                    "title": x.get("title"),
                    "source_family": x.get("source_family"),
                    "matched_concepts": x.get("matched_concepts"),
                }
                for x in semantic["results"][:3]
            ],
        })

    # Locked D4 stress suite: every case must gain at least one semantically
    # relevant candidate in top 10. This is an authored benchmark, not held-out
    # proof of generalization.
    assert all(x["semantic_relevant_hit_at_10"] for x in report), report
    assert semantic_wins >= 4, report

    receipt = {
        "schema": "TAKY_DATA_INDEX_D4_SEMANTIC_REGRESSION_RECEIPT_V1",
        "projection_authoritative": False,
        "source_current": payload["source_current"],
        "semantic_mode": MODE,
        "embedding_claim": False,
        "benchmark_kind": "LOCKED_AUTHORED_STRESS_QUERIES__NOT_HELD_OUT",
        "semantic_wins_without_lexical_relevant_hit": semantic_wins,
        "cases": report,
        "promotion": "FORBIDDEN_BY_THIS_TEST",
        "next_gate": "D5_RRF_HYBRID_ONLY_AFTER_D2_D3_REGRESSION_STAYS_PASS",
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
