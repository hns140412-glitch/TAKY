#!/usr/bin/env python3
"""Resumable Mining Core for TAKY Mining Engine V2.

Pure orchestration/evidence logic: external search is performed by adapters.
Every cycle returns a checkpoint so interruption never requires restarting.
"""
from __future__ import annotations
import hashlib, json
from typing import Iterable
from mining_claim_relations import analyze
from mining_goal_sufficiency import evaluate as evaluate_goal_sufficiency
from mining_external_adapter import ingest_receipt
from mining_synthesis import synthesize
from mining_goal_decomposition import decompose

AUTHORITY={"PRIMARY":4,"OFFICIAL":4,"ACADEMIC":3,"IMPLEMENTATION":2,"COMMUNITY":1,"UNKNOWN":0}

def _id(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

def normalize_goal(task:dict)->dict:
    goal=str(task.get("goal","")).strip()
    return {"goal":goal,"task_family":task.get("task_family"),"goal_id":_id(f"{task.get('task_family')}|{goal}")}

def preserve_task_contract(task:dict, frontier:list[dict])->dict:
    """Keep the original required goal scope through every checkpoint/resume.

    Derive only explicitly declared required items (plus explicitly requested
    alternatives). Generic scaffolding never silently becomes a hard goal.
    Existing callers with no explicit contract preserve the legacy fallback.
    """
    contract={key:task.get(key) for key in (
        "goal","task_family","critical_frontier_ids","foundation_frontier_ids",
        "advanced_frontier_ids","alternative_frontier_ids","alternatives_required",
        "required_frontier_ids"
    ) if key in task}
    by_question={str(x.get("question")):str(x.get("id")) for x in frontier
                 if x.get("question") and x.get("id")}
    def ordered(values):
        return list(dict.fromkeys(str(x) for x in values if x))
    derived=decompose(task)
    critical=ordered(task.get("critical_frontier_ids") or
                     [by_question.get(text, fid) for text,fid in
                      zip(task.get("critical_requirements",[]) or [],
                          derived["critical_frontier_ids"])])
    if critical:
        contract["critical_frontier_ids"]=critical
    explicit=ordered(
        [by_question.get(text, fid) for text,fid in
         zip(task.get("requirements",[]) or [],derived["explicit_requirement_ids"])]
    )
    required=ordered(task.get("required_frontier_ids") or [])
    if "required_frontier_ids" in task:
        required=ordered(required+critical)
    else:
        declared=bool(any(task.get(k) for k in (
            "critical_requirements","requirements","unknown","conflict",
            "foundation_requirements","advanced_requirements",
            "alternative_requirements","critical_frontier_ids",
            "foundation_frontier_ids","advanced_frontier_ids")))
        if declared:
            required=ordered(
                critical + explicit
                + [by_question.get(str(q), str(q)) for k in (
                    "unknown","conflict","foundation_requirements",
                    "advanced_requirements"
                ) for q in (task.get(k,[]) or [])]
                + list(task.get("foundation_frontier_ids") or [])
                + list(task.get("advanced_frontier_ids") or [])
                + ([by_question.get(str(q),str(q)) for q in
                    (task.get("alternative_requirements",[]) or [])]
                   + list(task.get("alternative_frontier_ids") or [])
                   if task.get("alternatives_required") else [])
            )
    if required or "required_frontier_ids" in task:
        contract["required_frontier_ids"]=required
    # Do not retain synthetic/decomposed IDs for a dimension when the user's
    # actual selected frontier uses legacy question IDs.
    for key,field in (("foundation_frontier_ids","foundation_requirements"),
                      ("advanced_frontier_ids","advanced_requirements"),
                      ("alternative_frontier_ids","alternative_requirements")):
        if task.get(field):
            contract[key]=ordered(by_question.get(str(q),str(q))
                                  for q in task.get(field,[]) or [])
    return contract


def evidence_score(e:dict)->float:
    authority=AUTHORITY.get(str(e.get("source_class","UNKNOWN")).upper(),0)/4
    direct=1.0 if e.get("direct_support") else 0.0
    fresh=1.0 if e.get("fresh_enough",True) else 0.0
    corroborated=min(1.0,float(e.get("independent_support_count",1))/2)
    return round(.40*authority+.30*direct+.15*fresh+.15*corroborated,4)

def assess_frontier(frontier:Iterable[dict], evidence:Iterable[dict], threshold=.65)->list[dict]:
    by={}
    for row in evidence:
        fid=str(row.get("frontier_id",""))
        by.setdefault(fid,[]).append(dict(row))
    out=[]
    for item in frontier:
        fid=str(item.get("id"))
        raw=by.get(fid,[])
        # A source can have multiple publication surfaces (HTML/catalog/API JSON).
        # Provider-supplied independent_support_count is only a claim. Never
        # upgrade it beyond independently identifiable source identities.
        identities={
            str(row.get("source_identity") or row.get("source_url") or
                row.get("source_id") or "").strip()
            for row in raw
        }
        identities.discard("")
        independently_identified=len(identities)
        cap=max(1,independently_identified)
        ev=[]
        for row in raw:
            try:
                claimed=max(1,int(row.get("independent_support_count",1) or 1))
            except (TypeError,ValueError):
                claimed=1
            effective=min(claimed,cap)
            scored={**row,"claimed_independent_support_count":claimed,
                    "independent_support_count":effective,
                    "independence_checked":True}
            scored["quality_score"]=evidence_score(scored)
            ev.append(scored)
        best=max((x["quality_score"] for x in ev),default=0.0)
        relations=analyze(ev)
        conflict=relations["conflict"]
        unresolved=relations["unresolved_pairs"]
        status="CONFLICT" if conflict else "CLOSED" if best>=threshold else "OPEN"
        out.append({**item,"status":status,"best_evidence_score":best,
                    "evidence_count":len(ev),
                    "independent_source_identity_count":independently_identified,
                    "source_identity_required_for_independence":True,
                    "claim_relations":relations,
                    "unresolved_claim_pairs":unresolved})
    return out

def next_queries(assessed:list[dict])->list[dict]:
    q=[]
    for x in assessed:
        if x["status"]=="CLOSED": continue
        q.append({"frontier_id":x["id"],"query":x.get("question") or x["id"],"purpose":"RESOLVE_CONFLICT" if x["status"]=="CONFLICT" else "FILL_EVIDENCE_GAP","prefer":["PRIMARY","OFFICIAL","ACADEMIC"]})
    return q

def checkpoint(task:dict, frontier:list[dict], evidence:list[dict], previous:dict|None=None)->dict:
    task=preserve_task_contract(task,frontier)
    goal=normalize_goal(task); assessed=assess_frontier(frontier,evidence)
    open_items=[x for x in assessed if x["status"]!="CLOSED"]
    sufficiency=evaluate_goal_sufficiency(task,assessed)
    cycle=int((previous or {}).get("cycle",0))+1
    stop=not open_items and sufficiency["goal_sufficient"]
    reason="GOAL_AND_EVIDENCE_SUFFICIENT" if stop else "GOAL_GAPS_REMAIN" if not sufficiency["goal_sufficient"] else "EVIDENCE_GAPS_REMAIN"
    return {"schema":"TAKY_MINING_CORE_CHECKPOINT_V1","goal":goal,"task_contract":task,"cycle":cycle,"frontier":assessed,"evidence":evidence,"goal_sufficiency":sufficiency,"next_queries":next_queries(assessed),"stop":stop,"stop_reason":reason,"resume_key":_id(json.dumps({"g":goal["goal_id"],"c":cycle,"o":[x["id"] for x in open_items],"required":sufficiency["required_ids"]},sort_keys=True,ensure_ascii=False)),"guards":{"checkpoint_is_not_canonical":True,"external_adapter_required":True,"source_authority_preserved":True,"evidence_sufficient_is_not_goal_sufficient":True}}

def resume(checkpoint_state:dict,new_evidence:list[dict])->dict:
    task=dict(checkpoint_state.get("task_contract") or {
        "goal":checkpoint_state["goal"]["goal"],
        "task_family":checkpoint_state["goal"].get("task_family")
    })
    frontier=[{"id":x["id"],"question":x.get("question"),"kind":x.get("kind")} for x in checkpoint_state.get("frontier",[])]
    evidence=list(checkpoint_state.get("evidence",[]))+list(new_evidence)
    return checkpoint(task,frontier,evidence,checkpoint_state)


def apply_external_receipts(checkpoint_state:dict, receipts:list[dict])->dict:
    """Ingest provider-independent external receipts then resume from checkpoint."""
    new=[]; rejected=[]
    for receipt in receipts or []:
        ing=ingest_receipt(receipt)
        if ing.get("accepted"):
            new.extend(ing.get("evidence",[]))
        else:
            rejected.append({"frontier_id":receipt.get("frontier_id"),"errors":ing.get("errors",[])})
    out=resume(checkpoint_state,new)
    out["external_ingest"]={"accepted_evidence":len(new),"rejected_receipts":rejected}
    return out


def synthesize_checkpoint(checkpoint_state:dict)->dict:
    """Build trace-preserving synthesis from a Mining Core checkpoint."""
    out=synthesize(checkpoint_state)
    return {"checkpoint_resume_key":checkpoint_state.get("resume_key"),"synthesis":out}
