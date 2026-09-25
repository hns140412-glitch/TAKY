#!/usr/bin/env python3
"""Learning Engine orchestration V1.

Index retrieval -> Learning runtime.
Evidence gaps remain explicit and may be handed to Mining later.
"""
from __future__ import annotations
from learning_index_bridge import retrieve_learning_evidence
from learning_runtime import run_learning_cycle

def orchestrate_learning(payload:dict)->dict:
    request=payload.get("evidence_request") or {}
    retrieval=retrieve_learning_evidence(
        request,
        payload.get("index_rows") or [],
        semantic_scores=payload.get("semantic_scores"),
        relations=payload.get("index_relations"),
        detail_rows=payload.get("detail_rows"),
    )
    evidence=[]
    for x in retrieval.get("evidence_candidates",[]):
        row=dict(x.get("row") or {})
        row.setdefault("source_id",x.get("source_id"))
        evidence.append(row)
    runtime_payload={
        "context":payload.get("context") or {},
        "evidence_candidates":evidence,
        "observations":payload.get("observations") or [],
    }
    runtime=run_learning_cycle(runtime_payload)
    gap=runtime.get("evidence_gap") or retrieval.get("evidence_gap")
    return {
        "schema":"TAKY_LEARNING_ORCHESTRATOR_V1",
        "retrieval":retrieval,
        "runtime":runtime,
        "mining_request_candidate":gap,
        "guards":{
            "index_checked_before_mining":True,
            "learning_does_not_acquire_sources":True,
            "planner_date_authority_preserved":True,
            "mining_request_is_gap_only":True,
        },
    }
