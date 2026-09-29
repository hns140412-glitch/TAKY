#!/usr/bin/env python3
"""Learning Engine -> shared Index Retrieval bridge.

Learning owns the learning-context request and later use decision.
This bridge only retrieves evidence candidates and emits explicit evidence gaps.
It never authorizes pedagogical use and never mutates learner state.
"""
from __future__ import annotations
from index_retrieval import retrieve

def retrieve_learning_evidence(request:dict, index_rows:list[dict], *,
                               semantic_scores=None, relations=None, detail_rows=None)->dict:
    query=str(request.get("query") or request.get("learning_context") or "").strip()
    filters=dict(request.get("filters") or {})
    if request.get("minimum_authority"):
        filters["authority_class"]=request["minimum_authority"]
    result=retrieve(
        index_rows or [],
        query,
        filters=filters,
        semantic_scores=semantic_scores,
        relations=relations,
        detail_rows=detail_rows,
        top_k=max(int(request.get("top_k",5) or 5),len(index_rows or [])),
        relation_hops=int(request.get("relation_hops",1) or 1),
    )
    minimum=int(request.get("minimum_results",1) or 1)
    primary=result.get("primary",[])
    # Discovery candidates remain visible for review, but do not satisfy a
    # Learning evidence request merely by entering a search projection.
    reviewable=[x for x in primary if str((x.get("row") or {}).get("index_state") or "").upper()
                not in {"CANDIDATE","STAGED","PENDING","HELD","REJECTED"}]
    staged=[x for x in primary if x not in reviewable]
    reviewable=reviewable[:max(0,int(request.get("top_k",5) or 5))]
    sufficient=len(reviewable)>=minimum
    gap=None if sufficient else {
        "type":"LEARNING_EVIDENCE_GAP",
        "query":query,
        "desired_evidence_type":request.get("desired_evidence_type"),
        "context":request.get("learning_context"),
        "constraints":request.get("constraints") or {},
        "minimum_authority":request.get("minimum_authority"),
        "minimum_freshness":request.get("minimum_freshness"),
        "existing_evidence_count":len(reviewable),
        "staged_candidate_count":len(staged),
        "why_insufficient":f"MINIMUM_REVIEWABLE_RESULTS_NOT_MET:{len(reviewable)}/{minimum}",
    }
    return {
        "schema":"TAKY_LEARNING_INDEX_RETRIEVAL_V1",
        "request_id":request.get("request_id"),
        "learning_context":request.get("learning_context"),
        "evidence_candidates":reviewable,
        "staged_discovery_candidates":staged,
        "relation_expansion":result.get("expanded",[]),
        "details":result.get("details",[]),
        "retrieval_counts":result.get("counts",{}),
        "evidence_sufficient_for_review":sufficient,
        "evidence_gap":gap,
        "guards":{
            "retrieval_is_not_pedagogical_authorization":True,
            "staged_candidates_do_not_satisfy_evidence":True,
            "retrieval_does_not_mutate_learner_state":True,
            "learning_engine_retains_use_decision":True,
            "search_projection_is_not_source_of_truth":True,
            "gap_may_trigger_mining_only_after_index_check":True,
        },
    }
