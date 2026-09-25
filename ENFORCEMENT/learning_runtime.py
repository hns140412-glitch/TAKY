#!/usr/bin/env python3
"""TAKY Learning Engine Runtime V1.

Shared learning-domain runtime:
Index evidence -> learner-state interpretation -> strategy selection ->
next learning action proposal -> outcome observation.

It does NOT own dated scheduling (Planner), app UX, source acquisition,
or automatic policy promotion.
"""
from __future__ import annotations
import hashlib

ALLOWED_EVIDENCE_CLASSES={"READY_WITH_GUARDS","CONDITIONAL","REFERENCE_ONLY"}
HOLD_CLASSES={"HOLD","REVIEW_REQUIRED"}

def _id(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def interpret_learner_state(context:dict, evidence:list[dict], observations:list[dict])->dict:
    obs=observations or []
    correct=sum(1 for x in obs if x.get("correct") is True)
    incorrect=sum(1 for x in obs if x.get("correct") is False)
    assisted=sum(1 for x in obs if x.get("assisted") is True)
    total=max(1,correct+incorrect)
    accuracy=correct/total if (correct+incorrect) else None
    repeated_error=incorrect>=2
    assistance_dependency=assisted>=2
    confidence="LOW" if repeated_error else "MEDIUM" if incorrect else "HIGH" if correct else "UNKNOWN"
    return {
        "schema":"TAKY_LEARNER_STATE_V1",
        "learner_id":context.get("learner_id"),
        "skill_id":context.get("skill_id"),
        "accuracy":round(accuracy,4) if accuracy is not None else None,
        "correct_count":correct,
        "incorrect_count":incorrect,
        "assisted_count":assisted,
        "repeated_error":repeated_error,
        "assistance_dependency":assistance_dependency,
        "confidence":confidence,
        "evidence_count":len(evidence or []),
        "guards":{
            "state_is_contextual_not_global_ability":True,
            "single_session_not_mastery_proof":True,
        },
    }

def _usable_evidence(evidence:list[dict])->list[dict]:
    out=[]
    for row in evidence or []:
        cls=str(row.get("authorization_class") or row.get("utilization_class") or "REFERENCE_ONLY").upper()
        if cls in HOLD_CLASSES:
            continue
        if cls in ALLOWED_EVIDENCE_CLASSES or cls=="DIRECT_USE_READY":
            out.append(row)
    return out

def select_strategy(context:dict, state:dict, evidence:list[dict])->dict:
    usable=_usable_evidence(evidence)
    if not usable:
        return {
            "strategy":"HOLD_FOR_EVIDENCE",
            "reason":"NO_USABLE_EVIDENCE",
            "intensity":"NONE",
            "requires_review":True,
        }
    if state.get("repeated_error"):
        strategy="TARGETED_REMEDIATION"
        intensity="HIGH"
    elif state.get("assistance_dependency"):
        strategy="SUPPORTED_RECALL"
        intensity="MEDIUM"
    elif state.get("accuracy") is not None and state["accuracy"]>=0.8:
        strategy="SPACED_REVIEW"
        intensity="LOW"
    else:
        strategy="GUIDED_PRACTICE"
        intensity="MEDIUM"
    return {
        "strategy":strategy,
        "intensity":intensity,
        "reason":"LEARNER_STATE_AND_AVAILABLE_EVIDENCE",
        "requires_review":bool(context.get("high_impact")),
        "evidence_refs":[x.get("source_id") for x in usable if x.get("source_id")],
    }

def propose_learning_action(context:dict, state:dict, strategy:dict)->dict:
    if strategy["strategy"]=="HOLD_FOR_EVIDENCE":
        return {
            "action":"NO_LEARNING_ACTION",
            "status":"HOLD",
            "reason":"INSUFFICIENT_USABLE_EVIDENCE",
            "planner_allocation_allowed":False,
        }
    action_type={
        "TARGETED_REMEDIATION":"REMEDIATION_UNIT",
        "SUPPORTED_RECALL":"ASSISTED_RECALL_UNIT",
        "SPACED_REVIEW":"REVIEW_UNIT",
        "GUIDED_PRACTICE":"PRACTICE_UNIT",
    }[strategy["strategy"]]
    return {
        "action":action_type,
        "status":"CANDIDATE",
        "skill_id":context.get("skill_id"),
        "intensity":strategy["intensity"],
        "estimated_units":1,
        "planner_allocation_allowed":True,
        "planner_date":None,
        "guards":{
            "learning_engine_does_not_assign_date":True,
            "planner_owns_dated_allocation":True,
            "candidate_action_is_not_completed_assignment":True,
        },
    }

def run_learning_cycle(payload:dict)->dict:
    context=payload.get("context") or {}
    evidence=payload.get("evidence_candidates") or []
    observations=payload.get("observations") or []
    state=interpret_learner_state(context,evidence,observations)
    strategy=select_strategy(context,state,evidence)
    action=propose_learning_action(context,state,strategy)
    evidence_gap=None
    if strategy["strategy"]=="HOLD_FOR_EVIDENCE":
        evidence_gap={
            "type":"LEARNING_EVIDENCE_GAP",
            "skill_id":context.get("skill_id"),
            "learning_context":context.get("learning_context"),
            "desired_evidence_type":context.get("desired_evidence_type") or "learning support evidence",
            "what_existing_evidence_is_insufficient":"NO_USABLE_EVIDENCE_AFTER_POLICY_FILTER",
        }
    return {
        "schema":"TAKY_LEARNING_RUNTIME_V1",
        "cycle_id":_id(str(payload)),
        "learner_state":state,
        "strategy_selection":strategy,
        "next_learning_action":action,
        "evidence_gap":evidence_gap,
        "guards":{
            "mining_not_owned_by_learning":True,
            "indexing_not_owned_by_learning":True,
            "planner_date_authority_preserved":True,
            "no_auto_promotion":True,
            "user_not_debugger":True,
        },
    }

def evaluate_outcome(run:dict,outcome:dict)->dict:
    success=bool(outcome.get("completed")) and bool(outcome.get("evidence_of_improvement"))
    return {
        "schema":"TAKY_LEARNING_OUTCOME_OBSERVATION_V1",
        "cycle_id":run.get("cycle_id"),
        "strategy":run.get("strategy_selection",{}).get("strategy"),
        "success":success,
        "observation":{
            "completed":bool(outcome.get("completed")),
            "evidence_of_improvement":bool(outcome.get("evidence_of_improvement")),
            "needed_assistance":bool(outcome.get("needed_assistance")),
            "error_persisted":bool(outcome.get("error_persisted")),
        },
        "memory_proposal":{
            "type":"LEARNING_STRATEGY_OBSERVATION" if success else "LEARNING_FAILURE_OBSERVATION",
            "status":"CANDIDATE" if success else "OPEN",
            "promotion_allowed":False,
            "single_run_is_not_policy_change":True,
        },
    }
