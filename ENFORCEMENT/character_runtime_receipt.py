#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_CHARACTER_RUNTIME_RECEIPT_V1"

def canonical_hash(value)->str:
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def create(coordinator_result:dict)->dict:
    if not coordinator_result.get("pass"):
        return {"pass":False,"error":"COORDINATOR_RESULT_NOT_PASS"}
    plans=coordinator_result.get("render_plans") or []
    if not plans:
        return {"pass":False,"error":"NO_RENDER_PLANS"}
    chars=[]
    for p in plans:
        chars.append({
          "character_id":p.get("character_id"),
          "visual_id":p.get("visual_id"),
          "presence_role":p.get("presence_role"),
          "relationship_state":p.get("relationship_state"),
          "action":p.get("action"),
          "dialogue_level":p.get("dialogue_level"),
          "asset_pointers":list(p.get("asset_pointers") or []),
          "fallback_used":bool(p.get("fallback_used"))
        })
    body={
      "schema":SCHEMA,
      "target_app":coordinator_result.get("target_app"),
      "policy_id":coordinator_result.get("policy_id"),
      "scene_id":coordinator_result.get("scene_id"),
      "foreground_character_id":coordinator_result.get("foreground_character_id"),
      "visible_order":list(coordinator_result.get("visible_order") or []),
      "speaking_order":list(coordinator_result.get("speaking_order") or []),
      "characters":chars,
      "rejected":list(coordinator_result.get("rejected") or []),
      "partial_render":bool(coordinator_result.get("partial_render")),
      "generation_allowed":False,
      "production_state_mutation_allowed":False,
      "design_gate_required":True
    }
    return {"pass":True,**body,"receipt_sha256":canonical_hash(body)}
