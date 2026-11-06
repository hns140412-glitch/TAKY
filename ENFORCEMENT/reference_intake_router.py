#!/usr/bin/env python3
"""Route external/reference review requests across Mining -> Indexing -> domain consumer.

This classifier preserves the distinction between plain read-only review and
reference-intake review. It emits an execution plan only; it does not fetch,
persist, promote, or mutate canonical state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PLAIN_REVIEW_EXACT = {"/검토", "타키 검토", "타키 기준으로 검토"}
NO_MINING_TERMS = ("보기만 해", "마이닝하지 마", "저장하지 마", "일회성으로만 검토해")
REVIEW_TERMS = ("검토", "참고", "자료로", "분석", "봐봐", "확인해", "살펴봐")
LEARNING_TERMS = ("학습", "러닝", "learning", "복습", "서술형", "글쓰기", "교육")

def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())

def route(record: dict) -> dict:
    text = _norm(record.get("intent_text"))
    has_source = bool(
        record.get("has_reference_source")
        or record.get("source_url")
        or record.get("source_id")
        or record.get("source_locator")
    )
    # A user-supplied external reference is mined by default under MASTER.
    # Only an explicit no-storage instruction may bypass source intake.
    if any(term in text for term in NO_MINING_TERMS) or (
        text in PLAIN_REVIEW_EXACT and not has_source
    ):
        return {"pass": True, "route_type": "PLAIN_REVIEW", "write_authorized": False,
                "canonical_promotion_authorized": False,
                "pipeline": ["READ", "ANALYZE", "COMPARE", "REPORT"]}

    review_signal = any(term in text for term in REVIEW_TERMS)
    if not has_source or not review_signal:
        return {"pass": False, "detected": ["REFERENCE_INTAKE_NOT_ESTABLISHED"]}

    domain = _norm(record.get("domain"))
    if not domain:
        domain = "learning" if any(term in text for term in LEARNING_TERMS) else "unspecified"

    consumer = "LEARNING_ENGINE" if domain in {"learning", "education", "family_learning"} else "DOMAIN_ENGINE"
    pipeline = [
        "SOURCE_OR_LOCATOR",
        "MINING_ACQUIRE_AND_DISCOVER_IF_NEEDED",
        "SOURCE_ACTOR_AUTHOR_PROVENANCE_CLASSIFY",
        "SOURCE_DIRECTION_INTENT_BIAS_CLASSIFY",
        "APPLICABILITY_SCOPE_AND_AUTHORITY_CEILING_CLASSIFY",
        "INDEX_EXISTENCE_DUPLICATE_VERSION_CHECK",
        "INDEX_INCREMENTAL_CLASSIFY_RELATE_RETRIEVAL_METADATA",
        consumer,
        "EVIDENCE_GAP_TO_MINING_IF_NEEDED",
        "REFERENCE_ONLY_OR_CANDIDATE_DISPOSITION",
        "REPORT",
    ]
    return {
        "pass": True,
        "route_type": "REFERENCE_INTAKE_REVIEW",
        "domain": domain,
        "consumer": consumer,
        "write_authorized": True,
        "write_scope": "REFERENCE_INDEX_STATE_ONLY",
        "canonical_promotion_authorized": False,
        "full_corpus_reindex": False,
        "pipeline": pipeline,
        "guards": [
            "MINING != INDEXING",
            "INDEXING != LEARNING",
            "REFERENCE_INTAKE != CANONICAL_PROMOTION",
            "INDEXED != APPROVED_POLICY",
            "DUPLICATE != NEW_EVIDENCE",
            "AUTHOR != AUTHORITY",
            "DIRECTION != APPLICABILITY_SCOPE",
            "SOURCE_TRUST != CANONICAL_AUTHORITY",
        ],
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    args = ap.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = route(record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("pass") else 1

if __name__ == "__main__":
    raise SystemExit(main())
