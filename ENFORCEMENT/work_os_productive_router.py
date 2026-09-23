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
DRAWING_USER_FACING={"PREVIEW","FINAL","USER_FACING"}
DRAWING_ONE_OFF={"PYTHON_ONE_OFF","REPORTLAB_ONE_OFF","GENERIC_HTML_ONE_OFF","UNREGISTERED_SCRIPT"}
HANDOFF_MODES={"RESUME","RETROSPECTIVE","SURGERY"}

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
    if kind=="DRAWING_PRODUCTION":
        artifact=str(record.get("artifact_class","EXPERIMENT")).upper()
        producer=str(record.get("producer_type","")).upper()
        engine_available=record.get("engine_available") is True
        bypass_used=record.get("bypass_used") is True
        if artifact in DRAWING_USER_FACING:
            if engine_available and bypass_used:
                return {"pass":False,"detected":["ENGINE_AVAILABLE_BYPASS_USED_GOVERNANCE_FAILURE"],"route":{"mode":"SURGERY"}}
            if producer in DRAWING_ONE_OFF or record.get("registered_engine") is not True:
                return {"pass":False,"detected":["USER_FACING_REQUIRES_AUTHORIZED_ENGINE"],"route":{"mode":"HOLD"}}
            return {"pass":True,"route":{"destination":"AUTHORIZED_DRAWING_ENGINE","requires":"EVIDENCE_BACKED_L7_L8_ADMISSION","artifact_class":artifact}}
        return {"pass":True,"route":{"destination":"INTERNAL_EXPERIMENT_OR_DIAGNOSTIC","user_facing":False,"artifact_class":artifact}}
    if kind=="HANDOFF_MODE":
        mode=str(record.get("mode","")).upper()
        if mode not in HANDOFF_MODES:
            return {"pass":False,"detected":["INVALID_HANDOFF_MODE"]}
        failures=int(record.get("structural_failure_count",0) or 0)
        engine_bypass=record.get("engine_bypass") is True
        user_debugger=record.get("user_as_debugger") is True
        if mode=="RESUME" and (failures>=3 or engine_bypass or user_debugger):
            return {"pass":False,"detected":["RESUME_FORBIDDEN_SURGERY_REQUIRED"],"route":{"mode":"SURGERY"}}
        return {"pass":True,"route":{"mode":mode}}
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
