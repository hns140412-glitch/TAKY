#!/usr/bin/env python3
"""Resumable Mining Core for TAKY Mining Engine V2.

Pure orchestration/evidence logic: external search is performed by adapters.
Every cycle returns a checkpoint so interruption never requires restarting.
"""
from __future__ import annotations
import hashlib, json
from typing import Iterable
from mining_claim_relations import analyze

AUTHORITY={"PRIMARY":4,"OFFICIAL":4,"ACADEMIC":3,"IMPLEMENTATION":2,"COMMUNITY":1,"UNKNOWN":0}

def _id(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

def normalize_goal(task:dict)->dict:
    goal=str(task.get("goal","")).strip()
    return {"goal":goal,"task_family":task.get("task_family"),"goal_id":_id(f"{task.get('task_family')}|{goal}")}

def evidence_score(e:dict)->float:
    authority=AUTHORITY.get(str(e.get("source_class","UNKNOWN")).upper(),0)/4
    direct=1.0 if e.get("direct_support") else 0.0
    fresh=1.0 if e.get("fresh_enough",True) else 0.0
    corroborated=min(1.0,float(e.get("independent_support_count",1))/2)
    return round(.40*authority+.30*direct+.15*fresh+.15*corroborated,4)

def assess_frontier(frontier:Iterable[dict], evidence:Iterable[dict], threshold=.65)->list[dict]:
    by={}
    for e in evidence:
        fid=str(e.get("frontier_id",""))
        by.setdefault(fid,[]).append({**e,"quality_score":evidence_score(e)})
    out=[]
    for item in frontier:
        fid=str(item.get("id"))
        ev=by.get(fid,[])
        best=max((x["quality_score"] for x in ev),default=0.0)
        relations=analyze(ev)
        conflict=relations["conflict"]
        unresolved=relations["unresolved_pairs"]
        status="CONFLICT" if conflict else "CLOSED" if best>=threshold else "OPEN"
        out.append({**item,"status":status,"best_evidence_score":best,"evidence_count":len(ev),"claim_relations":relations,"unresolved_claim_pairs":unresolved})
    return out

def next_queries(assessed:list[dict])->list[dict]:
    q=[]
    for x in assessed:
        if x["status"]=="CLOSED": continue
        q.append({"frontier_id":x["id"],"query":x.get("question") or x["id"],"purpose":"RESOLVE_CONFLICT" if x["status"]=="CONFLICT" else "FILL_EVIDENCE_GAP","prefer":["PRIMARY","OFFICIAL","ACADEMIC"]})
    return q

def checkpoint(task:dict, frontier:list[dict], evidence:list[dict], previous:dict|None=None)->dict:
    goal=normalize_goal(task); assessed=assess_frontier(frontier,evidence)
    open_items=[x for x in assessed if x["status"]!="CLOSED"]
    cycle=int((previous or {}).get("cycle",0))+1
    return {"schema":"TAKY_MINING_CORE_CHECKPOINT_V1","goal":goal,"cycle":cycle,"frontier":assessed,"evidence":evidence,"next_queries":next_queries(assessed),"stop":not open_items,"stop_reason":"EVIDENCE_SUFFICIENT" if not open_items else "EVIDENCE_GAPS_REMAIN","resume_key":_id(json.dumps({"g":goal["goal_id"],"c":cycle,"o":[x["id"] for x in open_items]},sort_keys=True,ensure_ascii=False)),"guards":{"checkpoint_is_not_canonical":True,"external_adapter_required":True,"source_authority_preserved":True}}

def resume(checkpoint_state:dict,new_evidence:list[dict])->dict:
    task={"goal":checkpoint_state["goal"]["goal"],"task_family":checkpoint_state["goal"].get("task_family")}
    frontier=[{"id":x["id"],"question":x.get("question"),"kind":x.get("kind")} for x in checkpoint_state.get("frontier",[])]
    evidence=list(checkpoint_state.get("evidence",[]))+list(new_evidence)
    return checkpoint(task,frontier,evidence,checkpoint_state)
