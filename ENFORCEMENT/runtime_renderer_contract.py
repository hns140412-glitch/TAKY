#!/usr/bin/env python3
from __future__ import annotations

def render_plan(command:dict, composition:dict)->dict:
    if not command.get("pass"):
        return {"pass":False,"error":"COMMAND_INVALID"}
    if not composition.get("pass"):
        return {"pass":False,"error":"COMPOSITION_INVALID","cause":composition.get("error")}
    if command.get("character_id")!=composition.get("character_id"):
        return {"pass":False,"error":"CHARACTER_BINDING_MISMATCH"}
    if str(command.get("visual_id"))!=str(composition.get("visual_id")):
        return {"pass":False,"error":"VISUAL_ID_BINDING_MISMATCH"}
    if command.get("generation_allowed") is not False or composition.get("generation_allowed") is not False:
        return {"pass":False,"error":"UNAUTHORIZED_GENERATION_PATH"}
    pointers=composition.get("asset_pointers") or []
    if not pointers:
        return {"pass":False,"error":"NO_APPROVED_ASSET_POINTERS"}
    return {
      "pass":True,
      "renderer":"TAKY_APPROVED_POINTER_RENDERER_V1",
      "character_id":command.get("character_id"),
      "visual_id":command.get("visual_id"),
      "presence_role":command.get("presence_role"),
      "relationship_state":command.get("relationship_state"),
      "action":command.get("action"),
      "dialogue_level":command.get("dialogue_level"),
      "asset_pointers":pointers,
      "fallback_used":bool(composition.get("fallback_used")),
      "runtime_mutation_allowed":False,
      "asset_generation_allowed":False,
      "design_gate_required":True
    }
