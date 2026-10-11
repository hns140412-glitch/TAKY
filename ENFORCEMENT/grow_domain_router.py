#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"DOMAIN"/"GROW_DOMAIN_REGISTRY.json"

def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def normalize(value):
    text=str(value or "").strip().lower()
    text=re.sub(r"[\s&\-]+","_",text)
    return re.sub(r"_+","_",text).strip("_")

def _index_revision(path:Path):
    m=re.fullmatch(r"TAKY_GROW_CURRENT_INDEX_(\d{4}-\d{2}-\d{2})(?:_R(\d+))?\.json",path.name)
    if not m:
        return ("0000-00-00",-1)
    return (m.group(1),int(m.group(2) or 1))

def route(event:dict, registry:dict|None=None)->dict:
    registry=registry or load_registry()
    fields={k:normalize(event.get(k)) for k in ("domain","source_app","task_family","artifact_type","subject","owner")}
    field_values={v for v in fields.values() if v}
    word_tokens=set()
    for value in field_values:
        word_tokens.update(x for x in value.split("_") if x)
    explicit=normalize(event.get("grow_domain")).upper()
    if explicit in registry["domains"]:
        return {"ok":True,"grow_domain":explicit,"reason":"EXPLICIT_VALID_DOMAIN","authority_transfer":False}

    scores={}
    for domain,cfg in registry["domains"].items():
        score=0
        matches=[]
        for token in cfg.get("scope",[]):
            t=normalize(token)
            if not t:
                continue
            if t in field_values:
                score+=2 if fields.get("domain")==t else 1
                matches.append(token)
            elif "_" not in t and t in word_tokens:
                score+=1
                matches.append(token)
        scores[domain]=(score,matches)

    best=max(scores,key=lambda x:scores[x][0])
    best_score=scores[best][0]
    tied=[k for k,v in scores.items() if v[0]==best_score]
    if best_score<=0 or len(tied)>1:
        return {"ok":False,"grow_domain":None,"reason":"GROW_DOMAIN_AMBIGUOUS_OR_UNKNOWN",
                "candidates":{k:{"score":v[0],"matches":v[1]} for k,v in scores.items()},
                "authority_transfer":False}
    return {"ok":True,"grow_domain":best,"reason":"SCOPE_MATCH",
            "matches":scores[best][1],"authority_transfer":False}

def validate_registry(registry:dict|None=None)->dict:
    r=registry or load_registry()
    issues=[]
    if r.get("owner")!="TAKY_GROW_CORE": issues.append("GROW_CORE_OWNER_INVALID")
    domains=r.get("domains") or {}
    for required in ("ARCHI_GROW","LEARNING_GROW","SYSTEM_GROW"):
        if required not in domains: issues.append("REQUIRED_GROW_DOMAIN_MISSING:"+required)
    owners=[str(v.get("domain_owner") or "") for v in domains.values()]
    if len(set(owners))!=len(owners): issues.append("DOMAIN_OWNER_COLLISION")
    shared=r.get("shared_core") or {}
    if shared.get("does_not_own") is None: issues.append("SHARED_CORE_BOUNDARY_MISSING")
    current_index=str(shared.get("current_index") or "").strip()
    if not current_index:
        issues.append("GROW_CURRENT_INDEX_MISSING")
    else:
        current_path=ROOT/current_index
        if not current_path.exists():
            issues.append("GROW_CURRENT_INDEX_NOT_FOUND")
        else:
            indexes=list((ROOT/"CURRENT"/"TAKY").glob("TAKY_GROW_CURRENT_INDEX_*.json"))
            if indexes:
                latest=max(indexes,key=_index_revision)
                if current_path.resolve()!=latest.resolve():
                    issues.append("GROW_CURRENT_INDEX_STALE")
    return {"ok":not issues,"issues":issues,"domain_count":len(domains)}

if __name__=="__main__":
    print(json.dumps(validate_registry(),ensure_ascii=False,indent=2))
