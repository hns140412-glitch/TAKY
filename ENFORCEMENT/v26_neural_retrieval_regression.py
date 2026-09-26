#!/usr/bin/env python3
"""Evidence-backed V26 retrieval regression gate.

Fixtures are derived only from records that already contain both an explicit
source_family and INDEX_L1 controlled_terms. OUT_OF_LEARNING_SCOPE records are
excluded. No model-authored relevance labels are created.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

from data_index_local_embedding_provider import build_query
from data_index_vector_search import load_query_vector, load_vector_index, vector_scores
from data_index_search import load_index, search

def fixtures(records):
    out=[]
    for r in records:
        if r.get("owner")=="OUT_OF_LEARNING_SCOPE":
            continue
        i=r.get("index_l1") or {}
        family=((i.get("classification") or {}).get("source_family") or r.get("source_family"))
        terms=(i.get("discovery") or {}).get("controlled_terms") or []
        terms=[str(x).strip() for x in terms if str(x).strip()]
        if family and terms:
            out.append({"source_id":r["source_id"],"source_family":family,"query":" ".join(terms[:4])})
    return out

def family_hit(result, family, k=10):
    return any(x.get("source_family")==family for x in result.get("results",[])[:k])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--payload",type=Path,required=True)
    ap.add_argument("--vector-index",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    records=load_index(a.payload)
    fx=fixtures(records)
    if len(fx)!=6:
        raise SystemExit(f"FIXTURE_COUNT_CHANGED__EXPECTED_6__GOT_{len(fx)}")
    idx=load_vector_index(a.vector_index)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for n,x in enumerate(fx,1):
        baseline=search(records,x["query"],limit=10,relation_depth=1)
        qp=a.output_dir/f"regression-query-{n}.json"
        build_query(x["query"],qp)
        q=load_query_vector(qp)
        scores=vector_scores(idx,q)
        neural=search(records,x["query"],limit=10,relation_depth=1,
            semantic_vector_scores=scores,
            semantic_metadata={"model_id":idx["provider"]["model_id"],"dimension":idx["provider"]["dimension"],"neural_embedding_verified":True})
        rows.append({"source_id":x["source_id"],"source_family":x["source_family"],
            "baseline_family_hit_at_10":family_hit(baseline,x["source_family"]),
            "neural_family_hit_at_10":family_hit(neural,x["source_family"]),
            "neural_channel_active":neural.get("semantic_mode")=="NEURAL_EMBEDDING_VECTOR_VERIFIED"})
    base=sum(x["baseline_family_hit_at_10"] for x in rows)
    neu=sum(x["neural_family_hit_at_10"] for x in rows)
    active=all(x["neural_channel_active"] for x in rows)
    status="PASS" if active and neu>=base else "FAIL"
    receipt={"status":status,"fixture_count":len(rows),"baseline_family_recall_at_10":base/len(rows),
        "neural_family_recall_at_10":neu/len(rows),"neural_not_worse_than_baseline":neu>=base,
        "all_neural_channels_verified":active,
        "fixture_basis":"V26 explicit source_family + index_l1.discovery.controlled_terms; OUT_OF_LEARNING_SCOPE excluded",
        "results":rows}
    out=a.output_dir/"retrieval-regression-receipt.json"
    out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False))
    if status!="PASS":
        raise SystemExit("V26_NEURAL_RETRIEVAL_REGRESSION_FAILED")

if __name__=="__main__":
    main()
