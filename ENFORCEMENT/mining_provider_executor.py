#!/usr/bin/env python3
"""Provider execution contract for TAKY Mining Engine.

Creates provider-agnostic execution requests and normalizes provider responses
into External Mining Adapter receipts. Network calls remain outside this module.
"""
from __future__ import annotations
import hashlib
from urllib.parse import urlparse

SUPPORTED_PROVIDERS={"WEB","GITHUB","PUBLIC_DATA"}

def _id(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def build_execution_request(query_plan:dict, provider:str)->dict:
    p=str(provider or "").upper()
    if p not in SUPPORTED_PROVIDERS:
        return {"valid":False,"error":"UNSUPPORTED_PROVIDER","provider":p}
    fid=str(query_plan.get("frontier_id") or "")
    query=str(query_plan.get("query") or "").strip()
    if not fid or not query:
        return {"valid":False,"error":"INVALID_QUERY_PLAN","provider":p}
    return {
        "schema":"TAKY_MINING_PROVIDER_REQUEST_V1",
        "request_id":_id(f"{p}|{fid}|{query}"),
        "provider":p,
        "frontier_id":fid,
        "query":query,
        "purpose":query_plan.get("purpose"),
        "preferred_source_classes":query_plan.get("prefer") or query_plan.get("preferred_source_classes") or [],
        "limits":{"max_results":int(query_plan.get("max_results",10) or 10)},
        "guards":{"provider_may_not_promote_memory":True,"provider_result_is_evidence_candidate_only":True},
    }

def _classify(provider:str,row:dict)->str:
    explicit=str(row.get("source_class") or "").upper()
    if explicit in {"PRIMARY","OFFICIAL","ACADEMIC","IMPLEMENTATION","COMMUNITY","UNKNOWN"}:
        return explicit
    url=str(row.get("url") or "")
    domain=urlparse(url).netloc.lower()
    if provider=="GITHUB": return "IMPLEMENTATION"
    if provider=="PUBLIC_DATA": return "OFFICIAL"
    if domain.endswith(".gov") or ".go." in domain or domain.endswith(".go.kr"): return "OFFICIAL"
    return "UNKNOWN"

def provider_response_to_receipt(request:dict,response:dict)->dict:
    if not request.get("schema")=="TAKY_MINING_PROVIDER_REQUEST_V1":
        return {"frontier_id":request.get("frontier_id"),"query":request.get("query"),"adapter":request.get("provider"),"results":[],"error":"INVALID_REQUEST"}
    provider=request["provider"]
    rows=response.get("results",[]) if isinstance(response,dict) else []
    out=[]
    for row in rows:
        if not isinstance(row,dict): continue
        url=str(row.get("url") or row.get("html_url") or "")
        out.append({
            "source_id":row.get("source_id") or row.get("id"),
            "source_identity":row.get("source_identity") or url or row.get("title") or row.get("name"),
            "url":url or None,
            "title":row.get("title") or row.get("name"),
            "source_class":_classify(provider,row),
            "claim":row.get("claim") or row.get("summary"),
            "subject":row.get("subject"),
            "predicate":row.get("predicate"),
            "scope":row.get("scope"),
            "value":row.get("value"),
            "polarity":row.get("polarity"),
            "direct_support":bool(row.get("direct_support")),
            "fresh_enough":bool(row.get("fresh_enough",True)),
            "independent_support_count":int(row.get("independent_support_count",1) or 1),
            "published_at":row.get("published_at") or row.get("updated_at"),
            "retrieved_at":response.get("retrieved_at") if isinstance(response,dict) else None,
            "excerpt_ref":row.get("excerpt_ref"),
            "adapter":provider,
        })
    return {
        "frontier_id":request["frontier_id"],
        "query":request["query"],
        "adapter":provider,
        "request_id":request["request_id"],
        "results":out,
    }
