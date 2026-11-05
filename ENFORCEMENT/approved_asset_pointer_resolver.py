#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_APPROVED_ASSET_POINTER_RESOLVER_V1"

def resolve(pointer:str,registry:dict,expected_visual_id:str|None=None)->dict:
    if not isinstance(pointer,str) or not pointer.strip():
        return {"pass":False,"error":"POINTER_MISSING"}
    entries=registry.get("assets")
    if not isinstance(entries,list):
        return {"pass":False,"error":"REGISTRY_INVALID"}
    row=next((x for x in entries if x.get("asset_pointer")==pointer),None)
    if not row:
        return {"pass":False,"error":"POINTER_NOT_FOUND"}
    if row.get("approval_status")!="APPROVED":
        return {"pass":False,"error":"ASSET_NOT_APPROVED"}
    if expected_visual_id and str(row.get("visual_id"))!=str(expected_visual_id):
        return {"pass":False,"error":"VISUAL_ID_MISMATCH"}
    sha=str(row.get("sha256",""))
    if len(sha)!=64 or any(c not in "0123456789abcdefABCDEF" for c in sha):
        return {"pass":False,"error":"ASSET_SHA_INVALID"}
    url=row.get("runtime_url")
    if not isinstance(url,str) or not url.strip():
        return {"pass":False,"error":"RUNTIME_URL_MISSING"}
    return {
      "schema":SCHEMA,
      "pass":True,
      "asset_pointer":pointer,
      "asset_id":row.get("asset_id"),
      "visual_id":row.get("visual_id"),
      "sha256":sha,
      "url":url,
      "approval_status":"APPROVED",
      "producer_pointer":row.get("producer_pointer"),
      "generation_allowed":False
    }
