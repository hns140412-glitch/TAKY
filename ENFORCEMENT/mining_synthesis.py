#!/usr/bin/env python3
"""Evidence synthesis for TAKY Mining Engine.

Transforms resolved Mining Core evidence into foundation, advanced, alternatives
and recommendation candidates without collapsing unresolved conflicts.
"""
from __future__ import annotations
from collections import defaultdict

def _group_by_frontier(checkpoint:dict)->dict:
    grouped=defaultdict(list)
    for e in checkpoint.get("evidence",[]) or []:
        grouped[str(e.get("frontier_id"))].append(e)
    return grouped

def _frontier_map(checkpoint:dict)->dict:
    return {str(x.get("id")):x for x in checkpoint.get("frontier",[]) or []}

def _best_evidence(rows:list[dict])->list[dict]:
    return sorted(
        rows,
        key=lambda e:(
            float(e.get("quality_score",0) or 0),
            bool(e.get("direct_support")),
            int(e.get("independent_support_count",1) or 1),
        ),
        reverse=True,
    )

def synthesize(checkpoint:dict)->dict:
    fmap=_frontier_map(checkpoint)
    grouped=_group_by_frontier(checkpoint)
    sections={"foundation":[],"advanced":[],"alternatives":[],"critical":[],"other":[]}
    unresolved=[]
    for fid,item in fmap.items():
        status=item.get("status")
        if status!="CLOSED":
            unresolved.append({"frontier_id":fid,"status":status,"question":item.get("question")})
            continue
        kind=str(item.get("kind","")).upper()
        if kind=="FOUNDATION": bucket="foundation"
        elif kind=="ADVANCED": bucket="advanced"
        elif kind=="ALTERNATIVE": bucket="alternatives"
        elif kind=="CRITICAL": bucket="critical"
        else: bucket="other"
        evidence=_best_evidence(grouped.get(fid,[]))
        sections[bucket].append({
            "frontier_id":fid,
            "question":item.get("question"),
            "evidence_ids":[e.get("evidence_id") for e in evidence if e.get("evidence_id")],
            "claims":[e.get("claim") for e in evidence if e.get("claim")],
            "best_quality_score":max([float(e.get("quality_score",0) or 0) for e in evidence] or [float(item.get("best_evidence_score",0) or 0)]),
        })

    candidates=[]
    for alt in sections["alternatives"]:
        candidates.append({
            "candidate_id":f"candidate:{alt['frontier_id']}",
            "basis_frontier_id":alt["frontier_id"],
            "status":"CANDIDATE",
            "supporting_evidence_ids":alt["evidence_ids"],
            "promotion_allowed":False,
        })

    return {
        "schema":"TAKY_MINING_SYNTHESIS_V1",
        "sections":sections,
        "recommendation_candidates":candidates,
        "unresolved":unresolved,
        "ready_for_recommendation_review":not unresolved,
        "guards":{
            "unresolved_conflict_not_collapsed":True,
            "candidate_is_not_recommendation":True,
            "no_auto_promotion":True,
            "source_trace_preserved":True,
        },
    }
