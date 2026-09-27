#!/usr/bin/env python3
"""Audit-only seam: main Learning Index-first gap -> separate Mining V2 provider
candidate -> independently reviewed result -> V2 evidence candidate.

This is NOT a provider/network adapter, trusted authority itself, CURRENT
promotion, production execution authorization or a copy of Mining V2.
"""
from __future__ import annotations

import hashlib
import json
from typing import Callable
from urllib.parse import urlparse

from mining_provider_execution_loop import build_requests
from mining_provider_executor import provider_response_to_receipt
from mining_external_adapter import ingest_receipt

SCHEMA="TAKY_MAIN_LEARNING_TO_MINING_V2_GUARDED_AUDIT_V01"
REQUIRED_CONSTRAINTS={
    "MINING_DISCOVERS_AND_ACQUIRES_ONLY",
    "INDEXING_OWNS_PERSISTENT_CLASSIFICATION",
    "LEARNING_OWNS_FINAL_EVIDENCE_USE_DECISION",
    "NO_CANONICAL_PROMOTION",
}
# Immutable checkpoint for *this test only*, not an alternate CURRENT.
PINNED_POINTER={
    "source_index":("DATA_SOURCE_INDEX_2026-09-25_V6.json",
                    "13tmAJVLn9jZRn8NUOfBtOhnEuCqCyS7ZY8iXLDKHtdc"),
    "utilization_index":("DATA_UTILIZATION_INDEX_2026-09-25_V26.json",
                         "1wjoNxZVhM7L_BL7VFtbAGuV-NwzrF4U3pK7y5vrRC3s")
}


def clean(value):
    return str(value or "").strip()


def list_of_text(value):
    if not isinstance(value,list):
        return []
    return [clean(x) for x in value if isinstance(x,str) and clean(x)]


def fail(reason):
    return {"ok":False,"reason":reason,"requests":[],
            "external_dispatch_authorized":False,"index_write_authorized":False}


def check_index_projection(projection):
    a=projection.get("authority_current") if isinstance(projection,dict) else None
    if not isinstance(a,dict):
        return False
    for key,(name,identity) in PINNED_POINTER.items():
        row=a.get(key)
        if not isinstance(row,dict) or (row.get("name"),row.get("id"))!=(name,identity):
            return False
    return (a.get("source_entries_total")==679 and a.get("indexed_l1")==679
            and a.get("semantic_content_resolved")==677
            and a.get("content_access_holds")==2 and a.get("full_reindex") is False
            and a.get("source_loss") is False)


def prepare(route,gap,projection,plan):
    if not check_index_projection(projection):
        return fail("PINNED_INDEX_CURRENT_PROJECTION_MISMATCH")
    if (not isinstance(gap,dict) or gap.get("owner")!="LEARNING_ENGINE_CORE"
            or gap.get("resolution_path")!="INDEX_THEN_MINING_IF_INSUFFICIENT"
            or gap.get("index_check_required") is not True
            or gap.get("mining_request_authorized") is True):
        return fail("LEARNING_REFERENCE_GAP_REQUIRED")
    if (not isinstance(route,dict) or route.get("pass") is not True
            or route.get("decision")!="MINING_REQUEST"
            or route.get("index_checked") is not True
            or route.get("index_sufficient") is not False):
        return fail("ACTUAL_MAIN_INDEX_FIRST_MISS_REQUIRED")
    request=route.get("mining_request") or {}
    proof=request.get("index_check") or {}
    if (request.get("request_type")!="DOMAIN_EVIDENCE_GAP_MINING_REQUEST"
            or request.get("requester")!="LEARNING_ENGINE"
            or not clean(request.get("gap_id")) or request.get("gap_id")!=gap.get("gap_id")
            or proof.get("performed") is not True
            or not isinstance(proof.get("eligible_result_count"),int)
            or not isinstance(proof.get("minimum_required"),int)
            or proof["minimum_required"]<1
            or proof["eligible_result_count"]>=proof["minimum_required"]
            or not REQUIRED_CONSTRAINTS.issubset(set(request.get("constraints") or []))):
        return fail("BROKER_REFERENCE_REQUEST_INVALID")
    keys=("query_terms","acceptable_source_families",
          "acceptable_authority_classes","required_provenance")
    values={}
    for key in keys:
        expected=list_of_text(gap.get(key))
        actual=list_of_text(request.get(key))
        if not expected or actual!=expected or len(actual)!=len(set(actual)):
            return fail("MISSING_OR_CHANGED_"+key.upper())
        values[key]=actual
    external=plan.get("external_search_frontier") if isinstance(plan,dict) else None
    if (plan.get("schema") if isinstance(plan,dict) else None)=="TAKY_MINING_RUN_ORCHESTRATOR_V1":
        # Whole run result accepted only with explicit route; never infer it
        # from a generic V2 execution_allowed flag.
        external=plan.get("plan",{}).get("external_search_frontier")
    query=" ".join(values["query_terms"])
    if not isinstance(external,list) or len(external)!=1 or (
        clean(external[0].get("question"))!=query):
        return fail("V2_EXTERNAL_FRONTIER_NOT_EXACT_LEARNING_GAP")
    if plan.get("plan",{}).get("execution_allowed") is False:
        return fail("V2_KNOWN_FAILED_ROUTE_HELD")
    source_classes=values["acceptable_authority_classes"]
    if any(x not in {"OFFICIAL","PRIMARY","ACADEMIC","IMPLEMENTATION","COMMUNITY"}
           for x in source_classes):
        return fail("EXPLICIT_SUPPORTED_SOURCE_CLASS_REQUIRED")
    plans=[{"frontier_id":clean(external[0].get("id")),
            "query":query,"purpose":"FILL_EVIDENCE_GAP",
            "prefer":source_classes,"max_results":10}]
    candidates=build_requests(plans,max_providers_per_query=2)
    if not candidates:
        return fail("V2_PROVIDER_CANDIDATES_MISSING")
    policy={
        "gap_id":request["gap_id"],
        "source_families":values["acceptable_source_families"],
        "source_classes":source_classes,
        "required_provenance":values["required_provenance"],
        "index_current":PINNED_POINTER["utilization_index"][0],
        "index_check":dict(proof),
    }
    digest=hashlib.sha256(json.dumps(policy,sort_keys=True,ensure_ascii=False,
                                   separators=(",",":")).encode()).hexdigest()
    outputs=[]
    for c in candidates:
        if c.get("schema")!="TAKY_MINING_PROVIDER_REQUEST_V1":
            return fail("V2_PROVIDER_REQUEST_INVALID")
        outputs.append({**c,"audit_guard":{
            "contract":SCHEMA,"constraint_sha256":digest,
            "gap_id":request["gap_id"],
            "network_authorized":False,
            "independent_source_review_required":True
        }})
    return {"ok":True,"schema":SCHEMA,"policy":policy,
            "constraint_sha256":digest,"requests":outputs,
            "external_dispatch_authorized":False,
            "index_write_authorized":False,"learning_promotion_authorized":False,
            "basis":"ACTUAL_MAIN_BROKER__SEPARATE_V2_CANDIDATE__FIXTURE_ONLY"}


def screen_response(prepared,request,response,source_metadata_verifier:Callable|None=None):
    """Filter before invoking the V2 normalizer (which drops family/provenance).
    A self-declared OFFICIAL source or metadata flag cannot satisfy verifier.
    """
    if not prepared.get("ok") or request not in prepared.get("requests",[]):
        return fail("UNKNOWN_OR_UNBOUND_GUARDED_REQUEST")
    if (not isinstance(response,dict)
            or response.get("request_id")!=request.get("request_id")
            or response.get("provider")!=request.get("provider")
            or not isinstance(response.get("results"),list)):
        return fail("UNBOUND_PROVIDER_RESPONSE")
    policy=prepared["policy"]
    accepted=[];held=[];sidecar=[];seen=set()
    for row in response["results"]:
        if not isinstance(row,dict):
            held.append({"reason":"INVALID_SOURCE_ROW"});continue
        sid=clean(row.get("source_id"))
        url=clean(row.get("url"))
        parsed=urlparse(url)
        metadata_classes=list_of_text(row.get("provenance"))
        cls=clean(row.get("source_class")).upper()
        family=clean(row.get("source_family"))
        if (not sid or sid in seen or not clean(row.get("title")) or
                parsed.scheme!="https" or not parsed.netloc or
                parsed.username or parsed.password):
            held.append({"source_id":sid or None,"reason":"INVALID_OR_DUPLICATE_SOURCE_IDENTITY"})
            continue
        seen.add(sid)
        if cls not in policy["source_classes"] or family not in policy["source_families"]:
            held.append({"source_id":sid,"reason":"REQUESTED_FAMILY_OR_AUTHORITY_NOT_MET"})
            continue
        if not set(policy["required_provenance"]).issubset(set(metadata_classes)):
            held.append({"source_id":sid,"reason":"REQUESTED_PROVENANCE_NOT_MET"})
            continue
        if not callable(source_metadata_verifier):
            held.append({"source_id":sid,"reason":"INDEPENDENT_SOURCE_REVIEW_REQUIRED"})
            continue
        # The verifier must be supplied by an independently controlled reviewer;
        # never accept the provider's own reviewed/verified boolean.
        try:
            review=source_metadata_verifier(row,policy)
        except Exception:
            review=None
        if (not isinstance(review,dict) or review.get("reviewed") is not True
                or review.get("source_id")!=sid
                or review.get("source_family")!=family
                or review.get("source_class")!=cls
                or not list_of_text(review.get("evidence_refs"))):
            held.append({"source_id":sid,"reason":"INDEPENDENT_SOURCE_REVIEW_FAILED"})
            continue
        accepted.append(row)
        sidecar.append({"source_id":sid,"source_family":family,"source_class":cls,
                        "required_provenance":metadata_classes,
                        "review_evidence_refs":review["evidence_refs"],
                        "constraint_sha256":prepared["constraint_sha256"]})
    if not accepted:
        return {"ok":False,"reason":"NO_INDEPENDENTLY_REVIEWED_MATCHES","held":held,
                "evidence":[],"external_dispatch_authorized":False,
                "index_write_authorized":False,"learning_promotion_authorized":False}
    # Actual V2 functions are invoked ONLY after independent metadata review.
    raw_request={k:v for k,v in request.items() if k!="audit_guard"}
    receipt=provider_response_to_receipt(raw_request,{
        "results":accepted,"retrieved_at":response.get("retrieved_at")})
    ingested=ingest_receipt(receipt)
    if not ingested.get("accepted") or len(ingested["evidence"])!=len(accepted):
        return fail("V2_EVIDENCE_NORMALIZATION_FAILED")
    return {"ok":True,"schema":SCHEMA,"status":"REVIEWED_MINING_EVIDENCE_CANDIDATE_ONLY",
            "receipt":receipt,"evidence":ingested["evidence"],
            "source_metadata_sidecar":sidecar,"held":held,
            "external_dispatch_authorized":False,"index_write_authorized":False,
            "learning_promotion_authorized":False,
            "pending":"INDEXING_OWNED_INTAKE_AND_INDEPENDENT_LEARNING_POLICY"}
