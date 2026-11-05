#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_EXPLORER_CREW_RELEASE_GATE_V1"
REQUIRED=[
 "asset_registry_gate",
 "runtime_contract_gate",
 "relation_behavior_gate",
 "scene_orchestration_gate",
 "ui_binding_gate",
 "design_gate",
 "interaction_gate",
 "responsive_gate",
 "device_gate",
 "recovery_gate"
]

def evaluate(status:dict)->dict:
    if status.get("schema")!=SCHEMA:
        return {"pass":False,"error":"SCHEMA_INVALID","release_candidate":False}
    missing=[];failed=[];blocked=[]
    gates=status.get("gates") or {}
    for name in REQUIRED:
        v=gates.get(name)
        if v is None:
            missing.append(name);continue
        state=v.get("state") if isinstance(v,dict) else v
        if state=="PASS":continue
        if state in {"BLOCKED","HOLD","OPEN"}:blocked.append(name)
        else:failed.append(name)
    if status.get("image_generation_hold") is True:
        blocked.append("image_generation_hold")
    if status.get("main_merge_authorized") is not True:
        blocked.append("main_merge_authorization")
    if status.get("release_approval_authorized") is not True:
        blocked.append("release_approval_authorization")
    ok=not missing and not failed and not blocked
    return {
      "pass":True,
      "release_candidate":ok,
      "pwa_ready":ok,
      "missing":missing,
      "failed":failed,
      "blocked":sorted(set(blocked)),
      "claim_ceiling":"RELEASE_CANDIDATE" if ok else "IMPLEMENTATION_VALIDATED_NOT_RELEASE_READY"
    }
