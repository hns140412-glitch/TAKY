#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENFORCEMENT=ROOT/"ENFORCEMENT"
if str(ENFORCEMENT) not in sys.path:
    sys.path.insert(0,str(ENFORCEMENT))

from grow_review_gate import evaluate_queue

QUEUE_KEY="taky/grow/review-queue-v1"

def _store_file(store_root:Path,key:str=QUEUE_KEY)->Path:
    return store_root/(hashlib.sha256(key.encode("utf-8")).hexdigest()+".json")

def load_queue(store_root:Path)->dict:
    p=_store_file(store_root)
    if not p.exists():
        raise FileNotFoundError(f"GROW_REVIEW_QUEUE_NOT_FOUND:{p}")
    wrapper=json.loads(p.read_text(encoding="utf-8"))
    if wrapper.get("key")!=QUEUE_KEY:
        raise RuntimeError("GROW_REVIEW_QUEUE_KEY_MISMATCH")
    data=wrapper.get("data")
    if not isinstance(data,dict):
        raise RuntimeError("GROW_REVIEW_QUEUE_DATA_INVALID")
    return data

def main()->int:
    ap=argparse.ArgumentParser(description="Evaluate the durable GROW review queue without promoting anything.")
    ap.add_argument("--store-root",type=Path,required=True)
    ap.add_argument("--evidence",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()

    queue=load_queue(args.store_root.resolve())
    evidence={}
    if args.evidence:
        loaded=json.loads(args.evidence.read_text(encoding="utf-8"))
        if isinstance(loaded,dict):
            evidence=loaded.get("by_event_id") or {}

    result=evaluate_queue(queue,evidence)
    result["source_queue_key"]=QUEUE_KEY
    result["source_store_root"]=str(args.store_root.resolve())
    result["queue_authoritative"]=False
    result["writes_promotion_state"]=False

    output=args.output or (args.store_root.resolve()/"grow-review-gate-report.json")
    tmp=output.with_suffix(output.suffix+".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(output)
    print(json.dumps({
        "ok":True,
        "candidate_count":result["candidate_count"],
        "states":result["states"],
        "promotion_authorized":False,
        "output":str(output)
    },ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
