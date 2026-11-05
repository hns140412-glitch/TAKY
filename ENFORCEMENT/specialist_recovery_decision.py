#!/usr/bin/env python3
from __future__ import annotations

def decide(resume_state:dict,chain:dict,last_good_pointer:str|None=None)->dict:
    if resume_state.get("pass") is not True:
        return {"pass":False,"error":"RESUME_STATE_INVALID"}
    if chain.get("pass") is not True:
        return {"pass":False,"error":"STAGE_CHAIN_INVALID"}
    rs=resume_state.get("resume_stage")
    cs=chain.get("resume_stage")
    if rs=="NONE" and cs=="NONE":
        return {"pass":True,"action":"COMPLETE","generation_allowed":False}
    if rs!=cs:
        return {"pass":True,"action":"HOLD","reason":"RESUME_SOURCE_DISAGREEMENT","resume_state_stage":rs,"chain_stage":cs,
                "rollback_pointer":last_good_pointer,"generation_allowed":False}
    if resume_state.get("status") in {"FAILED","BLOCKED"}:
        return {"pass":True,"action":"RECOVER","resume_stage":rs,"rollback_pointer":last_good_pointer,"generation_allowed":False}
    return {"pass":True,"action":"RESUME","resume_stage":rs,"rollback_pointer":last_good_pointer,"generation_allowed":False}
