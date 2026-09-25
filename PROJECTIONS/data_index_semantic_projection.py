#!/usr/bin/env python3
"""TAKY D4 controlled semantic-vector search projection.

Derived/search-only layer. It does not mutate RAW, INDEX, DETAIL, CURRENT,
authority, or domain/learning decisions.

This baseline is deliberately named CONTROLLED_CONCEPT_VECTOR_V1.
It is semantic/vector retrieval, but it is NOT a neural embedding model.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

MODE = "CONTROLLED_CONCEPT_VECTOR_V1__NOT_NEURAL_EMBEDDING"
FORBIDDEN_DECISION_FIELDS = {
    "value_statement",
    "function_ids",
    "runtime_connection_state",
    "utilization_class",
    "gap",
    "cannot_claim",
    "owner",
    "consumers",
}

# Small governed bridge between natural Korean intent words and stable
# cross-language retrieval concepts already present in titles/families/types.
# This is intentionally compact: broad taxonomy expansion belongs in INDEX
# governance, not inside the search scorer.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "education_assessment": ("평가", "진단", "약한", "부족", "취약", "assessment", "diagnostic", "evaluation", "remediation", "mastery"),
    "review_learning": ("복습", "반복", "practice", "revision", "remediation", "spaced", "rehearsal"),
    "learning": ("학습", "learning", "education", "study"),
    "architecture": ("건축", "도면", "설계", "architecture", "architectural", "drawing", "cad", "plan"),
    "rendering": ("렌더", "표현", "시각화", "고급", "render", "rendering", "visualization", "presentation", "prompt"),
    "geometry_preservation": ("형상", "형태", "유지", "보존", "geometry", "geometric", "preserve", "preservation", "controlnet", "lineart"),
    "state": ("상태", "state", "runtime", "session"),
    "recovery": ("복구", "복원", "회복", "recovery", "restore", "restoration", "persistence", "rollback", "fallback", "resume"),
    "debug_reduction": ("디버깅", "문제해결", "오류", "troubleshoot", "troubleshooting", "debug", "failure", "error"),
    "user_autonomy": ("사용자", "human", "user"),
    "family": ("가족", "부모", "아이", "family", "parent", "child", "kid"),
    "planning": ("일정", "계획", "플래너", "schedule", "planner", "planning", "calendar", "assignment", "router"),
    "vocabulary": ("단어", "어휘", "vocabulary", "vocab", "word", "lexeme"),
    "memory": ("기억", "회상", "외우", "암기", "memory", "recall", "memorization", "retrieval"),
    "association": ("단서", "연결", "연상", "어근", "어원", "map", "root", "etymology", "association", "link"),
    "historical": ("과거", "이전", "옛", "historical", "history", "archive", "legacy", "2014", "2016", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"),
    "law_regulation": ("법규", "법령", "규정", "기준", "law", "regulation", "code", "guideline", "standard"),
    "case": ("사례", "case", "precedent"),
}

SEMANTIC_TEXT_FIELDS = (
    "canonical_title",
    "source_family",
    "source_type",
    "domain_facets",
    "controlled_terms",
    "keywords",
    "entities",
    "short_summary",
    "detail_terms",
)


def _norm(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).lower()


def _flatten(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            out.extend(_flatten(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_flatten(item))
        return out
    return [str(value)]


def _semantic_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in SEMANTIC_TEXT_FIELDS:
        parts.extend(_flatten(record.get(key)))
    return " ".join(x for x in parts if x)


def concept_set(text: str) -> set[str]:
    text_n = _norm(text)
    words = set(re.findall(r"[0-9a-z가-힣]+", text_n))
    found: set[str] = set()
    for concept, aliases in CONCEPTS.items():
        for alias in aliases:
            alias_n = _norm(alias)
            # English aliases are word-level to prevent accidental substrings;
            # Korean aliases allow compound-word containment.
            if alias_n in words or (re.search(r"[가-힣]", alias_n) and alias_n in text_n):
                found.add(concept)
                break
    return found


def load_fixture(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("semantic projection fixture must contain records[]")
    return payload, [r for r in records if isinstance(r, dict) and r.get("source_id")]


def validate_fixture(payload: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if payload.get("projection_authoritative") is not False:
        errors.append("projection must be non-authoritative")
    current = payload.get("source_current") or {}
    expected = current.get("total")
    if expected is not None and expected != len(records):
        errors.append(f"record count mismatch: expected {expected}, got {len(records)}")
    if payload.get("raw_reread") is not False:
        errors.append("raw_reread must be false")
    if payload.get("historical_versions_included") is not False:
        errors.append("historical versions must be excluded")
    for r in records:
        leaked = FORBIDDEN_DECISION_FIELDS.intersection(r)
        if leaked:
            errors.append(f"{r.get('source_id')}: forbidden fields leaked: {sorted(leaked)}")
    return errors


def _matches_filter(record: dict[str, Any], key: str, expected: str) -> bool:
    aliases = {
        "family": "source_family",
        "type": "source_type",
        "authority": "authority_class",
        "domain": "domain_facets",
        "current": "current_relation",
    }
    actual = record.get(aliases.get(key, key))
    expected_n = _norm(expected)
    if isinstance(actual, list):
        return any(_norm(v) == expected_n for v in actual)
    return _norm(actual) == expected_n if actual is not None else False


def apply_filters(records: Iterable[dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    return [
        r for r in records
        if all(_matches_filter(r, key, expected) for key, expected in filters.items())
    ]


def _idf(records: list[dict[str, Any]]) -> tuple[dict[str, set[str]], dict[str, float]]:
    by_id = {r["source_id"]: concept_set(_semantic_text(r)) for r in records}
    df: Counter[str] = Counter()
    for concepts in by_id.values():
        df.update(concepts)
    n = len(records)
    idf = {
        concept: math.log((n + 1.0) / (df.get(concept, 0) + 1.0)) + 1.0
        for concept in CONCEPTS
    }
    return by_id, idf


def _cosine(q: set[str], d: set[str], idf: dict[str, float]) -> float:
    common = q.intersection(d)
    if not common:
        return 0.0
    numerator = sum(idf[c] ** 2 for c in common)
    q_norm = math.sqrt(sum(idf[c] ** 2 for c in q))
    d_norm = math.sqrt(sum(idf[c] ** 2 for c in d))
    return numerator / (q_norm * d_norm) if q_norm and d_norm else 0.0


def semantic_search(
    records: list[dict[str, Any]],
    query: str,
    *,
    filters: dict[str, str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    filters = filters or {}
    candidates = apply_filters(records, filters)
    query_concepts = concept_set(query)
    by_id, idf = _idf(candidates)

    ranked: list[tuple[float, str]] = []
    for r in candidates:
        sid = r["source_id"]
        score = _cosine(query_concepts, by_id[sid], idf)
        if score > 0:
            ranked.append((score, sid))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    records_by_id = {r["source_id"]: r for r in candidates}
    results: list[dict[str, Any]] = []
    for score, sid in ranked[:limit]:
        r = records_by_id[sid]
        matched = sorted(query_concepts.intersection(by_id[sid]))
        results.append({
            "source_id": sid,
            "title": r.get("canonical_title"),
            "source_family": r.get("source_family"),
            "source_type": r.get("source_type"),
            "authority_class": r.get("authority_class"),
            "current_relation": r.get("current_relation"),
            "detail_available": r.get("detail_available"),
            "semantic_score": round(score, 8),
            "matched_concepts": matched,
        })

    return {
        "projection_authoritative": False,
        "semantic_mode": MODE,
        "embedding_claim": False,
        "semantic_score_is_authority": False,
        "query": query,
        "query_concepts": sorted(query_concepts),
        "filters": filters,
        "candidate_count": len(candidates),
        "result_count": len(results),
        "results": results,
    }


def _parse_filters(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid filter {value!r}; expected key=value")
        key, expected = value.split("=", 1)
        if not key.strip() or not expected.strip():
            raise ValueError(f"invalid filter {value!r}; expected non-empty key=value")
        out[key.strip()] = expected.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--filter", action="append", default=[])
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()
    if args.limit < 1:
        ap.error("--limit must be >= 1")

    payload, records = load_fixture(args.fixture)
    errors = validate_fixture(payload, records)
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    result = semantic_search(
        records,
        args.query,
        filters=_parse_filters(args.filter),
        limit=args.limit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
