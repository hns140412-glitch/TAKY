#!/usr/bin/env python3
"""TAKY rebuildable data-index search projection.

This utility is intentionally non-authoritative. It projects legacy/new index
records into a searchable in-memory view without mutating RAW, INDEX, DETAIL,
or CURRENT.

Pipeline:
structured filter -> exact -> lexical -> token-cosine fallback -> RRF
-> relation expansion -> ranked result cards

The token-cosine channel is explicitly a fallback and MUST NOT be described as
embedding/vector semantic retrieval.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

TOKEN_RE = re.compile(r"[0-9A-Za-z_\-\.]+|[가-힣]+")
RRF_K = 60.0

CORE_DISCOVERY_FIELDS = (
    "canonical_title",
    "short_summary",
    "source_family",
    "source_type",
    "authority_class",
    "controlled_terms",
    "keywords",
    "entities",
)


def _tokens(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            out.extend(_tokens(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_tokens(item))
        return out
    return [m.group(0).lower() for m in TOKEN_RE.finditer(str(value))]


def _nested(record: dict[str, Any], *path: str) -> Any:
    cur: Any = record
    for part in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Compatibility projection from legacy V24 rows or schema-contract rows."""
    index_l1 = record.get("index_l1") if isinstance(record.get("index_l1"), dict) else {}
    identity = index_l1.get("identity") if isinstance(index_l1.get("identity"), dict) else {}
    provenance = index_l1.get("provenance") if isinstance(index_l1.get("provenance"), dict) else {}
    classification = index_l1.get("classification") if isinstance(index_l1.get("classification"), dict) else {}
    discovery = index_l1.get("discovery") if isinstance(index_l1.get("discovery"), dict) else {}
    state = index_l1.get("state") if isinstance(index_l1.get("state"), dict) else {}

    relations = index_l1.get("relations") if isinstance(index_l1.get("relations"), list) else []
    relations = [r for r in relations if isinstance(r, dict) and r.get("type")]

    source_id = identity.get("source_id") or record.get("source_id")
    title = identity.get("canonical_title") or record.get("title")
    media_type = identity.get("media_type") or record.get("mime_type")
    source_family = classification.get("source_family") or record.get("source_family")
    source_type = classification.get("source_type") or record.get("source_type")
    authority_class = classification.get("authority_class") or record.get("authority_level")
    domain_facets = classification.get("domain_facets") or record.get("domain_facets") or []
    origin_type = provenance.get("origin_type") or record.get("origin_type")
    consumer_candidates = discovery.get("consumer_candidates") or record.get("consumers") or []

    # Legacy relation hints are retained as candidate relations only.
    legacy_relation_hints: list[dict[str, Any]] = []
    if record.get("duplicate_group"):
        legacy_relation_hints.append({"type": "LEGACY_DUPLICATE_GROUP", "target": record["duplicate_group"]})
    if record.get("fragment_group"):
        legacy_relation_hints.append({"type": "LEGACY_FRAGMENT_GROUP", "target": record["fragment_group"]})
    if record.get("version_relation"):
        legacy_relation_hints.append({"type": "LEGACY_VERSION_RELATION", "target": record["version_relation"]})

    normalized = {
        "source_id": source_id,
        "canonical_title": title,
        "locator": identity.get("locator") or record.get("path"),
        "media_type": media_type,
        "content_hash": identity.get("content_hash") or record.get("content_hash"),
        "source_family": source_family,
        "source_type": source_type,
        "domain_facets": domain_facets if isinstance(domain_facets, list) else [domain_facets],
        "authority_class": authority_class,
        "language": classification.get("language") or record.get("language"),
        "modality": classification.get("modality") or record.get("modality"),
        "origin_type": origin_type,
        "publisher_or_account": provenance.get("publisher_or_account") or record.get("publisher_or_account"),
        "short_summary": discovery.get("short_summary")
        or (record.get("value_statement") if isinstance(record.get("value_statement"), str) else None),
        "controlled_terms": discovery.get("controlled_terms") or record.get("controlled_terms") or [],
        "keywords": discovery.get("keywords") or record.get("keywords") or [],
        "entities": discovery.get("entities") or record.get("entities") or [],
        "consumer_candidates": consumer_candidates if isinstance(consumer_candidates, list) else [consumer_candidates],
        "relations": relations,
        "legacy_relation_hints": legacy_relation_hints,
        "index_state": state.get("index_state") or record.get("source_review_state"),
        "detail_available": state.get("detail_available") if "detail_available" in state else bool(record.get("detail_l2")),
        "stale_state": state.get("stale_state") or record.get("stale_state"),
        "review_state": state.get("review_state") or record.get("review_bucket"),
        "current_relation": state.get("current_relation") or record.get("current_relation"),
        "temporal_group": record.get("temporal_group"),
    }
    return normalized


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        raise ValueError("index payload must be object or list")
    for key in ("source_entries", "sources", "records", "entries"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    # V24-like files may store the source rows under an implementation-specific key.
    list_candidates = [
        value
        for value in payload.values()
        if isinstance(value, list)
        and value
        and all(isinstance(x, dict) for x in value[: min(5, len(value))])
        and any("source_id" in x for x in value[: min(20, len(value))])
    ]
    if len(list_candidates) == 1:
        return list_candidates[0]
    raise ValueError("could not locate source record array")


def load_index(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = [normalize_record(x) for x in _extract_records(payload)]
    return [x for x in records if x.get("source_id")]


def _matches_filter(record: dict[str, Any], key: str, expected: str) -> bool:
    aliases = {
        "family": "source_family",
        "type": "source_type",
        "authority": "authority_class",
        "domain": "domain_facets",
        "consumer": "consumer_candidates",
        "origin": "origin_type",
        "current": "current_relation",
        "media": "media_type",
    }
    key = aliases.get(key, key)
    actual = record.get(key)
    expected_l = expected.lower()
    if isinstance(actual, list):
        return any(str(v).lower() == expected_l for v in actual)
    return str(actual).lower() == expected_l if actual is not None else False


def apply_filters(records: Iterable[dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for record in records:
        if all(_matches_filter(record, key, value) for key, value in filters.items()):
            out.append(record)
    return out


def exact_scores(records: list[dict[str, Any]], query: str) -> dict[str, float]:
    q = query.strip().lower()
    if not q:
        return {}
    scores: dict[str, float] = {}
    for r in records:
        sid = str(r.get("source_id") or "").lower()
        title = str(r.get("canonical_title") or "").lower()
        family = str(r.get("source_family") or "").lower()
        score = 0.0
        if q == sid:
            score = 1.0
        elif q == title:
            score = 0.95
        elif q == family:
            score = 0.9
        elif q and q in title:
            score = 0.7
        if score:
            scores[r["source_id"]] = score
    return scores


def _search_tokens(record: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key in CORE_DISCOVERY_FIELDS:
        out.extend(_tokens(record.get(key)))
    return out


def lexical_scores(records: list[dict[str, Any]], query: str) -> dict[str, float]:
    q_tokens = _tokens(query)
    if not q_tokens or not records:
        return {}

    docs = [_search_tokens(r) for r in records]
    doc_freq: Counter[str] = Counter()
    for tokens in docs:
        doc_freq.update(set(tokens))
    avg_len = sum(len(d) for d in docs) / max(1, len(docs))
    k1, b = 1.2, 0.75

    scores: dict[str, float] = {}
    n = len(records)
    for record, tokens in zip(records, docs):
        tf = Counter(tokens)
        dl = len(tokens)
        score = 0.0
        for term in q_tokens:
            df = doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            freq = tf.get(term, 0)
            if not freq:
                continue
            denom = freq + k1 * (1 - b + b * dl / max(avg_len, 1e-9))
            score += idf * ((freq * (k1 + 1)) / denom)
        if score > 0:
            scores[record["source_id"]] = score
    return scores


def token_cosine_scores(records: list[dict[str, Any]], query: str) -> dict[str, float]:
    """Non-embedding fallback channel; exposed as TOKEN_COSINE_FALLBACK."""
    q = Counter(_tokens(query))
    if not q:
        return {}
    q_norm = math.sqrt(sum(v * v for v in q.values()))
    scores: dict[str, float] = {}
    for record in records:
        d = Counter(_search_tokens(record))
        if not d:
            continue
        dot = sum(q[t] * d.get(t, 0) for t in q)
        d_norm = math.sqrt(sum(v * v for v in d.values()))
        if dot and q_norm and d_norm:
            scores[record["source_id"]] = dot / (q_norm * d_norm)
    return scores


def _rank(scores: dict[str, float]) -> list[str]:
    return [sid for sid, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]


def rrf_fuse(channels: list[dict[str, float]]) -> dict[str, float]:
    fused: defaultdict[str, float] = defaultdict(float)
    for scores in channels:
        for rank, sid in enumerate(_rank(scores), start=1):
            fused[sid] += 1.0 / (RRF_K + rank)
    return dict(fused)


def relation_expand(
    ranked_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    fused: dict[str, float],
    depth: int = 1,
) -> dict[str, float]:
    if depth <= 0:
        return fused
    out = dict(fused)
    frontier = ranked_ids[:10]
    for _ in range(depth):
        next_frontier: list[str] = []
        for sid in frontier:
            record = by_id.get(sid)
            if not record:
                continue
            base = out.get(sid, 0.0)
            for rel in record.get("relations", []):
                target = rel.get("target")
                if target in by_id and target not in out:
                    out[target] = base * 0.35
                    next_frontier.append(target)
        frontier = next_frontier
        if not frontier:
            break
    return out


def search(
    records: list[dict[str, Any]],
    query: str,
    filters: dict[str, str] | None = None,
    limit: int = 10,
    relation_depth: int = 1,
    semantic_vector_scores: dict[str, float] | None = None,
    semantic_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters = filters or {}
    candidates = apply_filters(records, filters)
    by_id = {r["source_id"]: r for r in candidates}

    exact = exact_scores(candidates, query)
    lexical = lexical_scores(candidates, query)
    token_cosine = token_cosine_scores(candidates, query)
    vector_scores_verified = {
        sid: score
        for sid, score in (semantic_vector_scores or {}).items()
        if sid in by_id and isinstance(score, (int, float)) and score > 0
    }
    channels_for_fusion = [exact, lexical, token_cosine]
    if vector_scores_verified:
        channels_for_fusion.append(vector_scores_verified)
    fused = rrf_fuse(channels_for_fusion)
    pre_relation = _rank(fused)
    fused = relation_expand(pre_relation, by_id, fused, relation_depth)
    ranked = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))

    results = []
    for sid, score in ranked[:limit]:
        r = by_id[sid]
        results.append(
            {
                "source_id": sid,
                "title": r.get("canonical_title"),
                "source_family": r.get("source_family"),
                "source_type": r.get("source_type"),
                "authority_class": r.get("authority_class"),
                "current_relation": r.get("current_relation"),
                "detail_available": r.get("detail_available"),
                "score": round(score, 8),
                "channels": {
                    "exact": sid in exact,
                    "lexical": sid in lexical,
                    "token_cosine_fallback": sid in token_cosine,
                    "verified_neural_vector": sid in vector_scores_verified,
                    "relation_expanded": sid not in pre_relation and sid in fused,
                },
            }
        )

    vector_enabled = bool(vector_scores_verified)
    pipeline = [
        "STRUCTURED_FILTER",
        "EXACT_RETRIEVAL",
        "LEXICAL_RETRIEVAL",
        "TOKEN_COSINE_FALLBACK",
    ]
    if vector_enabled:
        pipeline.append("VERIFIED_NEURAL_VECTOR")
    pipeline.extend(["RRF", "RELATION_EXPANSION"])

    return {
        "projection_authoritative": False,
        "pipeline": pipeline,
        "semantic_mode": (
            "NEURAL_EMBEDDING_VECTOR_VERIFIED"
            if vector_enabled
            else "TOKEN_COSINE_FALLBACK__NOT_EMBEDDING_SEMANTIC"
        ),
        "semantic_metadata": semantic_metadata if vector_enabled else None,
        "query": query,
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
        key, expected = key.strip(), expected.strip()
        if not key or not expected:
            raise ValueError(f"invalid filter {value!r}; expected non-empty key=value")
        out[key] = expected
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=Path, required=True)
    ap.add_argument("--query", default="")
    ap.add_argument("--filter", action="append", default=[])
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--relation-depth", type=int, default=1)
    ap.add_argument("--vector-index", type=Path)
    ap.add_argument("--query-vector", type=Path)
    args = ap.parse_args()

    if args.limit < 1:
        ap.error("--limit must be >= 1")
    if args.relation_depth < 0:
        ap.error("--relation-depth must be >= 0")

    vector_scores_input = None
    vector_meta = None
    if bool(args.vector_index) != bool(args.query_vector):
        ap.error("--vector-index and --query-vector must be supplied together")
    if args.vector_index and args.query_vector:
        from data_index_vector_search import (
            load_query_vector,
            load_vector_index,
            metadata as vector_metadata,
            vector_scores,
        )
        vector_index = load_vector_index(args.vector_index)
        query_vector = load_query_vector(args.query_vector)
        allowed_ids = {r["source_id"] for r in load_index(args.index)}
        vector_scores_input = vector_scores(
            vector_index,
            query_vector,
            allowed_source_ids=allowed_ids,
        )
        vector_meta = vector_metadata(vector_index)

    result = search(
        load_index(args.index),
        args.query,
        filters=_parse_filters(args.filter),
        limit=args.limit,
        relation_depth=args.relation_depth,
        semantic_vector_scores=vector_scores_input,
        semantic_metadata=vector_meta,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
