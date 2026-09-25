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
REVIEW_TERMS = ("검토", "참고", "자료로", "분석")
INTAKE_TERMS = ("참고하게", "참고해", "참고자료", "자료로 써", "자료로 사용", "활용해", "반영 후보")
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
    if text in PLAIN_REVIEW_EXACT and not record.get("reference_intake_intent"):
        return {"pass": True, "route_type": "PLAIN_REVIEW", "write_authorized": False,
                "canonical_promotion_authorized": False,
                "pipeline": ["READ", "ANALYZE", "COMPARE", "REPORT"]}

    review_signal = any(term in text for term in REVIEW_TERMS)
    intake_signal = bool(record.get("reference_intake_intent")) or any(term in text for term in INTAKE_TERMS)
    if not has_source or not review_signal:
        return {"pass": False, "detected": ["REFERENCE_INTAKE_NOT_ESTABLISHED"]}

    if not intake_signal and not bool(record.get("use_as_reference")):
        return {"pass": True, "route_type": "PLAIN_SOURCE_REVIEW", "write_authorized": False,
                "canonical_promotion_authorized": False,
                "pipeline": ["SOURCE_READ", "ANALYZE", "COMPARE", "REPORT"]}

    domain = _norm(record.get("domain"))
    if not domain:
        domain = "learning" if any(term in text for term in LEARNING_TERMS) else "unspecified"

    consumer = "LEARNING_ENGINE" if domain in {"learning", "education", "family_learning"} else "DOMAIN_ENGINE"
    pipeline = [
        "SOURCE_OR_LOCATOR",
        "MINING_ACQUIRE_AND_DISCOVER_IF_NEEDED",
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
