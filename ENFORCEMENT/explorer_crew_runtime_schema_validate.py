#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path

SHA=re.compile(r"^[a-fA-F0-9]{64}$")

def validate(doc:dict,spec:dict)->list[str]:
    e=[]
    for k in spec.get("required",[]):
        if k not in doc:e.append("REQUIRED_MISSING:"+k)
    for k,v in (spec.get("constants") or {}).items():
        if doc.get(k)!=v:e.append("CONSTANT_MISMATCH:"+k)
    for k in spec.get("sha256_fields",[]):
        if k in doc and not SHA.match(str(doc.get(k,""))):e.append("SHA_INVALID:"+k)
    for k,vals in (spec.get("enum_fields") or {}).items():
        if k in doc and doc.get(k) not in vals:e.append("ENUM_INVALID:"+k)
    for k in spec.get("forbidden_fields",[]):
        if k in doc:e.append("FORBIDDEN_FIELD:"+k)
    gates=spec.get("gate_names")
    if gates:
        actual=doc.get("gates") or {}
        for g in gates:
            if g not in actual:e.append("GATE_MISSING:"+g)
            else:
                st=actual[g].get("state") if isinstance(actual[g],dict) else actual[g]
                if st not in spec.get("gate_states",[]):e.append("GATE_STATE_INVALID:"+g)
    return e

def load_specs():
    p=Path(__file__).parents[1]/"MASTER"/"EXPLORER_CREW_RUNTIME_CONTRACT_SCHEMAS_V1.json"
    return json.loads(p.read_text(encoding="utf8"))["schemas"]

if __name__=="__main__":
    print(json.dumps({"pass":True,"schemas":sorted(load_specs())},ensure_ascii=False,indent=2))
