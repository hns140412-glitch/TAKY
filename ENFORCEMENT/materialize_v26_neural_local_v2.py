#!/usr/bin/env python3
"""Private local TAKY V26 neural materialization runner."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from data_index_local_embedding_provider import EXPECTED_DIMENSION, MODEL_ID, build_index, build_query
from data_index_vector_search import load_query_vector, load_vector_index, vector_scores
from data_index_search import load_index, search

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--probe-query", default="한국어 학습 자료")
    args = ap.parse_args()
    if not args.payload.is_file():
        raise SystemExit("V26_PAYLOAD_NOT_FOUND")
    raw = json.loads(args.payload.read_text(encoding="utf-8-sig"))
    rows = raw.get("source_entries")
    if raw.get("schema") != "TAKY_DATA_UTILIZATION_INDEX_V26":
        raise SystemExit("V26_SCHEMA_MISMATCH")
    if not isinstance(rows, list) or len(rows) != 679:
        raise SystemExit("V26_SOURCE_COUNT_MISMATCH")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    index_path = args.output_dir / "v26-neural-index.json"
    query_path = args.output_dir / "probe-query-vector.json"
    receipt_path = args.output_dir / "materialization-receipt.json"
    build_index(args.payload, index_path)
    build_query(args.probe_query, query_path)
    index = load_vector_index(index_path)
    query = load_query_vector(query_path)
    if index["provider"]["model_id"] != MODEL_ID or query["model_id"] != MODEL_ID:
        raise SystemExit("MODEL_ID_MISMATCH")
    if index["provider"]["dimension"] != EXPECTED_DIMENSION or query["dimension"] != EXPECTED_DIMENSION:
        raise SystemExit("DIMENSION_MISMATCH")
    if len(index["vectors"]) != 679:
        raise SystemExit("VECTOR_SOURCE_COUNT_MISMATCH")
    scores = vector_scores(index, query)
    if not scores:
        raise SystemExit("NO_POSITIVE_VECTOR_SCORES")
    fused = search(load_index(args.payload), args.probe_query, limit=10, relation_depth=1,
        semantic_vector_scores=scores,
        semantic_metadata={"model_id": MODEL_ID, "dimension": EXPECTED_DIMENSION, "neural_embedding_verified": True})
    if fused.get("semantic_mode") != "NEURAL_EMBEDDING_VECTOR_VERIFIED":
        raise SystemExit("VERIFIED_VECTOR_CHANNEL_NOT_ACTIVE")
    if not any(r.get("channels", {}).get("verified_neural_vector") for r in fused.get("results", [])):
        raise SystemExit("VERIFIED_VECTOR_NOT_PRESENT_IN_TOP_RESULTS")
    receipt = {"status":"PASS","source_count":679,"unique_vector_source_ids":len(index["vectors"]),
        "model_id":MODEL_ID,"dimension":EXPECTED_DIMENSION,"neural_embedding_verified":True,
        "verified_vector_channel_active":True,"payload_location_exposed":False}
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == "__main__":
    main()
