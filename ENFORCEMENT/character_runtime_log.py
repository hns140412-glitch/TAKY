#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_CHARACTER_RUNTIME_LOG_V1"

def _hash(x)->str:
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def compose(runtime_receipt:dict,binding_receipt:dict,design_gate_receipt:dict|None=None)->dict:
    if runtime_receipt.get("pass") is not True:return {"pass":False,"error":"RUNTIME_RECEIPT_INVALID"}
    if binding_receipt.get("pass") is not True:return {"pass":False,"error":"BINDING_RECEIPT_INVALID"}
    if runtime_receipt.get("scene_id")!=binding_receipt.get("scene_id"):
        return {"pass":False,"error":"SCENE_RECEIPT_MISMATCH"}
    if runtime_receipt.get("target_app")!=binding_receipt.get("app_id"):
        return {"pass":False,"error":"APP_RECEIPT_MISMATCH"}
    gate_state="BLOCKED"
    gate_sha=None
    if design_gate_receipt:
        if design_gate_receipt.get("pass") is not True:return {"pass":False,"error":"DESIGN_GATE_RECEIPT_INVALID"}
        if design_gate_receipt.get("app_id")!=runtime_receipt.get("target_app"):
            return {"pass":False,"error":"DESIGN_GATE_APP_MISMATCH"}
        gate_state="PASS";gate_sha=design_gate_receipt.get("receipt_sha256")
    body={
      "schema":SCHEMA,
      "app_id":runtime_receipt.get("target_app"),
      "scene_id":runtime_receipt.get("scene_id"),
      "runtime_receipt_sha256":runtime_receipt.get("receipt_sha256"),
      "binding_receipt_sha256":binding_receipt.get("receipt_sha256"),
      "design_gate_state":gate_state,
      "design_gate_receipt_sha256":gate_sha,
      "characters":runtime_receipt.get("characters",[]),
      "bindings":binding_receipt.get("assignments",[]),
      "partial_render":runtime_receipt.get("partial_render",False),
      "partial_binding":binding_receipt.get("partial_binding",False),
      "activation_allowed":gate_state=="PASS",
      "production_state_mutation_allowed":False,
      "generation_allowed":False
    }
    return {"pass":True,**body,"log_sha256":_hash(body)}
