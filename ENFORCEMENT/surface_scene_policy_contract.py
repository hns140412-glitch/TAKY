#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_SURFACE_SCENE_POLICY_V1"

def derive(binding_registry:dict)->dict:
    app=binding_registry.get("app_id")
    slots=binding_registry.get("slots")
    if not app or not isinstance(slots,list) or not slots:
        return {"pass":False,"error":"BINDING_REGISTRY_INVALID"}
    surfaces={}
    for s in slots:
        surface=s.get("surface")
        if not surface: return {"pass":False,"error":"SURFACE_MISSING"}
        bucket=surfaces.setdefault(surface,{"slot_ids":[],"allowed_presence_roles":set()})
        bucket["slot_ids"].append(s.get("slot_id"))
        bucket["allowed_presence_roles"].update(s.get("allowed_presence_roles") or [])
    policies={}
    for surface,b in surfaces.items():
        policies[surface]={
          "schema":SCHEMA,
          "app_id":app,
          "surface":surface,
          "max_visible":len(b["slot_ids"]),
          "max_speaking":1,
          "slot_ids":b["slot_ids"],
          "allowed_presence_roles":sorted(b["allowed_presence_roles"]),
          "asset_generation_allowed":False,
          "creates_ui_slots":False,
          "design_gate_required":True
        }
    return {"pass":True,"app_id":app,"surfaces":policies}

def validate(policy:dict, binding_registry:dict)->list[str]:
    e=[]
    if policy.get("schema")!=SCHEMA:e.append("SCHEMA_INVALID")
    if policy.get("app_id")!=binding_registry.get("app_id"):e.append("APP_MISMATCH")
    slots=[s for s in binding_registry.get("slots",[]) if s.get("surface")==policy.get("surface")]
    if not slots:e.append("SURFACE_NOT_REGISTERED")
    if policy.get("max_visible")!=len(slots):e.append("MAX_VISIBLE_SLOT_COUNT_MISMATCH")
    if policy.get("max_speaking")!=1:e.append("MAX_SPEAKING_INVALID")
    if policy.get("asset_generation_allowed") is not False:e.append("GENERATION_MUST_BE_FALSE")
    if policy.get("creates_ui_slots") is not False:e.append("UI_SLOT_CREATION_FORBIDDEN")
    return e
