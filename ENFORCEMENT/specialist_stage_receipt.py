#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_SPECIALIST_STAGE_RECEIPT_V1"

def _hash(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def issue(stage_name:str,pipeline_owner:str,evidence_refs:list[str],input_hashes:list[str],output_hashes:list[str],status:str="PASS")->dict:
    if status!="PASS":return {"pass":False,"error":"ONLY_PASS_CAN_ISSUE_RECEIPT"}
    if not stage_name or not pipeline_owner:return {"pass":False,"error":"IDENTITY_MISSING"}
    if not evidence_refs:return {"pass":False,"error":"EVIDENCE_REQUIRED"}
    for h in [*(input_hashes or []),*(output_hashes or [])]:
        if len(str(h))!=64 or any(c not in "0123456789abcdefABCDEF" for c in str(h)):
            return {"pass":False,"error":"HASH_INVALID"}
    body={
      "schema":SCHEMA,"pipeline_owner":pipeline_owner,"stage_name":stage_name,"status":"PASS",
      "evidence_refs":list(evidence_refs),"input_hashes":list(input_hashes or []),"output_hashes":list(output_hashes or []),
      "production_state_owner":pipeline_owner
    }
    return {"pass":True,**body,"stage_receipt_sha256":_hash(body)}
