#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_CONTRACT_VERSION_HANDSHAKE_V1"

def validate(declaration:dict,registry:dict)->dict:
    if declaration.get("schema")!=SCHEMA:
        return {"pass":False,"error":"DECLARATION_SCHEMA_INVALID"}
    app=declaration.get("app_id")
    req=declaration.get("requires")
    if not app or not isinstance(req,dict) or not req:
        return {"pass":False,"error":"DECLARATION_INVALID"}
    rows={x.get("id"):x for x in registry.get("contracts",[]) if isinstance(x,dict)}
    missing=[];mismatch=[]
    for cid,ver in req.items():
        row=rows.get(cid)
        if not row:
            missing.append(cid);continue
        if row.get("version")!=ver:
            mismatch.append({"contract":cid,"required":ver,"available":row.get("version")})
    return {"pass":not missing and not mismatch,"app_id":app,"missing":missing,"mismatch":mismatch,
            "compatible":not missing and not mismatch}
