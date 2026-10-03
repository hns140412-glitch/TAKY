#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_SPECIALIST_TO_ASSET_REGISTRY_HANDOFF_V1"

def _hash(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def create(payload:dict)->dict:
    req=("pipeline_owner","pipeline_receipt_ref","asset_id","visual_id","approval_status","binary_sha256","runtime_url")
    missing=[k for k in req if not payload.get(k)]
    if missing:return {"pass":False,"error":"FIELD_MISSING","missing":missing}
    if payload.get("approval_status")!="APPROVED":return {"pass":False,"error":"NOT_APPROVED"}
    sha=str(payload["binary_sha256"])
    if len(sha)!=64 or any(c not in "0123456789abcdefABCDEF" for c in sha):
        return {"pass":False,"error":"SHA_INVALID"}
    forbidden=("pipeline_state","retry_count","generation_prompt","qa_queue","next_action")
    leak=[k for k in forbidden if k in payload]
    if leak:return {"pass":False,"error":"PRODUCTION_STATE_LEAK","fields":leak}
    body={
      "schema":SCHEMA,
      "pipeline_owner":payload["pipeline_owner"],
      "pipeline_receipt_ref":payload["pipeline_receipt_ref"],
      "asset_id":payload["asset_id"],
      "visual_id":payload["visual_id"],
      "approval_status":"APPROVED",
      "binary_sha256":sha,
      "runtime_url":payload["runtime_url"],
      "asset_pointer":payload.get("asset_pointer"),
      "provenance":payload.get("provenance")
    }
    return {"pass":True,**body,"handoff_sha256":_hash(body)}
