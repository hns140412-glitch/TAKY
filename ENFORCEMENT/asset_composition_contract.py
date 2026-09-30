#!/usr/bin/env python3
from __future__ import annotations
import json

ALLOWED_ROLES={"BODY","FACE","ARM","HAND","PROP","EQUIPMENT","EFFECT"}

def validate_approved_registry(reg:dict)->list[str]:
    e=[]
    chars=reg.get("characters")
    if not isinstance(chars,list):return ["CHARACTERS_INVALID"]
    seen=set()
    for i,c in enumerate(chars):
        cid=str(c.get("character_id","")).strip()
        vid=str(c.get("visual_id","")).strip()
        if not cid or cid in seen:e.append(f"CHAR_{i}_ID_INVALID_OR_DUPLICATE")
        seen.add(cid)
        if not vid:e.append(f"{cid}:VISUAL_ID_MISSING")
        if c.get("runtime_source_eligible") is not True:e.append(f"{cid}:RUNTIME_SOURCE_NOT_ELIGIBLE")
        parts=c.get("approved_parts")
        if not isinstance(parts,list):e.append(f"{cid}:APPROVED_PARTS_INVALID");continue
        for pi,p in enumerate(parts):
            if p.get("role") not in ALLOWED_ROLES:e.append(f"{cid}:PART_{pi}_ROLE_INVALID")
            if p.get("approval_state")!="APPROVED":e.append(f"{cid}:PART_{pi}_NOT_APPROVED")
            if not str(p.get("asset_pointer","")).strip():e.append(f"{cid}:PART_{pi}_POINTER_MISSING")
    return e

def resolve(command:dict, reg:dict)->dict:
    if command.get("generation_allowed") is not False:
        return {"pass":False,"error":"UNAUTHORIZED_GENERATION_REQUEST"}
    cid=command.get("character_id")
    vid=str(command.get("visual_id",""))
    chars={c.get("character_id"):c for c in reg.get("characters",[])}
    c=chars.get(cid)
    if not c:return {"pass":False,"error":"CHARACTER_NOT_REGISTERED","character_id":cid}
    if str(c.get("visual_id"))!=vid:
        return {"pass":False,"error":"VISUAL_ID_MISMATCH","character_id":cid}
    if c.get("runtime_source_eligible") is not True:
        return {"pass":False,"error":"SOURCE_NOT_RUNTIME_ELIGIBLE","character_id":cid}
    required=command.get("required_roles") or []
    action=command.get("action")
    chosen=[];missing=[]
    for role in required:
        cand=next((p for p in c.get("approved_parts",[])
                   if p.get("role")==role and p.get("approval_state")=="APPROVED"
                   and (not p.get("actions") or action in p.get("actions"))),None)
        if cand:chosen.append(cand)
        else:missing.append(role)
    if missing:
        fb=c.get("fallback")
        if isinstance(fb,dict) and fb.get("character_id")==cid:
            part=next((p for p in c.get("approved_parts",[]) if p.get("asset_pointer")==fb.get("asset_pointer") and p.get("approval_state")=="APPROVED"),None)
            if part:
                return {"pass":True,"character_id":cid,"visual_id":vid,"action":action,
                        "asset_pointers":[part["asset_pointer"]],"fallback_used":True,
                        "missing_roles":missing,"generation_allowed":False}
        return {"pass":False,"error":"APPROVED_PART_MISSING","character_id":cid,
                "missing_roles":missing,"generation_allowed":False}
    return {"pass":True,"character_id":cid,"visual_id":vid,"action":action,
            "asset_pointers":[p["asset_pointer"] for p in chosen],
            "fallback_used":False,"generation_allowed":False}
