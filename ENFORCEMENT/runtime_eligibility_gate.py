#!/usr/bin/env python3
from __future__ import annotations

VALID_STATES={
 "SOURCE_LOCK_READY",
 "AWAITING_INDEPENDENT_CUTOUT_SHA",
 "INDEPENDENT_CUTOUT_SHA_LOCKED_MASK_SPEC_OPEN",
 "ART_PRODUCTION_OPEN_NOT_AUTO_GENERATED",
 "APPROVED_RUNTIME_ASSET"
}

def evaluate(entry:dict)->dict:
    state=entry.get("production_state")
    if state not in VALID_STATES:
        return {"pass":False,"error":"PRODUCTION_STATE_INVALID","runtime_eligible":False}
    source_ready=state in {
      "SOURCE_LOCK_READY","INDEPENDENT_CUTOUT_SHA_LOCKED_MASK_SPEC_OPEN",
      "ART_PRODUCTION_OPEN_NOT_AUTO_GENERATED","APPROVED_RUNTIME_ASSET"
    }
    approved_pointer_ready=(
      state=="APPROVED_RUNTIME_ASSET"
      and bool(entry.get("approved_asset_pointer"))
      and bool(entry.get("approved_asset_sha256"))
      and entry.get("approval_status")=="APPROVED"
    )
    runtime_eligible=approved_pointer_ready
    return {
      "pass":True,
      "character_id":entry.get("character_id"),
      "visual_id":entry.get("visual_id"),
      "production_state":state,
      "source_ready":source_ready,
      "approved_pointer_ready":approved_pointer_ready,
      "runtime_eligible":runtime_eligible,
      "generation_allowed":False,
      "reason":"APPROVED_POINTER_READY" if runtime_eligible else "PRODUCTION_NOT_RUNTIME_APPROVED"
    }
