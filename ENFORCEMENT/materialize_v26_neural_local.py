#!/usr/bin/env python3
"""One-shot private local materializer for TAKY V26 neural retrieval.

The V26 payload stays on the local/Drive-synced filesystem. Only derived vector,
query and receipt files are written to the requested output directory.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

from data_index_local_embedding_provider import (
    EXPECTED_DIMENSION, MODEL_ID, build_index, build_query
)
from data_index_vector_search import load_query_vector, load_vector_index, vector_scores

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--payload", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--probe-query", default="한국어 학습 자료")
    a=p.parse_args()
    if not a.payload.is_file():
        raise SystemExit("V26_PAYLOAD_NOT_FOUND")
    raw=json.loads(a.payload.read_text(encoding="utf-8-sig"))
    rows=raw.get("source_entries")
    if raw.get("schema_version")!="DATA_UTILIZATION_INDEX_V26":
        raise SystemExit("V26_SCHEMA_MISMATCH")
    if not isinstance(rows,list) or len(rows)!=679:
        raise SystemExit("V26_SOURCE_COUNT_MISMATCH")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    idxp=a.output_dir/"v26-neural-index.json"
    qp=a.output_dir/"probe-query-vector.json"
    rp=a.output_dir/"materialization-receipt.json"
    build_index(a.payload,idxp)
    build_query(a.probe_query,qp)
    idx=load_vector_index(idxp); q=load_query_vector(qp)
    if idx["provider"]["model_id"]!=q["model_id"]!=MODEL_ID:
        raise SystemExit("MODEL_ID_MISMATCH")
    if idx["provider"]["dimension"]!=q["dimension"] or q["dimension"]!=EXPECTED_DIMENSION:
        raise SystemExit("DIMENSION_MISMATCH")
    if len(idx["vectors"])!=679:
        raise SystemExit("VECTOR_SOURCE_COUNT_MISMATCH")
    scores=vector_scores(idx,q)
    if not scores:
        raise SystemExit("NO_POSITIVE_VECTOR_SCORES")
    receipt={
      "status":"PASS","source_count":679,"unique_vector_source_ids":len(idx["vectors"]),
      "model_id":idx["provider"]["model_id"],"dimension":idx["provider"]["dimension"],
      "neural_embedding_verified":True,"positive_query_scores":len(scores),
      "payload_location_exposed":False,
      "note":"V26 remained local; receipt contains no source titles, locators, or raw content."
    }
    rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=="__main__":
    main()
