#!/usr/bin/env python3
"""Verified neural-vector retrieval channel for TAKY search projection.

This module never generates embeddings and never guesses whether a vector is
semantic. It only accepts an explicit vector index and query vector that both
declare a verified neural embedding model, matching model_id and dimension.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

VECTOR_INDEX_SCHEMA = "TAKY_NEURAL_VECTOR_INDEX_V1"
QUERY_VECTOR_SCHEMA = "TAKY_NEURAL_QUERY_VECTOR_V1"


class VectorContractError(ValueError):
    pass


def _finite_vector(value: Any, dimension: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != dimension:
        raise VectorContractError(f"{label}_DIMENSION_MISMATCH")
    out: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)) or not math.isfinite(float(item)):
            raise VectorContractError(f"{label}_NONFINITE")
        out.append(float(item))
    if not any(abs(x) > 0 for x in out):
        raise VectorContractError(f"{label}_ZERO_VECTOR")
    return out


def load_vector_index(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != VECTOR_INDEX_SCHEMA:
        raise VectorContractError("VECTOR_INDEX_SCHEMA_INVALID")
    provider = payload.get("provider")
    if not isinstance(provider, dict):
        raise VectorContractError("VECTOR_PROVIDER_MISSING")
    if provider.get("neural_embedding_verified") is not True:
        raise VectorContractError("NEURAL_EMBEDDING_NOT_VERIFIED")
    model_id = str(provider.get("model_id") or "").strip()
    dimension = provider.get("dimension")
    if not model_id:
        raise VectorContractError("VECTOR_MODEL_ID_MISSING")
    if not isinstance(dimension, int) or dimension < 2:
        raise VectorContractError("VECTOR_DIMENSION_INVALID")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise VectorContractError("VECTOR_ENTRIES_INVALID")

    vectors: dict[str, list[float]] = {}
    for row in entries:
        if not isinstance(row, dict):
            raise VectorContractError("VECTOR_ENTRY_INVALID")
        source_id = str(row.get("source_id") or "").strip()
        if not source_id:
            raise VectorContractError("VECTOR_SOURCE_ID_MISSING")
        if source_id in vectors:
            raise VectorContractError("VECTOR_SOURCE_ID_DUPLICATE")
        vectors[source_id] = _finite_vector(row.get("vector"), dimension, "VECTOR")

    return {
        "schema": VECTOR_INDEX_SCHEMA,
        "provider": {
            "provider_type": provider.get("provider_type") or "EXPLICIT_PRECOMPUTED_NEURAL_EMBEDDING",
            "model_id": model_id,
            "dimension": dimension,
            "normalized": bool(provider.get("normalized", False)),
            "neural_embedding_verified": True,
            "generated_at": provider.get("generated_at"),
            "source": provider.get("source"),
        },
        "vectors": vectors,
    }


def load_query_vector(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != QUERY_VECTOR_SCHEMA:
        raise VectorContractError("QUERY_VECTOR_SCHEMA_INVALID")
    if payload.get("neural_embedding_verified") is not True:
        raise VectorContractError("QUERY_NEURAL_EMBEDDING_NOT_VERIFIED")
    model_id = str(payload.get("model_id") or "").strip()
    dimension = payload.get("dimension")
    if not model_id:
        raise VectorContractError("QUERY_MODEL_ID_MISSING")
    if not isinstance(dimension, int) or dimension < 2:
        raise VectorContractError("QUERY_DIMENSION_INVALID")
    vector = _finite_vector(payload.get("vector"), dimension, "QUERY_VECTOR")
    return {
        "schema": QUERY_VECTOR_SCHEMA,
        "model_id": model_id,
        "dimension": dimension,
        "vector": vector,
        "neural_embedding_verified": True,
    }


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    an = math.sqrt(sum(x * x for x in a))
    bn = math.sqrt(sum(y * y for y in b))
    if not an or not bn:
        return 0.0
    return dot / (an * bn)


def vector_scores(
    vector_index: dict[str, Any],
    query_vector: dict[str, Any],
    *,
    allowed_source_ids: set[str] | None = None,
) -> dict[str, float]:
    provider = vector_index.get("provider") or {}
    if provider.get("neural_embedding_verified") is not True:
        raise VectorContractError("NEURAL_EMBEDDING_NOT_VERIFIED")
    if query_vector.get("neural_embedding_verified") is not True:
        raise VectorContractError("QUERY_NEURAL_EMBEDDING_NOT_VERIFIED")
    if provider.get("model_id") != query_vector.get("model_id"):
        raise VectorContractError("VECTOR_MODEL_MISMATCH")
    if provider.get("dimension") != query_vector.get("dimension"):
        raise VectorContractError("VECTOR_DIMENSION_MISMATCH")

    query = query_vector["vector"]
    scores: dict[str, float] = {}
    for source_id, vector in (vector_index.get("vectors") or {}).items():
        if allowed_source_ids is not None and source_id not in allowed_source_ids:
            continue
        score = _cosine(query, vector)
        if score > 0:
            scores[source_id] = score
    return scores


def metadata(vector_index: dict[str, Any]) -> dict[str, Any]:
    provider = vector_index.get("provider") or {}
    return {
        "semantic_mode": "NEURAL_EMBEDDING_VECTOR_VERIFIED",
        "provider_type": provider.get("provider_type"),
        "model_id": provider.get("model_id"),
        "dimension": provider.get("dimension"),
        "neural_embedding_verified": provider.get("neural_embedding_verified") is True,
    }
