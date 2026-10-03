#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_CHARACTER_SCENE_ROUTE_V1"
APPS={"READY_SET","HIDE_SEEK","SNAP_POP"}

def route(target_app:str,scene_plan:dict)->dict:
    if target_app not in APPS:
        return {"pass":False,"error":"TARGET_APP_INVALID"}
    if not isinstance(scene_plan,dict) or scene_plan.get("pass") is not True:
        return {"pass":False,"error":"SCENE_PLAN_INVALID"}
    if scene_plan.get("generation_allowed") is not False:
        return {"pass":False,"error":"GENERATION_PATH_FORBIDDEN"}
    if scene_plan.get("asset_selection_allowed") is not False:
        return {"pass":False,"error":"ASSET_SELECTION_BOUNDARY_VIOLATION"}
    return {
      "schema":SCHEMA,
      "pass":True,
      "target_app":target_app,
      "scene_plan":{**scene_plan,"target_app":target_app},
      "cross_app_broadcast":False,
      "requires_target_adapter":True
    }
