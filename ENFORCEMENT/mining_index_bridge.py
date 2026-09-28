#!/usr/bin/env python3
"""Bridge shared Index Retrieval Runtime into Mining without merging roles.

Retrieval can locate candidate sources; it cannot establish evidence sufficiency
or replace the domain owner's utilization decision. Only uncovered source gaps
need external acquisition, while retrieved candidates still require verification.
"""
from __future__ import annotations
from index_retrieval import retrieve


def _candidate_usable(row: dict) -> bool:
    """Reject explicitly stale or held records as satisfying an index-first gap.

    Unknown status is allowed as a retrieval candidate for backward compatibility,
    but no retrieved candidate is marked as verified *evidence* here.
    """
    state = row.get("state") if isinstance(row.get("state"), dict) else {}
    for key in ("stale_state", "review_state", "index_state", "current_relation"):
        value = str(row.get(key) or state.get(key) or "").upper()
        if (value.startswith(("STALE", "SUPERSEDED", "REJECTED", "HELD", "HOLD"))
                or value in {"REVIEW_REQUIRED", "REFERENCE_ONLY", "UNVERIFIED"}):
            return False
    authority = row.get("authority_class") or (row.get("classification") or {}).get("authority_class")
    if str(authority or "").upper() in {"REFERENCE_ONLY", "UNKNOWN_UNVERIFIED"}:
        return False
    return True


def _excluded_candidate_reason(row: dict) -> str | None:
    state = row.get("state") if isinstance(row.get("state"), dict) else {}
    for key in ("stale_state", "current_relation", "review_state", "index_state"):
        value = str(row.get(key) or state.get(key) or "").upper()
        if value.startswith("STALE"):
            return "STALE"
        if value.startswith("SUPERSEDED"):
            return "SUPERSEDED"
        if value.startswith(("HELD", "HOLD")):
            return "SOURCE_REVIEW_HOLD"
        if value.startswith("REJECTED"):
            return "REJECTED"
        if value in {"REVIEW_REQUIRED", "REFERENCE_ONLY", "UNVERIFIED"}:
            return "SOURCE_REVIEW_HOLD"
    classification = row.get("classification") if isinstance(row.get("classification"), dict) else {}
    authority = str(row.get("authority_class") or classification.get("authority_class") or "").upper()
    if authority in {"REFERENCE_ONLY", "UNKNOWN_UNVERIFIED"}:
        return "SOURCE_REVIEW_HOLD"
    return None


def query_frontier(frontier, index_rows, *, semantic_scores=None, relations=None,
                   detail_rows=None, min_results=1, top_k=5):
    located, unresolved, verification, traces = [], [], [], []
    required_count = max(1, int(min_results))
    for item in frontier or []:
        fid = str(item.get("id") or "")
        question = str(item.get("question") or fid)
        result = retrieve(
            index_rows or [], question,
            semantic_scores=semantic_scores,
            relations=relations,
            detail_rows=detail_rows,
            top_k=top_k,
            relation_hops=1,
        )
        primary = result.get("primary", [])
        qualified = [x for x in primary if _candidate_usable(x.get("row") or {})]
        rejected = [
            {"source_id": x.get("source_id"), "reason": _excluded_candidate_reason(x.get("row") or {})}
            for x in primary if not _candidate_usable(x.get("row") or {})
        ]
        enough = len(qualified) >= required_count
        traces.append({
            "frontier_id": fid,
            "query": question,
            "sufficient": enough,  # legacy: retrieval coverage ONLY, never evidence sufficiency
            "retrieval_sufficient": enough,
            "evidence_sufficient": False,
            "retrieval_hit_count": len(primary),
            "qualified_index_hits": len(qualified),
            "rejected_index_candidates": rejected,
            "verification_required": enough,
            "retrieval_counts": result.get("counts", {}),
            "source_ids": [x.get("source_id") for x in primary],
        })
        if enough:
            located.append({
                "frontier_id": fid,
                "question": question,
                "index_result": result,
                "evidence_sufficient": False,
            })
            verification.append({
                **item,
                "candidate_source_ids": [x.get("source_id") for x in qualified],
                "reason": "INDEX_HIT_NOT_VERIFIED_EVIDENCE",
            })
        else:
            unresolved.append(item)
    return {
        "schema": "TAKY_MINING_INDEX_FIRST_BRIDGE_V1",
        "resolved_from_index": located,  # historical name: source retrieval, NOT research completion
        "verification_frontier": verification,
        "external_mining_frontier": unresolved,
        "trace": traces,
        "counts": {
            "frontier_total": len(frontier or []),
            "resolved_from_index": len(located),
            "verification_required": len(verification),
            "external_required": len(unresolved),
        },
        "guards": {
            "index_does_not_decide_domain_use": True,
            "index_result_is_evidence_candidate": True,
            "index_hit_does_not_prove_evidence_sufficiency": True,
            "external_mining_only_for_remaining_gap": True,
            "search_projection_is_not_source_of_truth": True,
        },
    }
