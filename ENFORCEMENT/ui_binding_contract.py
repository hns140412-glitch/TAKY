#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_UI_BINDING_CONTRACT_V1"
VALID_APPS={"READY_SET","HIDE_SEEK","SNAP_POP"}

def validate_registry(reg:dict)->list[str]:
    e=[]
    if reg.get("schema")!=SCHEMA:e.append("SCHEMA_INVALID")
    if reg.get("app_id") not in VALID_APPS:e.append("APP_ID_INVALID")
    slots=reg.get("slots")
    if not isinstance(slots,list) or not slots:return e+["SLOTS_MISSING"]
    seen=set()
    for i,s in enumerate(slots):
        sid=str(s.get("slot_id","")).strip()
        if not sid or sid in seen:e.append(f"SLOT_{i}_ID_INVALID_OR_DUPLICATE")
        seen.add(sid)
        if not str(s.get("surface","")).strip():e.append(f"{sid}:SURFACE_MISSING")
        roles=s.get("allowed_presence_roles")
        if not isinstance(roles,list) or not roles:e.append(f"{sid}:ALLOWED_ROLES_MISSING")
        if s.get("approved_only") is not True:e.append(f"{sid}:APPROVED_ONLY_REQUIRED")
        if s.get("design_gate_required") is not True:e.append(f"{sid}:DESIGN_GATE_REQUIRED")
        if s.get("allow_generation") is not False:e.append(f"{sid}:GENERATION_MUST_BE_FALSE")
    return e

def bind(reg:dict,vm:dict)->dict:
    errors=validate_registry(reg)
    if errors:return {"pass":False,"error":"REGISTRY_INVALID","detected":errors}
    if vm.get("ok") is not True:return {"pass":False,"error":"VIEW_MODEL_INVALID"}
    if vm.get("app_id")!=reg.get("app_id"):return {"pass":False,"error":"APP_BINDING_MISMATCH"}
    if vm.get("asset_generation_allowed") is not False:return {"pass":False,"error":"GENERATION_PATH_FORBIDDEN"}
    slots={s["slot_id"]:s for s in reg["slots"]}
    assignments=[];rejected=[]
    requested=vm.get("characters") or []
    for c in requested:
        role=c.get("presence_role")
        slot=next((s for s in reg["slots"] if role in s.get("allowed_presence_roles",[]) and s["slot_id"] not in {a["slot_id"] for a in assignments}),None)
        if not slot:
            rejected.append({"character_id":c.get("character_id"),"reason":"NO_COMPATIBLE_SLOT"})
            continue
        assignments.append({
          "slot_id":slot["slot_id"],
          "surface":slot["surface"],
          "character_id":c.get("character_id"),
          "visual_id":c.get("visual_id"),
          "presence_role":role,
          "action":c.get("action"),
          "dialogue_level":c.get("dialogue_level"),
          "runtime_eligible":c.get("runtime_eligible") is True
        })
    if not assignments:return {"pass":False,"error":"NO_BINDABLE_CHARACTER","rejected":rejected}
    return {
      "pass":True,"app_id":reg["app_id"],
      "scene_id":vm.get("scene_id"),
      "assignments":assignments,
      "rejected":rejected,
      "partial_binding":bool(rejected),
      "dom_mutation_allowed":False,
      "asset_generation_allowed":False,
      "design_gate_required":True
    }
