#!/usr/bin/env python3
"""Local-only pretrained neural embedding provider for TAKY V26 retrieval.

Downloads/caches a pinned public SentenceTransformer model only when explicitly
requested. Corpus and query embeddings MUST use the same model_id and dimension.
No paid API and no remote inference provider are used.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_ID = "dragonkue/multilingual-e5-small-ko"
EXPECTED_DIMENSION = 384
VECTOR_SCHEMA = "TAKY_NEURAL_VECTOR_INDEX_V1"
QUERY_SCHEMA = "TAKY_NEURAL_QUERY_VECTOR_V1"

class LocalEmbeddingProviderError(RuntimeError):
    pass

def _load_model(model_id: str = MODEL_ID):
    if model_id != MODEL_ID:
        raise LocalEmbeddingProviderError("UNPINNED_MODEL_ID")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise LocalEmbeddingProviderError(
            "SENTENCE_TRANSFORMERS_NOT_INSTALLED__INSTALL_LOCAL_RUNTIME_DEPENDENCY"
        ) from exc
    model = SentenceTransformer(model_id)
    dim = int(model.get_sentence_embedding_dimension())
    if dim != EXPECTED_DIMENSION:
        raise LocalEmbeddingProviderError(f"MODEL_DIMENSION_MISMATCH:{dim}")
    return model

def _record_text(row: dict[str, Any]) -> str:
    idx = row.get("index_l1") or {}
    ident = idx.get("identity") or {}
    cls = idx.get("classification") or {}
    disc = idx.get("discovery") or {}
    values = [
        ident.get("canonical_title") or row.get("title"),
        cls.get("source_family") or row.get("source_family"),
        cls.get("source_type") or row.get("source_type"),
        " ".join(cls.get("domain_facets") or []),
        disc.get("short_summary"),
        " ".join(disc.get("controlled_terms") or []),
        " ".join(disc.get("keywords") or []),
    ]
    return "passage: " + " | ".join(str(x).strip() for x in values if x)

def _source_id(row: dict[str, Any]) -> str:
    idx = row.get("index_l1") or {}
    ident = idx.get("identity") or {}
    return str(ident.get("source_id") or row.get("source_id") or "").strip()

def build_index(payload_path: Path, output_path: Path) -> None:
    payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
    rows = payload.get("source_entries")
    if not isinstance(rows, list):
        raise LocalEmbeddingProviderError("SOURCE_ENTRIES_MISSING")
    source_ids = [_source_id(x) for x in rows]
    if len(rows) != 679 or len(set(source_ids)) != 679 or any(not x for x in source_ids):
        raise LocalEmbeddingProviderError("V26_SOURCE_ID_1_TO_1_FAILED")
    model = _load_model()
    vectors = model.encode(
        [_record_text(x) for x in rows],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    if tuple(vectors.shape) != (679, EXPECTED_DIMENSION):
        raise LocalEmbeddingProviderError(f"VECTOR_SHAPE_INVALID:{vectors.shape}")
    generated_at = datetime.now(timezone.utc).isoformat()
    out = {
        "schema": VECTOR_SCHEMA,
        "provider": {
            "provider_type": "LOCAL_PRETRAINED_SENTENCE_TRANSFORMER",
            "model_id": MODEL_ID,
            "dimension": EXPECTED_DIMENSION,
            "normalized": True,
            "neural_embedding_verified": True,
            "generated_at": generated_at,
            "source": "DATA_UTILIZATION_INDEX_2026-09-25_V26.json:index_l1 metadata only",
        },
        "entries": [
            {"source_id": sid, "vector": [float(v) for v in vec]}
            for sid, vec in zip(source_ids, vectors)
        ],
    }
    output_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

def build_query(query: str, output_path: Path) -> None:
    model = _load_model()
    vector = model.encode(
        ["query: " + query.strip()],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]
    out = {
        "schema": QUERY_SCHEMA,
        "model_id": MODEL_ID,
        "dimension": EXPECTED_DIMENSION,
        "neural_embedding_verified": True,
        "vector": [float(v) for v in vector],
    }
    output_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("index")
    i.add_argument("--payload", type=Path, required=True)
    i.add_argument("--output", type=Path, required=True)
    q = sub.add_parser("query")
    q.add_argument("--text", required=True)
    q.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.command == "index":
        build_index(args.payload, args.output)
    else:
        build_query(args.text, args.output)

if __name__ == "__main__":
    main()
