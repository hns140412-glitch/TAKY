#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def _load(name,file):
    p=ROOT/file
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

adapter=_load("app_adapter","app_scene_policy_adapter.py")
scene_policy=_load("scene_policy","scene_policy_contract.py")
orchestrator=_load("orchestrator","scene_orchestrator.py")
composition=_load("composition","asset_composition_contract.py")
renderer=_load("renderer","runtime_renderer_contract.py")

def coordinate(app_adapter:dict, scene_input:dict, approved_registry:dict)->dict:
    adapted=adapter.to_scene_policy(app_adapter)
    if not adapted.get("pass"):
        return {"pass":False,"stage":"APP_POLICY","detected":adapted.get("detected",[])}
    p=adapted["policy"]
    pe=scene_policy.validate(p)
    if pe:return {"pass":False,"stage":"SCENE_POLICY","detected":pe}

    scene={**scene_input,"max_visible":p["max_visible"],"max_speaking":p["max_speaking"]}
    orch=orchestrator.orchestrate(scene)
    if not orch.get("pass"):
        return {"pass":False,"stage":"ORCHESTRATION","error":orch.get("error")}

    render_plans=[]
    rejected=[]
    for cmd in orch.get("characters",[]):
        semantic={
          **cmd,
          "pass":True,
          "generation_allowed":False,
          "asset_selection_forbidden":True,
          "asset_path":None
        }
        comp=composition.resolve(semantic,approved_registry)
        if not comp.get("pass"):
            rejected.append({
              "character_id":cmd.get("character_id"),
              "stage":"COMPOSITION",
              "error":comp.get("error"),
              "missing_roles":comp.get("missing_roles",[])
            })
            continue
        plan=renderer.render_plan(semantic,comp)
        if not plan.get("pass"):
            rejected.append({
              "character_id":cmd.get("character_id"),
              "stage":"RENDERER",
              "error":plan.get("error")
            })
            continue
        render_plans.append(plan)

    if not render_plans:
        return {
          "pass":False,"stage":"RUNTIME_RENDER",
          "error":"NO_RENDERABLE_CHARACTER",
          "scene_id":orch.get("scene_id"),
          "rejected":rejected
        }

    return {
      "pass":True,
      "schema":"TAKY_CHARACTER_RUNTIME_COORDINATOR_V1",
      "target_app":app_adapter.get("app_id"),
      "policy_id":p["policy_id"],
      "scene_id":orch.get("scene_id"),
      "visible_order":orch.get("visible_order"),
      "speaking_order":orch.get("speaking_order"),
      "foreground_character_id":orch.get("foreground_character_id"),
      "render_plans":render_plans,
      "rejected":rejected,
      "partial_render":bool(rejected),
      "generation_allowed":False,
      "production_state_mutation_allowed":False,
      "design_gate_required":True
    }
