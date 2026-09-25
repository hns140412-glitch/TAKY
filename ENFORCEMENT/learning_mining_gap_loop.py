#!/usr/bin/env python3
"""TAKY cross-engine evidence-gap loop V1.

Closes the control-flow contract:
Learning gap -> Mining plan -> new indexed evidence -> Learning re-evaluation.

This module does not perform network I/O and does not mutate canonical INDEX.
It coordinates already-authorized engine boundaries using explicit payloads.
"""
from __future__ import annotations
from learning_orchestrator import orchestrate_learning
from mining_run_orchestrator import orchestrate as orchestrate_mining

def learning_gap_to_mining_task(gap:dict, context:dict|None=None)->dict:
    context=context or {}
    query=str(gap.get("query") or gap.get("desired_evidence_type") or gap.get("learning_context") or "").strip()
    unknown=[query] if query else ["learning evidence gap"]
    return {
        "task_family":"LEARNING_ENGINE",
        "goal":f"Acquire evidence for learning gap: {query or gap.get('type','LEARNING_EVIDENCE_GAP')}",
        "unknown":unknown,
        "foundation_requirements":[gap.get("what_existing_evidence_is_insufficient")] if gap.get("what_existing_evidence_is_insufficient") else [],
        "freshness_required":bool(gap.get("minimum_freshness")),
        "minimum_authority":gap.get("minimum_authority"),
        "learning_context":gap.get("learning_context") or context.get("learning_context"),
        "skill_id":gap.get("skill_id") or context.get("skill_id"),
        "route_signature":"learning-gap:internal-index-first",
    }

def plan_from_learning_gap(learning_result:dict, memory:dict|None=None, index_rows:list[dict]|None=None)->dict:
    gap=learning_result.get("mining_request_candidate")
    if not gap:
        return {
            "schema":"TAKY_LEARNING_MINING_GAP_LOOP_V1",
            "mining_required":False,
            "reason":"NO_LEARNING_EVIDENCE_GAP",
            "mining_plan":None,
        }
    task=learning_gap_to_mining_task(gap, learning_result.get("runtime",{}).get("learner_state"))
    mining=orchestrate_mining({
        "task":task,
        "memory":memory or {},
        "index_rows":index_rows or [],
    })
    return {
        "schema":"TAKY_LEARNING_MINING_GAP_LOOP_V1",
        "mining_required":True,
        "gap":gap,
        "mining_task":task,
        "mining_plan":mining,
        "guards":{
            "learning_does_not_mine_directly":True,
            "mining_rechecks_index_before_external_search":True,
            "gap_only_handoff":True,
        },
    }

def requery_learning(original_payload:dict, updated_index_rows:list[dict])->dict:
    payload=dict(original_payload)
    payload["index_rows"]=updated_index_rows
    return {
        "schema":"TAKY_LEARNING_REQUERY_RESULT_V1",
        "learning_result":orchestrate_learning(payload),
        "guards":{
            "requery_uses_indexed_evidence":True,
            "raw_external_result_not_consumed_directly":True,
            "planner_authority_unchanged":True,
        },
    }
