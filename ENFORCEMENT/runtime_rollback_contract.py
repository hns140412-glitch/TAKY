#!/usr/bin/env python3
from __future__ import annotations

def plan(active:dict,candidate:dict,validation:dict)->dict:
    if not active.get("pointer"):return {"pass":False,"error":"ACTIVE_POINTER_MISSING"}
    if not candidate.get("pointer"):return {"pass":False,"error":"CANDIDATE_POINTER_MISSING"}
    if validation.get("pass") is True:
        return {"pass":True,"action":"PROMOTE_CANDIDATE","from":active["pointer"],"to":candidate["pointer"],
                "rollback_pointer":active["pointer"],"activation_allowed":True}
    return {"pass":True,"action":"KEEP_ACTIVE","active_pointer":active["pointer"],
            "rejected_candidate":candidate["pointer"],"activation_allowed":False,
            "rollback_pointer":active["pointer"],"reason":validation.get("error","VALIDATION_FAILED")}
