#!/usr/bin/env python3
"""Risk-aware research depth routing for TAKY Mining Engine.

Depth is driven by outcome impact, evidence risk, urgency, uncertainty, and
research cost rather than raw frontier counts alone.
"""
from __future__ import annotations

DEPTH_ORDER={"D0":0,"D1":1,"D2":2,"D3":3,"D4":4}

def _bounded(value,default=0.0):
    try: return max(0.0,min(1.0,float(value)))
    except (TypeError,ValueError): return default

def route_depth(task:dict)->dict:
    ceiling=str(task.get("max_research_depth","D4")).upper()
    if ceiling not in DEPTH_ORDER: ceiling="D4"
    if task.get("known_complete"):
        return {"research_depth_decision":"D0","routing_score":0.0,"depth_ceiling":ceiling,"reason":"KNOWN_COMPLETE","factors":{}}

    explicit={
        "goal_impact":_bounded(task.get("goal_impact"),0.5 if task.get("goal") else 0.0),
        "evidence_risk":_bounded(task.get("evidence_risk"),0.0),
        "urgency":_bounded(task.get("urgency"),1.0 if task.get("freshness_required") else 0.0),
        "uncertainty":_bounded(task.get("uncertainty"),0.0),
        "decision_risk":_bounded(task.get("decision_risk"),1.0 if task.get("high_stakes") else 0.0),
        "research_cost":_bounded(task.get("research_cost"),0.0),
    }
    # Structural signals raise uncertainty/evidence risk but do not determine depth alone.
    unknown=len(task.get("unknown",[]) or [])
    conflict=len(task.get("conflict",[]) or [])
    advanced=len(task.get("advanced_requirements",[]) or [])
    structural_uncertainty=min(1.0,(unknown + advanced*.5)/4.0)
    structural_risk=min(1.0,conflict/2.0)
    explicit["uncertainty"]=max(explicit["uncertainty"],structural_uncertainty)
    explicit["evidence_risk"]=max(explicit["evidence_risk"],structural_risk)

    score=(
        .27*explicit["goal_impact"]+
        .23*explicit["evidence_risk"]+
        .18*explicit["uncertainty"]+
        .14*explicit["decision_risk"]+
        .10*explicit["urgency"]-
        .08*explicit["research_cost"]
    )
    # A real new goal should receive at least a light research pass.
    if task.get("goal") and task.get("auto_research",True):
        score=max(score,0.16)

    if score < .16: depth="D0"
    elif score < .34: depth="D1"
    elif score < .53: depth="D2"
    elif score < .72: depth="D3"
    else: depth="D4"

    if DEPTH_ORDER[depth] > DEPTH_ORDER[ceiling]: depth=ceiling
    return {
        "research_depth_decision":depth,
        "routing_score":round(score,4),
        "depth_ceiling":ceiling,
        "reason":"RISK_AWARE_ROUTING",
        "factors":explicit,
        "structural_signals":{"unknown_count":unknown,"conflict_count":conflict,"advanced_count":advanced},
    }
