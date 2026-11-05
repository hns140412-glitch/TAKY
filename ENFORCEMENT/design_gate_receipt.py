#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_DESIGN_GATE_RECEIPT_V1"

def _hash(x)->str:
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def issue(evidence:dict)->dict:
    required=("app_id","screen_id","approved_reference_sha256","runtime_render_sha256","comparison_pass")
    missing=[k for k in required if evidence.get(k) in (None,"")]
    if missing:return {"pass":False,"error":"EVIDENCE_MISSING","missing":missing}
    if evidence.get("comparison_pass") is not True:
        return {"pass":False,"error":"VISUAL_COMPARISON_FAILED"}
    for k in ("approved_reference_sha256","runtime_render_sha256"):
        v=str(evidence.get(k,""))
        if len(v)!=64 or any(c not in "0123456789abcdefABCDEF" for c in v):
            return {"pass":False,"error":"SHA_INVALID","field":k}
    body={
      "schema":SCHEMA,
      "app_id":evidence["app_id"],
      "screen_id":evidence["screen_id"],
      "approved_reference_sha256":evidence["approved_reference_sha256"],
      "runtime_render_sha256":evidence["runtime_render_sha256"],
      "comparison_method":evidence.get("comparison_method","TAKY_VISUAL_COMPARE_V1"),
      "comparison_score":evidence.get("comparison_score"),
      "threshold":evidence.get("threshold"),
      "comparison_pass":True,
      "interaction_gate_pass":evidence.get("interaction_gate_pass") is True,
      "responsive_gate_pass":evidence.get("responsive_gate_pass") is True,
      "asset_integrity_gate_pass":evidence.get("asset_integrity_gate_pass") is True
    }
    if not all([body["interaction_gate_pass"],body["responsive_gate_pass"],body["asset_integrity_gate_pass"]]):
        return {"pass":False,"error":"SUBGATE_NOT_PASS",**body}
    return {"pass":True,**body,"receipt_sha256":_hash(body)}
