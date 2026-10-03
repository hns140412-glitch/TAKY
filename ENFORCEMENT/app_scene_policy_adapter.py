#!/usr/bin/env python3
from __future__ import annotations

REQUIRED_SCHEMA="TAKY_APP_SCENE_POLICY_ADAPTER_V1"
VALID_APPS={"READY_SET","HIDE_SEEK","SNAP_POP"}

def validate(x:dict)->list[str]:
    e=[]
    if x.get("schema")!=REQUIRED_SCHEMA:e.append("SCHEMA_INVALID")
    if x.get("app_id") not in VALID_APPS:e.append("APP_ID_INVALID")
    if not str(x.get("policy_id","")).strip():e.append("POLICY_ID_MISSING")
    if not isinstance(x.get("max_visible"),int) or not 1<=x["max_visible"]<=5:e.append("MAX_VISIBLE_INVALID")
    if not isinstance(x.get("max_speaking"),int) or not 1<=x["max_speaking"]<=2:e.append("MAX_SPEAKING_INVALID")
    if isinstance(x.get("max_visible"),int) and isinstance(x.get("max_speaking"),int) and x["max_speaking"]>x["max_visible"]:
        e.append("SPEAKING_EXCEEDS_VISIBLE")
    if x.get("asset_generation_allowed") is not False:e.append("ASSET_GENERATION_MUST_BE_FALSE")
    if x.get("unapproved_member_policy")!="EXCLUDE":e.append("UNAPPROVED_MEMBER_POLICY_INVALID")
    if x.get("design_gate_required") is not True:e.append("DESIGN_GATE_REQUIRED")
    if x.get("runtime_eligibility_required") is not True:e.append("RUNTIME_ELIGIBILITY_REQUIRED")
    if x.get("fallback_scope")!="SAME_CHARACTER_APPROVED_ONLY":e.append("FALLBACK_SCOPE_INVALID")
    return e

def to_scene_policy(x:dict)->dict:
    e=validate(x)
    if e:return {"pass":False,"detected":e}
    return {"pass":True,"policy":{
      "schema":"TAKY_SCENE_POLICY_V1",
      "policy_id":x["policy_id"],
      "max_visible":x["max_visible"],
      "max_speaking":x["max_speaking"],
      "role_priority":x["role_priority"],
      "allow_asset_generation":False,
      "design_gate_required":True,
      "unapproved_runtime_member_policy":"EXCLUDE",
      "multiple_intervention_policy":"ONE_FOREGROUND_REST_IDLE"
    }}
