#!/usr/bin/env python3
"""TAKY Learning Growth Memory V1.

Accumulates outcome observations without auto-promoting policy.
Designed for DEEP MEMORY — LIGHT EXECUTION.
"""
from __future__ import annotations
from collections import defaultdict

def observe(run:dict,outcome_observation:dict)->dict:
    strategy=run.get("strategy_selection",{}).get("strategy")
    state=run.get("learner_state",{})
    return {
        "type":"LEARNING_STRATEGY_OBSERVATION" if outcome_observation.get("success") else "LEARNING_FAILURE_OBSERVATION",
        "status":"CANDIDATE" if outcome_observation.get("success") else "OPEN",
        "strategy":strategy,
        "skill_id":state.get("skill_id"),
        "learner_id":state.get("learner_id"),
        "success":bool(outcome_observation.get("success")),
        "needed_assistance":bool(outcome_observation.get("observation",{}).get("needed_assistance")),
        "error_persisted":bool(outcome_observation.get("observation",{}).get("error_persisted")),
        "promotion_allowed":False,
    }

def aggregate(observations:list[dict],min_runs:int=3,min_success_rate:float=.67)->dict:
    groups=defaultdict(list)
    for x in observations or []:
        if not isinstance(x,dict): continue
        key=(x.get("strategy"),x.get("skill_id"))
        groups[key].append(x)
    summaries=[]
    for (strategy,skill_id),rows in groups.items():
        n=len(rows); success=sum(1 for r in rows if r.get("success"))
        rate=success/n if n else 0
        failures=n-success
        eligible=n>=min_runs and rate>=min_success_rate and failures==0
        summaries.append({
            "strategy":strategy,
            "skill_id":skill_id,
            "runs":n,
            "successes":success,
            "failures":failures,
            "success_rate":round(rate,4),
            "eligible_for_review":eligible,
            "promotion_allowed":False,
            "reason":"REVIEW_ELIGIBLE" if eligible else "MORE_VALIDATION_REQUIRED",
        })
    return {
        "schema":"TAKY_LEARNING_GROWTH_AGGREGATE_V1",
        "summaries":summaries,
        "guards":{
            "aggregate_does_not_auto_promote":True,
            "cross_skill_generalization_forbidden":True,
            "single_run_policy_change_forbidden":True,
        },
    }
