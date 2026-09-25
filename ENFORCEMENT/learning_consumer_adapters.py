#!/usr/bin/env python3
"""TAKY Learning consumer adapters V1.

Thin adapters only:
- Ready & Set consumes candidate learning actions and owns dated allocation.
- Hide & Seek emits memory observations into Learning Engine.
- Snap & Pop emits production/rubric outcomes into Learning Engine.

No app-specific UI or scheduling authority is moved into Learning Engine.
"""
from __future__ import annotations

def to_ready_planner_request(learning_result:dict, context:dict|None=None)->dict:
    context=context or {}
    action=learning_result.get("runtime",{}).get("next_learning_action") or learning_result.get("next_learning_action") or {}
    allowed=bool(action.get("planner_allocation_allowed"))
    return {
        "schema":"TAKY_READY_LEARNING_ACTION_V1",
        "accepted_for_planner":allowed,
        "child_id":context.get("child_id") or context.get("learner_id"),
        "skill_id":action.get("skill_id") or context.get("skill_id"),
        "action":action.get("action"),
        "intensity":action.get("intensity"),
        "estimated_units":action.get("estimated_units"),
        "preferred_date":None,
        "planner_date":None,
        "guards":{
            "ready_planner_owns_date":True,
            "learning_action_is_candidate":True,
            "learning_engine_does_not_write_schedule":True,
        },
    }

def hide_signal_to_observation(event:dict)->dict:
    payload=event.get("payload") or {}
    correct=payload.get("correct")
    if correct is None:
        status=str(payload.get("result") or payload.get("status") or "").upper()
        if status in {"CORRECT","SUCCESS","RECALLED"}: correct=True
        elif status in {"INCORRECT","FAIL","MISSED"}: correct=False
    return {
        "schema":"TAKY_HIDE_LEARNING_OBSERVATION_V1",
        "learner_id":event.get("child_id") or payload.get("child_id"),
        "skill_id":payload.get("skill_id") or payload.get("word") or payload.get("item_id"),
        "correct":correct,
        "assisted":bool(payload.get("assisted") or payload.get("hint_used")),
        "confusion":payload.get("confusion"),
        "strength":payload.get("strength"),
        "weakness":payload.get("weakness"),
        "spaced_evidence":payload.get("spacedEvidence") or payload.get("spaced_evidence"),
        "next_review_priority":payload.get("nextReviewPriority") or payload.get("next_review_priority"),
        "source_app":"HIDE_SEEK",
        "event_type":event.get("event_type") or event.get("type"),
        "guards":{
            "hide_does_not_schedule_long_term_review":True,
            "observation_is_not_mastery":True,
        },
    }

def snap_result_to_outcome(event:dict)->dict:
    payload=event.get("payload") or {}
    rubric=payload.get("rubric") or payload.get("rubric_result") or {}
    completed=(event.get("event_type") or event.get("type"))=="TASK_COMPLETED" or bool(payload.get("completed"))
    improvement=payload.get("evidence_of_improvement")
    if improvement is None:
        improvement=bool(rubric.get("passed") or rubric.get("improved") or payload.get("revision_improved"))
    return {
        "schema":"TAKY_SNAP_LEARNING_OUTCOME_V1",
        "learner_id":event.get("child_id") or payload.get("child_id"),
        "skill_id":payload.get("skill_id") or payload.get("concept_skill_target"),
        "completed":bool(completed),
        "evidence_of_improvement":bool(improvement),
        "needed_assistance":bool(payload.get("needed_assistance") or payload.get("help_used")),
        "error_persisted":bool(payload.get("error_persisted")),
        "production_ref":payload.get("production_ref") or payload.get("event_id"),
        "rubric_ref":payload.get("rubric_ref"),
        "source_app":"SNAP_POP",
        "guards":{
            "production_completion_is_not_global_mastery":True,
            "rubric_result_is_contextual_evidence":True,
        },
    }
