#!/usr/bin/env python3
"""Minimal executable Work OS productive router."""
from __future__ import annotations
import argparse, json
from pathlib import Path

PIPELINE=["GOAL","DISCOVER","BUILD","VERIFY","SHIP","LEARN"]
VIS={
    "comparison":"TABLE",
    "process_flow":"FLOW_DIAGRAM",
    "numeric_relation":"CHART",
    "interface_structure":"WIREFRAME",
    "spatial_location":"MAP",
    "simple_explanation":"TEXT",
}
EVIDENCE={"OBSERVED","INFERRED","EXPERIMENTAL","UNVERIFIED"}

def route(record: dict) -> dict:
    kind=str(record.get("kind","")).upper()
    if kind=="PIPELINE":
        stage=str(record.get("stage","")).upper()
        if stage not in PIPELINE:
            return {"pass":False,"detected":["INVALID_PIPELINE_STAGE"]}
        i=PIPELINE.index(stage)
        return {"pass":True,"route":{"stage":stage,"next_stage":PIPELINE[i+1] if i+1<len(PIPELINE) else None}}
    if kind=="IDEA":
        for k in ("idea","novelty","usefulness","cost","evidence_state"):
            if k not in record or record.get(k) in ("",None):
                return {"pass":False,"detected":[f"MISSING:{k}"]}
        if str(record["evidence_state"]).upper() not in EVIDENCE:
            return {"pass":False,"detected":["INVALID_EVIDENCE_STATE"]}
        return {
            "pass":True,
            "route":{
                "destination":"_LAB",
                "canonical":False,
                "idea":record["idea"],
                "novelty":record["novelty"],
                "usefulness":record["usefulness"],
                "cost":record["cost"],
                "evidence_state":str(record["evidence_state"]).upper()
            }
        }
    if kind=="VISUALIZATION":
        relation=str(record.get("relation_type","")).strip().lower()
        return {"pass":True,"route":{"visualization":VIS.get(relation,"TEXT"),"relation_type":relation or "unspecified"}}
    return {"pass":False,"detected":["UNKNOWN_ROUTE_KIND"]}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("record",type=Path)
    a=ap.parse_args()
    rec=json.loads(a.record.read_text(encoding="utf-8"))
    out=route(rec)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
