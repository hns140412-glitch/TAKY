#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_SPECIALIST_PIPELINE_RESUME_V1"
STAGES=[
 "AUTHORITY_RESTORE",
 "GROUP_SOURCE_SHA_LOCK",
 "MEMBER_ID_REFERENCE_BINDING",
 "INDIVIDUAL_TRANSPARENT_CUTOUT",
 "INDIVIDUAL_MASK_SPEC",
 "BODY_PROP_GEAR_FINAL_ART",
 "SIX_REACTION_FINAL_ART",
 "PER_ID_PACKAGE_AUDIT",
 "UI_BINDING_AND_RENDER",
 "VIEWPORT_DEVICE_VISUAL_QA",
 "RELEASE"
]
TERMINAL={"PASS","HOLD","BLOCKED","OPEN","PARTIAL","FAILED"}

def validate(state:dict)->list[str]:
    e=[]
    if state.get("schema")!=SCHEMA:e.append("SCHEMA_INVALID")
    stages=state.get("stages")
    if not isinstance(stages,list) or not stages:return e+["STAGES_MISSING"]
    names=[x.get("name") for x in stages]
    if names!=STAGES:e.append("STAGE_ORDER_INVALID")
    for i,s in enumerate(stages):
        if s.get("status") not in TERMINAL:e.append(f"{s.get('name')}:STATUS_INVALID")
        if s.get("status")=="PASS" and not s.get("evidence_ref"):e.append(f"{s.get('name')}:PASS_WITHOUT_EVIDENCE")
        if s.get("status") in {"OPEN","PARTIAL","FAILED","BLOCKED"} and not s.get("resume_reason"):e.append(f"{s.get('name')}:RESUME_REASON_MISSING")
    return e

def next_resume(state:dict)->dict:
    errors=validate(state)
    if errors:return {"pass":False,"error":"STATE_INVALID","detected":errors}
    for s in state["stages"]:
        if s["status"]!="PASS":
            return {"pass":True,"resume_stage":s["name"],"status":s["status"],"resume_reason":s.get("resume_reason"),
                    "evidence_ref":s.get("evidence_ref"),"generation_allowed":False}
    return {"pass":True,"resume_stage":"NONE","status":"COMPLETE","generation_allowed":False}

def recover(last_good:dict,candidate:dict)->dict:
    a=validate(last_good);b=validate(candidate)
    if a:return {"pass":False,"error":"LAST_GOOD_INVALID","detected":a}
    if b:return {"pass":False,"error":"CANDIDATE_INVALID","detected":b}
    # Candidate cannot regress a previously PASS stage unless evidence changed and explicit reopen is declared.
    regress=[]
    for old,new in zip(last_good["stages"],candidate["stages"]):
        if old["status"]=="PASS" and new["status"]!="PASS" and not new.get("explicit_reopen"):
            regress.append(old["name"])
    if regress:return {"pass":False,"error":"PASS_REGRESSION_FORBIDDEN","stages":regress}
    return {"pass":True,"state":candidate}
