#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_REGISTRY_VERSION_CONTRACT_V1"

def compare(current:dict,incoming:dict)->dict:
    if current.get("schema")!=incoming.get("schema"):
        return {"pass":False,"error":"SCHEMA_FAMILY_MISMATCH"}
    cv=int(current.get("version",0));iv=int(incoming.get("version",0))
    if iv<cv:return {"pass":False,"error":"REGISTRY_DOWNGRADE_FORBIDDEN","current":cv,"incoming":iv}
    if iv==cv and incoming.get("content_sha256")!=current.get("content_sha256"):
        return {"pass":False,"error":"SAME_VERSION_CONTENT_DRIFT"}
    return {"pass":True,"current":cv,"incoming":iv,"migration_required":iv>cv}

def migration_plan(current:dict,incoming:dict)->dict:
    c=compare(current,incoming)
    if not c.get("pass"):return c
    return {"pass":True,"migration_required":c["migration_required"],
      "from_version":c["current"],"to_version":c["incoming"],
      "activation_mode":"STAGED_VALIDATE_THEN_PROMOTE" if c["migration_required"] else "NOOP",
      "rollback_pointer_required":c["migration_required"]}
