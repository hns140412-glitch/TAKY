#!/usr/bin/env python3
"""Outcome-driven growth loop for TAKY Mining Engine.

Converts real run outcomes into advisory strategy/failure observations.
No single outcome can auto-promote a strategy or auto-resolve a failure.
"""
from __future__ import annotations

def _bounded(v,default=0.0):
    try:return max(0.0,min(1.0,float(v)))
    except (TypeError,ValueError):return default

def outcome_quality(outcome:dict)->dict:
    accuracy=_bounded(outcome.get("accuracy"))
    usefulness=_bounded(outcome.get("usefulness"))
    completeness=_bounded(outcome.get("completeness"))
    efficiency=_bounded(outcome.get("efficiency"))
    user_correction=_bounded(outcome.get("user_correction_rate"))
    score=.30*accuracy+.30*usefulness+.20*completeness+.15*efficiency+.05*(1-user_correction)
    return {"score":round(score,4),"factors":{"accuracy":accuracy,"usefulness":usefulness,"completeness":completeness,"efficiency":efficiency,"user_correction_rate":user_correction}}

def propose_growth(run:dict,outcome:dict)->dict:
    quality=outcome_quality(outcome)
    success=bool(outcome.get("success")) and quality["score"]>=float(outcome.get("success_threshold",.75))
    family=run.get("task_family") or run.get("plan",{}).get("task_family")
    goal=run.get("goal") or run.get("plan",{}).get("goal")
    route=run.get("selected_route") or run.get("plan",{}).get("selected_route")
    if success:
        action={"type":"STRATEGY_OBSERVATION","status":"CANDIDATE","task_family":family,"goal_pattern":goal,"route_signature":route,"quality_score":quality["score"],"repeat_validation_required":True,"promotion_allowed":False}
    else:
        action={"type":"FAILURE_OBSERVATION","status":"OPEN","task_family":family,"goal_pattern":goal,"route_signature":route,"quality_score":quality["score"],"failure_reason":outcome.get("failure_reason") or "OUTCOME_BELOW_THRESHOLD","new_evidence_required":True,"auto_resolution_allowed":False}
    return {"schema":"TAKY_MINING_GROWTH_PROPOSAL_V1","outcome_quality":quality,"proposal":action,"guards":{"single_run_auto_promotion":False,"single_run_auto_failure_resolution":False,"current_authority_unchanged":True}}

def aggregate_strategy_observations(observations:list[dict],min_successes:int=3,min_average:float=.82)->dict:
    rows=[x for x in observations if x.get("type")=="STRATEGY_OBSERVATION" and x.get("status")=="CANDIDATE"]
    if not rows:return {"eligible_for_review":False,"reason":"NO_CANDIDATE_OBSERVATIONS","count":0,"average_quality":0.0}
    avg=sum(float(x.get("quality_score",0)) for x in rows)/len(rows)
    families={x.get("task_family") for x in rows}
    eligible=len(rows)>=min_successes and avg>=min_average and len(families)==1
    return {"eligible_for_review":eligible,"reason":"REVIEW_ELIGIBLE" if eligible else "MORE_VALIDATION_REQUIRED","count":len(rows),"average_quality":round(avg,4),"task_family":next(iter(families)) if len(families)==1 else None}
