#!/usr/bin/env python3
"""Bridge shared Index Retrieval Runtime into Mining without merging roles.

Mining asks the index first. Only unresolved frontier items are forwarded to
external mining. Index remains retrieval infrastructure, not a reasoning engine.
"""
from __future__ import annotations
from index_retrieval import retrieve

def query_frontier(frontier, index_rows, *, semantic_scores=None, relations=None,
                   detail_rows=None, min_results=1, top_k=5):
    resolved=[]; unresolved=[]; traces=[]
    for item in frontier or []:
        fid=str(item.get("id") or "")
        q=str(item.get("question") or fid)
        result=retrieve(
            index_rows or [], q,
            semantic_scores=semantic_scores,
            relations=relations,
            detail_rows=detail_rows,
            top_k=top_k,
            relation_hops=1,
        )
        primary=result.get("primary",[])
        enough=len(primary)>=int(min_results)
        traces.append({
            "frontier_id":fid,
            "query":q,
            "sufficient":enough,
            "retrieval_counts":result.get("counts",{}),
            "source_ids":[x.get("source_id") for x in primary],
        })
        if enough:
            resolved.append({
                "frontier_id":fid,
                "question":q,
                "index_result":result,
            })
        else:
            unresolved.append(item)
    return {
        "schema":"TAKY_MINING_INDEX_FIRST_BRIDGE_V1",
        "resolved_from_index":resolved,
        "external_mining_frontier":unresolved,
        "trace":traces,
        "counts":{
            "frontier_total":len(frontier or []),
            "resolved_from_index":len(resolved),
            "external_required":len(unresolved),
        },
        "guards":{
            "index_does_not_decide_domain_use":True,
            "index_result_is_evidence_candidate":True,
            "external_mining_only_for_remaining_gap":True,
            "search_projection_is_not_source_of_truth":True,
        },
    }
