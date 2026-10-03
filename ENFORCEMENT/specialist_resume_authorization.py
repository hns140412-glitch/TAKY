#!/usr/bin/env python3
from __future__ import annotations

def authorize(decision:dict,approval:dict)->dict:
    if decision.get("pass") is not True:return {"pass":False,"error":"RECOVERY_DECISION_INVALID"}
    action=decision.get("action")
    if action in {"HOLD","COMPLETE"}:
        return {"pass":True,"authorized":False,"action":action,"reason":"NO_PRODUCTION_ACTION"}
    if approval.get("approved") is not True:
        return {"pass":True,"authorized":False,"action":action,"reason":"OWNER_APPROVAL_REQUIRED"}
    if not str(approval.get("authority_ref","")).strip():
        return {"pass":False,"error":"AUTHORITY_REF_REQUIRED"}
    return {"pass":True,"authorized":True,"action":action,"resume_stage":decision.get("resume_stage"),
            "authority_ref":approval.get("authority_ref"),"generation_allowed":False,
            "note":"Authorization permits pipeline execution only; image generation remains governed by execution mode."}
