#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from collections import defaultdict
from pathlib import Path
from typing import Any

SOURCE_PATTERNS=[
    re.compile(r"^(?:INDEX|REFERENCE):(.+)$",re.I),
    re.compile(r"^SOURCE:(.+)$",re.I),
]

def source_id_from_ref(value:str)->str|None:
    s=str(value or "").strip()
    if not s: return None
    for p in SOURCE_PATTERNS:
        m=p.match(s)
        if m: return m.group(1).strip()
    return None

def aggregate_events(events:list[dict[str,Any]])->dict[str,dict[str,int]]:
    out=defaultdict(lambda:{
        "verified_success":0,
        "verified_failure":0,
        "recovery_success":0,
        "regression_failure":0,
        "verified_reuse":0,
    })
    for e in events:
        sid=source_id_from_ref(e.get("source_ref"))
        if not sid: continue
        payload=e.get("payload") if isinstance(e.get("payload"),dict) else {}
        stage=str(e.get("stage") or "").upper()
        if stage=="OUTCOME":
            outcome=payload.get("outcome")
            verified=payload.get("verified_target") is True or payload.get("verification_state")=="VERIFIED"
            if verified and outcome in (1,"1","SUCCESS",True):
                out[sid]["verified_success"]+=1
            elif verified and outcome in (0,"0","FAILURE",False):
                out[sid]["verified_failure"]+=1
            if payload.get("recovery_success") is True:
                out[sid]["recovery_success"]+=1
            if payload.get("regression_failure") is True:
                out[sid]["regression_failure"]+=1
        if stage=="GROWTH" and payload.get("verified_reuse") is True:
            out[sid]["verified_reuse"]+=1
    return {k:v for k,v in out.items()}

def load_jsonl(path:Path)->list[dict[str,Any]]:
    rows=[]
    if not path.exists(): return rows
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        try:
            x=json.loads(line)
            if isinstance(x,dict): rows.append(x)
        except Exception:
            continue
    return rows

def main():
    p=argparse.ArgumentParser(description="Materialize non-authoritative DATA INDEX outcome-utility sidecar from GROW lineage.")
    p.add_argument("--lineage",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    utility=aggregate_events(load_jsonl(a.lineage))
    payload={
        "schema":"TAKY_DATA_INDEX_OUTCOME_UTILITY_V1",
        "authoritative":False,
        "ranking_role":"SECONDARY_ONLY",
        "precedence":"EXACT -> CURRENT -> OUTCOME_UTILITY -> RETRIEVAL_SCORE",
        "source_count":len(utility),
        "by_source_id":utility,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"source_count":len(utility),"output":str(a.output)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
