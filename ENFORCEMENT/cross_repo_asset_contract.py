#!/usr/bin/env python3
from __future__ import annotations

def specialist_handoff()->dict:
    return {
      "schema":"TAKY_SPECIALIST_TO_ASSET_REGISTRY_HANDOFF_V1",
      "pipeline_owner":"GUIDE_CHARACTER_PIPELINE",
      "pipeline_receipt_ref":"GUIDE_STAGE_RECEIPT",
      "asset_id":"GUIDE_VID07_BODY",
      "visual_id":"VID-07",
      "approval_status":"APPROVED",
      "binary_sha256":"a"*64,
      "runtime_url":"assets/guide/vid07/body.png",
      "asset_pointer":"TAKY-ASSETS:GUIDE:VID-07:BODY",
      "provenance":{"source":"approved-cutout"}
    }

def to_asset_export(h:dict)->dict:
    if h.get("approval_status")!="APPROVED":return {"pass":False,"error":"NOT_APPROVED"}
    forbidden=("pipeline_state","retry_count","generation_prompt","qa_queue","next_action")
    if any(k in h for k in forbidden):return {"pass":False,"error":"PRODUCTION_STATE_LEAK"}
    return {"pass":True,"asset":{
      "asset_pointer":h["asset_pointer"],"asset_id":h["asset_id"],"visual_id":h["visual_id"],
      "approval_status":"APPROVED","sha256":h["binary_sha256"],"runtime_url":h["runtime_url"],
      "producer_pointer":h["pipeline_receipt_ref"]
    }}

def app_resolve(pointer:str,registry:dict,expected_visual_id:str)->dict:
    row=next((x for x in registry.get("assets",[]) if x.get("asset_pointer")==pointer),None)
    if not row:return {"pass":False,"error":"POINTER_NOT_FOUND"}
    if row.get("approval_status")!="APPROVED":return {"pass":False,"error":"ASSET_NOT_APPROVED"}
    if row.get("visual_id")!=expected_visual_id:return {"pass":False,"error":"VISUAL_ID_MISMATCH"}
    return {"pass":True,"url":row["runtime_url"],"sha256":row["sha256"],"visual_id":row["visual_id"]}

def end_to_end()->dict:
    handoff=specialist_handoff()
    exported=to_asset_export(handoff)
    if not exported["pass"]:return exported
    registry={"assets":[exported["asset"]]}
    resolved=app_resolve(handoff["asset_pointer"],registry,handoff["visual_id"])
    if not resolved["pass"]:return resolved
    return {"pass":True,"handoff":handoff,"exported":exported["asset"],"resolved":resolved,
            "production_state_crossed_boundary":False,"generation_allowed":False}
