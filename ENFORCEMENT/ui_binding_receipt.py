#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_UI_BINDING_RECEIPT_V1"

def _hash(x)->str:
    raw=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def create(binding_plan:dict)->dict:
    if not binding_plan.get("pass") and not binding_plan.get("ok"):
        return {"pass":False,"error":"BINDING_PLAN_NOT_PASS"}
    assignments=binding_plan.get("assignments") or []
    if not assignments:return {"pass":False,"error":"NO_ASSIGNMENTS"}
    rows=[]
    for a in assignments:
        if not str(a.get("selector","")).startswith("#"):
            return {"pass":False,"error":"UNSTABLE_SELECTOR"}
        rows.append({
          "slot_id":a.get("slot_id"),
          "surface":a.get("surface"),
          "selector":a.get("selector"),
          "name_selector":a.get("name_selector"),
          "text_selector":a.get("text_selector"),
          "character_id":a.get("character_id"),
          "visual_id":a.get("visual_id"),
          "presence_role":a.get("presence_role"),
          "action":a.get("action"),
          "dialogue_level":a.get("dialogue_level")
        })
    body={
      "schema":SCHEMA,
      "app_id":binding_plan.get("app_id"),
      "scene_id":binding_plan.get("scene_id"),
      "surface":binding_plan.get("surface"),
      "assignments":rows,
      "rejected":list(binding_plan.get("rejected") or []),
      "partial_binding":bool(binding_plan.get("partial_binding")),
      "dom_mutation_allowed":False,
      "asset_generation_allowed":False,
      "design_gate_required":True
    }
    return {"pass":True,**body,"receipt_sha256":_hash(body)}
