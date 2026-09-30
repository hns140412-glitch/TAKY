#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_SCENE_POLICY_V1"
VALID_ROLES={"CHAPTER_OWNER","MAIN","GUEST","ACTING_CREW","AMBIENT"}

def validate(p:dict)->list[str]:
    e=[]
    if p.get("schema")!=SCHEMA:e.append("SCHEMA_INVALID")
    if not str(p.get("policy_id","")).strip():e.append("POLICY_ID_MISSING")
    mv=p.get("max_visible")
    ms=p.get("max_speaking")
    if not isinstance(mv,int) or mv<1 or mv>5:e.append("MAX_VISIBLE_INVALID")
    if not isinstance(ms,int) or ms<1 or (isinstance(mv,int) and ms>mv) or ms>2:e.append("MAX_SPEAKING_INVALID")
    priority=p.get("role_priority")
    if not isinstance(priority,list) or set(priority)!=VALID_ROLES or len(priority)!=len(VALID_ROLES):
        e.append("ROLE_PRIORITY_INVALID")
    if p.get("allow_asset_generation") is not False:e.append("ASSET_GENERATION_MUST_BE_FALSE")
    if p.get("design_gate_required") is not True:e.append("DESIGN_GATE_REQUIRED")
    if p.get("unapproved_runtime_member_policy")!="EXCLUDE":
        e.append("UNAPPROVED_RUNTIME_MEMBER_POLICY_INVALID")
    if p.get("multiple_intervention_policy")!="ONE_FOREGROUND_REST_IDLE":
        e.append("INTERVENTION_POLICY_INVALID")
    return e

def apply(scene:dict,p:dict)->dict:
    errors=validate(p)
    if errors:return {"pass":False,"error":"POLICY_INVALID","detected":errors}
    out=dict(scene)
    out["max_visible"]=p["max_visible"]
    out["max_speaking"]=p["max_speaking"]
    out["policy_id"]=p["policy_id"]
    return {"pass":True,"scene":out}
