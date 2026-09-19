#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime, timezone

def fail(msgs):
    print(json.dumps({"pass":False,"detected":msgs},ensure_ascii=False,indent=2))
    return 1

def validate_recipe(path:Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    errors=[]
    req=set(d.get("required_fields") or [])
    recipes=d.get("recipes") or []
    if not recipes: errors.append("RECIPE_REGISTRY_EMPTY")
    seen=set()
    for r in recipes:
        rid=str(r.get("recipe_id","")).strip()
        if not rid: errors.append("RECIPE_ID_MISSING"); continue
        if rid in seen: errors.append(f"DUPLICATE_RECIPE:{rid}")
        seen.add(rid)
        for k in req:
            if k not in r or r[k] in (None,"",[]):
                errors.append(f"{rid}:MISSING:{k}")
        if int(r.get("evidence_count",0)) < 1:
            errors.append(f"{rid}:NO_EVIDENCE")
        if len(r.get("source_pointers") or []) < int(r.get("evidence_count",0)):
            errors.append(f"{rid}:EVIDENCE_COUNT_EXCEEDS_POINTERS")
    return errors

def validate_cap(path:Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    errors=[]
    req=set(d.get("required_fields") or [])
    entries=d.get("entries") or []
    if not entries: errors.append("CAPABILITY_REGISTRY_EMPTY")
    seen=set()
    for e in entries:
        cid=str(e.get("capability_id","")).strip()
        if not cid: errors.append("CAPABILITY_ID_MISSING"); continue
        if cid in seen: errors.append(f"DUPLICATE_CAPABILITY:{cid}")
        seen.add(cid)
        for k in req:
            if k not in e or e[k] in (None,"",[]):
                errors.append(f"{cid}:MISSING:{k}")
        ttl=e.get("freshness_ttl_hours")
        if not isinstance(ttl,(int,float)) or ttl<=0:
            errors.append(f"{cid}:INVALID_TTL")
        try:
            datetime.fromisoformat(str(e.get("checked_at","")).replace("Z","+00:00"))
        except Exception:
            errors.append(f"{cid}:INVALID_CHECKED_AT")
    return errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--recipe",type=Path,required=True)
    ap.add_argument("--capability",type=Path,required=True)
    a=ap.parse_args()
    errors=validate_recipe(a.recipe)+validate_cap(a.capability)
    if errors: return fail(errors)
    print(json.dumps({"pass":True,"recipes":"valid","capabilities":"valid"},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
