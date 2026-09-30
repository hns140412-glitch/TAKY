#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_SPECIALIST_STAGE_CHAIN_V1"

def validate_chain(receipts:list[dict],expected_order:list[str])->list[str]:
    e=[]
    by={r.get("stage_name"):r for r in receipts if isinstance(r,dict)}
    seen=set()
    for name in expected_order:
        r=by.get(name)
        if not r:
            e.append("MISSING_STAGE_RECEIPT:"+name)
            break
        sha=r.get("stage_receipt_sha256")
        if not isinstance(sha,str) or len(sha)!=64:
            e.append("INVALID_STAGE_RECEIPT_SHA:"+name)
            break
        if name in seen:
            e.append("DUPLICATE_STAGE:"+name)
            break
        seen.add(name)
    return e

def resumable_prefix(receipts:list[dict],expected_order:list[str])->dict:
    by={}
    duplicates=[]
    for r in receipts or []:
        if not isinstance(r,dict):continue
        name=r.get("stage_name")
        if name in by:duplicates.append(name)
        else:by[name]=r
    if duplicates:return {"pass":False,"detected":["DUPLICATE_STAGE:"+x for x in duplicates]}
    valid=[]
    for name in expected_order:
        r=by.get(name)
        if not r:break
        sha=r.get("stage_receipt_sha256")
        if not isinstance(sha,str) or len(sha)!=64:
            return {"pass":False,"detected":["INVALID_STAGE_RECEIPT_SHA:"+name]}
        valid.append(name)
    return {"pass":True,"verified_prefix":valid,"resume_stage":expected_order[len(valid)] if len(valid)<len(expected_order) else "NONE"}
