#!/usr/bin/env python3
"""Audit-only safe composition: current main Learning Index eligibility -> V2 Index-first.

This is a source-projection adapter for one independently routed Learning gap,
NOT a new Index, an external provider, a CURRENT promotion, or live authorization.
The older V2 bridge counts any top-ranked source. A Learning gap must instead
retain its verified main-Index source-family/authority minimum and source IDs.
"""
from __future__ import annotations

from mining_v2_reference_gap_guard import check_index_projection

SCHEMA="TAKY_MAIN_LEARNING_TO_V2_SCOPED_INDEX_INPUT_AUDIT"
HOLD_REVIEW={"REVIEW_REQUIRED","HOLD","ACCESS_RESTRICTED","UNREVIEWED"}
def _text(value):
    return value.strip() if isinstance(value,str) else ""
def fail(reason):
    return {"ok":False,"reason":reason,"scoped_rows":[],
            "external_dispatch_authorized":False,"index_write_authorized":False,
            "learning_promotion_authorized":False}

def scope_index_input(gap,route,projection,index_rows):
    """Use only actual main-broker eligibility, never V2's raw retrieval count.

    Rows are main data_index_search normalized records from the same exact
    Index snapshot. A detached main receipt, a rewritten source ID, a held
    review state, or changed policy causes HOLD rather than a new mining call.
    """
    if not check_index_projection(projection):
        return fail("CURRENT_INDEX_POINTER_INVALID")
    if (not isinstance(gap,dict) or gap.get("owner")!="LEARNING_ENGINE_CORE"
            or gap.get("resolution_path")!="INDEX_THEN_MINING_IF_INSUFFICIENT"
            or gap.get("index_check_required") is not True
            or gap.get("mining_request_authorized") is True):
        return fail("REFERENCE_GAP_POLICY_REQUIRED")
    if (not isinstance(route,dict) or route.get("pass") is not True
            or route.get("index_checked") is not True
            or route.get("decision")!="MINING_REQUEST"
            or route.get("index_sufficient") is not False):
        return fail("MAIN_INDEX_REVIEW_OR_RESULT_NOT_EXTERNAL_MISS")
    request=route.get("mining_request") or {}
    proof=request.get("index_check") or {}
    retrieval=route.get("retrieval") or {}
    eligible=retrieval.get("eligible_results")
    if (request.get("gap_id")!=gap.get("gap_id")
            or request.get("request_type")!="DOMAIN_EVIDENCE_GAP_MINING_REQUEST"
            or request.get("requester")!="LEARNING_ENGINE"
            or proof.get("performed") is not True
            or type(proof.get("eligible_result_count")) is not int
            or type(proof.get("minimum_required")) is not int
            or proof["minimum_required"]<1
            or proof["eligible_result_count"]>=proof["minimum_required"]
            or not isinstance(eligible,list)
            or proof["eligible_result_count"]!=len(eligible)):
        return fail("MAIN_INDEX_CHECK_COUNT_OR_GAP_MISMATCH")
    for key in ("acceptable_source_families","acceptable_authority_classes"):
        requested=gap.get(key)
        echoed=request.get(key)
        if not isinstance(requested,list) or not requested or echoed!=requested:
            return fail("SOURCE_ELIGIBILITY_POLICY_MISSING_OR_CHANGED")
        if any(not _text(v) for v in requested):
            return fail("SOURCE_ELIGIBILITY_VALUE_INVALID")
    if not isinstance(index_rows,list) or any(not isinstance(x,dict) for x in index_rows):
        return fail("SOURCE_PROJECTION_ROWS_INVALID")
    by_id={}
    for row in index_rows:
        sid=_text(row.get("source_id"))
        if not sid or sid in by_id:
            return fail("SOURCE_PROJECTION_ID_MISSING_OR_DUPLICATE")
        by_id[sid]=row
    ids=set()
    scoped=[]
    for hit in eligible:
        if not isinstance(hit,dict):
            return fail("ELIGIBLE_SOURCE_PROOF_INVALID")
        sid=_text(hit.get("source_id"))
        if not sid or sid in ids:
            return fail("ELIGIBLE_SOURCE_DUPLICATE_OR_MISSING")
        ids.add(sid)
        row=by_id.get(sid)
        if not row:
            return fail("MAIN_INDEX_ELIGIBLE_ID_ABSENT_FROM_V2_SNAPSHOT")
        if (hit.get("source_family")!=row.get("source_family")
                or hit.get("authority_class")!=row.get("authority_class")
                or hit.get("source_ref",{}).get("source_id")!=sid):
            return fail("MAIN_INDEX_ELIGIBLE_PROVENANCE_CHANGED")
        if (row.get("source_family") not in gap["acceptable_source_families"]
                or row.get("authority_class") not in gap["acceptable_authority_classes"]):
            return fail("SOURCE_NOT_REQUESTED_AUTHORITY_OR_FAMILY")
        if str(row.get("review_state") or row.get("index_state") or "").upper() in HOLD_REVIEW:
            return fail("SOURCE_REVIEW_NOT_CLEARED")
        scoped.append(row)
    return {"ok":True,"schema":SCHEMA,"scoped_rows":scoped,
            "index_min_results":proof["minimum_required"],
            "eligible_source_ids":[x["source_id"] for x in scoped],
            "ineligible_rows_excluded":len(index_rows)-len(scoped),
            "main_index_check_preserved":dict(proof),
            "index_current_source":"DATA_UTILIZATION_INDEX_2026-09-25_V26.json",
            "external_dispatch_authorized":False,"index_write_authorized":False,
            "learning_promotion_authorized":False,
            "interpretation":"MAIN_INDEX_ELIGIBILITY_ONLY__NOT_AUTHENTICATED_SOURCE_REVIEW"}
