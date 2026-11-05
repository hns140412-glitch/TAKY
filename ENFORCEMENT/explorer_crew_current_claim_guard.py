#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path

BAD_CLAIMS={"RELEASE_READY","PWA_READY","RELEASED","COMPLETE","FULLY_IMPLEMENTED","PRODUCTION_READY"}

def validate(current:dict,release_status:dict)->list[str]:
    e=[]
    gates=(release_status.get("gates") or {})
    blockers=[
      k for k,v in gates.items()
      if (v.get("state") if isinstance(v,dict) else v)!="PASS"
    ]
    if release_status.get("image_generation_hold") is True:blockers.append("image_generation_hold")
    if release_status.get("main_merge_authorized") is not True:blockers.append("main_merge_authorization")
    if release_status.get("release_approval_authorized") is not True:blockers.append("release_approval_authorization")
    blob=json.dumps(current,ensure_ascii=False).upper()
    if blockers:
        for claim in BAD_CLAIMS:
            if re.search(r'(?<!NOT_)\b'+re.escape(claim)+r'\b',blob):
                e.append("OVERCLAIM_WITH_BLOCKERS:"+claim)
    mode=((current.get("execution_mode") or {}).get("mode"))
    if mode=="LOGIC_ONLY_HOLD":
        if (current.get("execution_mode") or {}).get("asset_generation_allowed") is not False:
            e.append("LOGIC_ONLY_HOLD_GENERATION_MUST_BE_FALSE")
        if (current.get("execution_mode") or {}).get("main_merge_authorized") is not False:
            e.append("LOGIC_ONLY_HOLD_MAIN_MERGE_MUST_BE_FALSE")
    return e

if __name__=="__main__":
    root=Path(__file__).parents[1]
    current=json.loads((root/"CURRENT"/"EXPLORER_CREW_RUNTIME_IMPLEMENTATION_CURRENT_V1.json").read_text(encoding="utf8"))
    status=json.loads((root/"CURRENT"/"EXPLORER_CREW_RELEASE_STATUS_CURRENT_V1.json").read_text(encoding="utf8"))
    errors=validate(current,status)
    print(json.dumps({"pass":not errors,"detected":errors},ensure_ascii=False,indent=2))
    raise SystemExit(1 if errors else 0)
