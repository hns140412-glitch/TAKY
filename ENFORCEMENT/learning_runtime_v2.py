#!/usr/bin/env python3
"""TAKY Learning Engine Runtime V2.

Separates:
1) evidence candidate visibility,
2) evidence reviewability,
3) evidence eligibility for autonomous learning action.

REFERENCE_ONLY and CONDITIONAL_USE can inform review but cannot by themselves
authorize an automatic learning action.
"""
from __future__ import annotations
import hashlib

ACTION_READY={"READY_WITH_GUARDS","DIRECT_USE_READY"}
REVIEWABLE={"READY_WITH_GUARDS","DIRECT_USE_READY","CONDITIONAL","CONDITIONAL_USE","REFERENCE_ONLY"}
BLOCKED={"HOLD","REVIEW_REQUIRED"}

def _id(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def _cls(row:dict)->str:
    return str(row.get("authorization_class") or row.get("utilization_class") or "REFERENCE_ONLY").upper()

def interpret_learner_state(context:dict,evidence:list[dict],observations:list[dict])->dict:
    obs=observations or []
    correct=sum(1 for x in obs if x.get("correct") is True)
    incorrect=sum(1 for x in obs if x.get("correct") is False)
    assisted=sum(1 for x in obs if x.get("assisted") is True)
    total=correct+incorrect
    accuracy=(correct/total) if total else None
    return {
        "schema":"TAKY_LEARNER_STATE_V2",
        "learner_id":context.get("learner_id"),
        "skill_id":context.get("skill_id"),
        "accuracy":round(accuracy,4) if accuracy is not None else None,
        "correct_count":correct,
        "incorrect_count":incorrect,
        "assisted_count":assisted,
        "repeated_error":incorrect>=2,
        "assistance_dependency":assisted>=2,
        "evidence_count":len(evidence or []),
        "guards":{"contextual_state_only":True,"single_session_not_mastery_proof":True},
    }

def select_strategy(context:dict,state:dict,evidence:list[dict])->dict:
    reviewable=[x for x in evidence or [] if _cls(x) in REVIEWABLE]
    ready=[x for x in evidence or [] if _cls(x) in ACTION_READY]
    if not reviewable:
        return {"strategy":"HOLD_FOR_EVIDENCE","reason":"NO_REVIEWABLE_EVIDENCE","intensity":"NONE","requires_review":True}
    if not ready:
        return {
            "strategy":"HOLD_FOR_REVIEW",
            "reason":"EVIDENCE_FOUND_BUT_NOT_ACTION_READY",
            "intensity":"NONE",
            "requires_review":True,
            "evidence_refs":[x.get("source_id") for x in reviewable if x.get("source_id")],
        }
    if state.get("repeated_error"):
        strategy,intensity="TARGETED_REMEDIATION","HIGH"
    elif state.get("assistance_dependency"):
        strategy,intensity="SUPPORTED_RECALL","MEDIUM"
    elif state.get("accuracy") is not None and state["accuracy"]>=0.8:
        strategy,intensity="SPACED_REVIEW","LOW"
    else:
        strategy,intensity="GUIDED_PRACTICE","MEDIUM"
    return {
        "strategy":strategy,
        "intensity":intensity,
        "reason":"LEARNER_STATE_AND_ACTION_READY_EVIDENCE",
        "requires_review":bool(context.get("high_impact")),
        "evidence_refs":[x.get("source_id") for x in ready if x.get("source_id")],
    }

def propose_learning_action(context:dict,strategy:dict)->dict:
    if strategy["strategy"] in {"HOLD_FOR_EVIDENCE","HOLD_FOR_REVIEW"}:
        return {
            "action":"NO_LEARNING_ACTION",
            "status":"HOLD",
            "reason":strategy["reason"],
            "planner_allocation_allowed":False,
            "planner_date":None,
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
        "guards":{"planner_owns_dated_allocation":True,"candidate_action_is_not_completed_assignment":True},
    }

def run_learning_cycle(payload:dict)->dict:
    context=payload.get("context") or {}
    evidence=payload.get("evidence_candidates") or []
    observations=payload.get("observations") or []
    state=interpret_learner_state(context,evidence,observations)
    strategy=select_strategy(context,state,evidence)
    action=propose_learning_action(context,strategy)
    gap=None
    if strategy["strategy"]=="HOLD_FOR_EVIDENCE":
        gap={"type":"LEARNING_EVIDENCE_GAP","skill_id":context.get("skill_id"),"learning_context":context.get("learning_context"),"desired_evidence_type":context.get("desired_evidence_type") or "learning support evidence","what_existing_evidence_is_insufficient":"NO_REVIEWABLE_EVIDENCE"}
    return {
        "schema":"TAKY_LEARNING_RUNTIME_V2",
        "cycle_id":_id(str(payload)),
        "learner_state":state,
        "strategy_selection":strategy,
        "next_learning_action":action,
        "evidence_gap":gap,
        "guards":{"planner_date_authority_preserved":True,"no_auto_promotion":True,"retrieval_is_not_action_permission":True},
    }

def evaluate_outcome(run:dict,outcome:dict)->dict:
    success=bool(outcome.get("completed")) and bool(outcome.get("evidence_of_improvement"))
    return {
        "schema":"TAKY_LEARNING_OUTCOME_OBSERVATION_V2",
        "cycle_id":run.get("cycle_id"),
        "strategy":run.get("strategy_selection",{}).get("strategy"),
        "success":success,
        "observation":{"completed":bool(outcome.get("completed")),"evidence_of_improvement":bool(outcome.get("evidence_of_improvement")),"needed_assistance":bool(outcome.get("needed_assistance")),"error_persisted":bool(outcome.get("error_persisted"))},
        "memory_proposal":{"type":"LEARNING_STRATEGY_OBSERVATION" if success else "LEARNING_FAILURE_OBSERVATION","status":"CANDIDATE" if success else "OPEN","promotion_allowed":False},
    }
