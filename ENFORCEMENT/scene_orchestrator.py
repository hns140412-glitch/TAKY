#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

SCHEMA="TAKY_SCENE_ORCHESTRATION_V1"
ROLE_PRIORITY={"CHAPTER_OWNER":0,"MAIN":1,"GUEST":2,"ACTING_CREW":3,"AMBIENT":4}
VALID_ROLES=set(ROLE_PRIORITY)
VALID_DIALOGUE={"SILENT","SHORT","HINT","COACH","CELEBRATE"}

def rank_candidate(c:dict)->tuple:
    return (
      ROLE_PRIORITY.get(c.get("presence_role"),99),
      int(c.get("recent_count",0)),
      str(c.get("character_id",""))
    )

def normalize(c:dict)->dict:
    return {
      "character_id":c.get("character_id"),
      "visual_id":c.get("visual_id"),
      "presence_role":c.get("presence_role"),
      "relationship_state":c.get("relationship_state","KNOWN"),
      "action":c.get("action","IDLE"),
      "dialogue_level":c.get("dialogue_level","SILENT"),
      "required_roles":list(c.get("required_roles") or []),
      "recent_count":int(c.get("recent_count",0)),
      "runtime_eligible":bool(c.get("runtime_eligible",False))
    }

def orchestrate(scene:dict)->dict:
    candidates=[normalize(x) for x in scene.get("candidates",[]) if isinstance(x,dict)]
    candidates=[x for x in candidates if x["presence_role"] in VALID_ROLES and x["runtime_eligible"]]
    if not candidates:
        return {"schema":SCHEMA,"pass":False,"error":"NO_RUNTIME_ELIGIBLE_CANDIDATE"}

    max_visible=max(1,min(int(scene.get("max_visible",3)),5))
    max_speaking=max(1,min(int(scene.get("max_speaking",1)),2))
    sorted_candidates=sorted(candidates,key=rank_candidate)

    visible=sorted_candidates[:max_visible]
    speaking=[]
    for c in visible:
        if c["dialogue_level"]!="SILENT" and len(speaking)<max_speaking:
            speaking.append(c["character_id"])

    # Force non-selected speakers to silent without changing their physical action.
    resolved=[]
    for c in visible:
        out=dict(c)
        if c["character_id"] not in speaking:
            out["dialogue_level"]="SILENT"
        resolved.append(out)

    # Only one high-intervention action may dominate foreground.
    intervention={"POINT","USE_RADIO","CHEER"}
    active=[x for x in resolved if x["action"] in intervention]
    foreground=None
    if active:
        foreground=sorted(active,key=rank_candidate)[0]["character_id"]
        for x in resolved:
            if x["action"] in intervention and x["character_id"]!=foreground:
                x["action"]="IDLE"
                x["required_roles"]=["BODY","FACE"]

    return {
      "schema":SCHEMA,"pass":True,
      "scene_id":scene.get("scene_id"),
      "visible_order":[x["character_id"] for x in resolved],
      "speaking_order":speaking,
      "foreground_character_id":foreground or resolved[0]["character_id"],
      "characters":resolved,
      "hidden_count":max(0,len(candidates)-len(resolved)),
      "generation_allowed":False,
      "asset_selection_allowed":False,
      "design_gate_required":True
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("scene")
    a=ap.parse_args()
    out=orchestrate(json.loads(Path(a.scene).read_text(encoding="utf8")))
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out.get("pass") else 1
if __name__=="__main__":raise SystemExit(main())
