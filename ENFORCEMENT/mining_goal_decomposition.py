#!/usr/bin/env python3
"""Conservative goal decomposition for TAKY Mining Engine.

Turns a user goal into minimum research dimensions without inventing domain
facts. It may classify explicit requirements and derive generic research
dimensions, but never fabricates hidden requirements.
"""
from __future__ import annotations
import re

GENERIC_FOUNDATION=("definition","baseline","constraints")
GENERIC_ADVANCED=("implementation","edge_cases")
GENERIC_ALTERNATIVES=("alternatives",)

def _clean(v):
    return re.sub(r"\s+"," ",str(v or "").strip())

def _slug(prefix,text):
    body=re.sub(r"[^A-Za-z0-9가-힣]+","_",text).strip("_").lower()
    return f"{prefix}_{body[:48]}" if body else prefix

def decompose(task:dict)->dict:
    goal=_clean(task.get("goal"))
    explicit=[_clean(x) for x in task.get("requirements",[]) or [] if _clean(x)]
    critical=[_clean(x) for x in task.get("critical_requirements",[]) or [] if _clean(x)]
    foundation=[_clean(x) for x in task.get("foundation_requirements",[]) or [] if _clean(x)]
    advanced=[_clean(x) for x in task.get("advanced_requirements",[]) or [] if _clean(x)]
    alternatives=[_clean(x) for x in task.get("alternative_requirements",[]) or [] if _clean(x)]

    # Generic dimensions are research scaffolding only; they are not asserted facts.
    if task.get("derive_generic_dimensions",True):
        if not foundation:
            foundation=[f"{goal}: {x}" for x in GENERIC_FOUNDATION if goal]
        if not advanced and task.get("implementation_or_action_goal",True):
            advanced=[f"{goal}: {x}" for x in GENERIC_ADVANCED if goal]
        if not alternatives and task.get("alternatives_required",False):
            alternatives=[f"{goal}: {x}" for x in GENERIC_ALTERNATIVES if goal]

    frontier=[]
    groups={"critical":critical,"foundation":foundation,"advanced":advanced,"alternatives":alternatives,"explicit":explicit}
    ids={k:[] for k in groups}
    seen=set()
    kind_map={"critical":"CRITICAL","foundation":"FOUNDATION","advanced":"ADVANCED","alternatives":"ALTERNATIVE","explicit":"REQUIREMENT"}
    for group,items in groups.items():
        for text in items:
            key=(group,text)
            if key in seen: continue
            seen.add(key)
            fid=_slug(group,text)
            ids[group].append(fid)
            frontier.append({"id":fid,"kind":kind_map[group],"question":text,"origin":"EXPLICIT" if group in {"critical","explicit"} or text in (task.get(f"{group}_requirements",[]) or []) else "GENERIC_SCAFFOLD"})

    return {
        "schema":"TAKY_MINING_GOAL_DECOMPOSITION_V1",
        "goal":goal,
        "frontier":frontier,
        "critical_frontier_ids":ids["critical"],
        "foundation_frontier_ids":ids["foundation"],
        "advanced_frontier_ids":ids["advanced"],
        "alternative_frontier_ids":ids["alternatives"],
        "explicit_requirement_ids":ids["explicit"],
        "guards":{
            "generic_dimensions_are_not_domain_facts":True,
            "no_hidden_requirement_fabrication":True,
            "user_intent_authority_preserved":True,
        },
    }

def apply_to_task(task:dict)->dict:
    d=decompose(task)
    out=dict(task)
    for k in ("critical_frontier_ids","foundation_frontier_ids","advanced_frontier_ids","alternative_frontier_ids"):
        if not out.get(k): out[k]=d[k]
    out["decomposed_frontier"]=d["frontier"]
    out["goal_decomposition"]=d
    return out
