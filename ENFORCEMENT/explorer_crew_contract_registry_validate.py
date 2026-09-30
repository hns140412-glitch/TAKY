#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

def validate(reg:dict)->list[str]:
    e=[]
    if reg.get("schema")!="TAKY_EXPLORER_CREW_CONTRACT_REGISTRY_V1":e.append("SCHEMA_INVALID")
    rows=reg.get("contracts")
    if not isinstance(rows,list) or not rows:return e+["CONTRACTS_MISSING"]
    seen=set()
    for i,c in enumerate(rows):
        cid=str(c.get("id","")).strip()
        if not cid or cid in seen:e.append(f"{i}:ID_INVALID_OR_DUPLICATE")
        seen.add(cid)
        if not isinstance(c.get("version"),int) or c["version"]<1:e.append(f"{cid}:VERSION_INVALID")
        if not str(c.get("owner","")).strip():e.append(f"{cid}:OWNER_MISSING")
        if not str(c.get("producer","")).strip():e.append(f"{cid}:PRODUCER_MISSING")
        if not isinstance(c.get("consumers"),list) or not c["consumers"]:e.append(f"{cid}:CONSUMERS_MISSING")
    return e

if __name__=="__main__":
    p=Path(__file__).parents[1]/"MASTER"/"EXPLORER_CREW_CONTRACT_REGISTRY_V1.json"
    errors=validate(json.loads(p.read_text(encoding="utf8")))
    print(json.dumps({"pass":not errors,"detected":errors},ensure_ascii=False,indent=2))
    raise SystemExit(1 if errors else 0)
