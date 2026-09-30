#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA="TAKY_CHARACTER_BEHAVIOR_V1"
VALID_ROLES={"MAIN","GUEST","AMBIENT","CHAPTER_OWNER","ACTING_CREW"}
VALID_REL={"FIRST_ENCOUNTER","KNOWN","FAMILIAR","TRUSTED"}
VALID_DIALOGUE={"SILENT","SHORT","HINT","COACH","CELEBRATE"}

ACTION_PARTS={
 "IDLE":["BODY","FACE"],
 "READ_BOOK":["BODY","FACE","HAND","PROP"],
 "READ_MAP":["BODY","FACE","HAND","PROP"],
 "WRITE_NOTE":["BODY","FACE","HAND","PROP"],
 "USE_RADIO":["BODY","FACE","HAND","EQUIPMENT"],
 "CHEER":["BODY","FACE","ARM"],
 "THINK":["BODY","FACE"],
 "POINT":["BODY","FACE","ARM","HAND"]
}

def select_character(state:dict)->dict:
    chars=state.get("characters",[])
    if not chars:return {"pass":False,"error":"NO_CHARACTERS"}
    eligible=[c for c in chars if c.get("available",True)]
    if not eligible:return {"pass":False,"error":"NO_AVAILABLE_CHARACTER"}

    owner=state.get("chapter_owner")
    if owner:
        c=next((x for x in eligible if x.get("character_id")==owner),None)
        if c:return {"character":c,"role":"CHAPTER_OWNER"}

    main=state.get("main_character_id")
    if main:
        c=next((x for x in eligible if x.get("character_id")==main),None)
        if c:return {"character":c,"role":"MAIN"}

    eligible=sorted(eligible,key=lambda x:(x.get("recent_count",0),x.get("character_id","")))
    return {"character":eligible[0],"role":"AMBIENT"}

def resolve_action(state:dict,character:dict,role:str)->str:
    requested=state.get("requested_action")
    if requested in ACTION_PARTS:return requested
    mode=str(state.get("mode","")).upper()
    need_hint=bool(state.get("needs_hint"))
    completed=bool(state.get("just_completed"))
    if completed:return "CHEER"
    if need_hint:return "POINT"
    if mode in {"TRACE","RECALL"}:return "READ_BOOK"
    if mode in {"LINK","CORE"}:return "THINK"
    if state.get("radio_input_active"):return "USE_RADIO"
    return "IDLE"

def dialogue_level(state:dict,role:str,relation:str)->str:
    if role=="AMBIENT":return "SILENT"
    if state.get("just_completed"):return "CELEBRATE"
    if state.get("needs_hint"):
        return "COACH" if relation=="TRUSTED" else "HINT"
    if relation=="FIRST_ENCOUNTER":
        return "SHORT"
    return "SHORT"

def run(state:dict)->dict:
    picked=select_character(state)
    if not picked.get("character"):return picked
    c=picked["character"];role=picked["role"]
    relation=c.get("relationship_state","KNOWN")
    if relation not in VALID_REL:relation="KNOWN"
    action=resolve_action(state,c,role)
    return {
      "schema":SCHEMA,
      "pass":True,
      "character_id":c.get("character_id"),
      "visual_id":c.get("visual_id"),
      "presence_role":role,
      "relationship_state":relation,
      "action":action,
      "dialogue_level":dialogue_level(state,role,relation),
      "required_roles":ACTION_PARTS[action],
      "asset_selection_forbidden":True,
      "asset_path":None,
      "generation_allowed":False
    }

def validate_command(x:dict)->list[str]:
    e=[]
    if x.get("schema")!=SCHEMA:e.append("SCHEMA_INVALID")
    if not x.get("pass"):e.append("COMMAND_NOT_PASS")
    if x.get("presence_role") not in VALID_ROLES:e.append("ROLE_INVALID")
    if x.get("relationship_state") not in VALID_REL:e.append("RELATIONSHIP_INVALID")
    if x.get("dialogue_level") not in VALID_DIALOGUE:e.append("DIALOGUE_INVALID")
    if x.get("action") not in ACTION_PARTS:e.append("ACTION_INVALID")
    if x.get("required_roles")!=ACTION_PARTS.get(x.get("action"),[]):e.append("REQUIRED_ROLES_MISMATCH")
    if x.get("asset_selection_forbidden") is not True:e.append("ASSET_SELECTION_BOUNDARY_MISSING")
    if x.get("asset_path") not in (None,""):e.append("BEHAVIOR_ENGINE_SELECTED_ASSET")
    if x.get("generation_allowed") is not False:e.append("UNAUTHORIZED_GENERATION")
    if not x.get("character_id"):e.append("CHARACTER_ID_MISSING")
    if not x.get("visual_id"):e.append("VISUAL_ID_MISSING")
    return e

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    r=sp.add_parser("run");r.add_argument("state")
    v=sp.add_parser("validate");v.add_argument("command")
    a=ap.parse_args()
    if a.cmd=="run":
        out=run(json.loads(Path(a.state).read_text(encoding="utf-8")))
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0 if out.get("pass") else 1
    x=json.loads(Path(a.command).read_text(encoding="utf-8"))
    e=validate_command(x);print(json.dumps({"pass":not e,"detected":e},ensure_ascii=False,indent=2));return 1 if e else 0
if __name__=="__main__":raise SystemExit(main())
