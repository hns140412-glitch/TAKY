#!/usr/bin/env python3
"""External Mining Adapter protocol for TAKY Mining Engine.

This layer does not bind TAKY to one search provider. It validates adapter
receipts and normalizes discovered evidence into the Mining Core schema.
"""
from __future__ import annotations
import hashlib
from urllib.parse import urlparse

ALLOWED_SOURCE_CLASSES={"PRIMARY","OFFICIAL","ACADEMIC","IMPLEMENTATION","COMMUNITY","UNKNOWN"}

def _id(v:str)->str:
    return hashlib.sha256(v.encode("utf-8")).hexdigest()[:16]

def _domain(url:str)->str:
    try: return urlparse(url).netloc.lower()
    except Exception: return ""

def validate_receipt(receipt:dict)->dict:
    errors=[]
    if not receipt.get("frontier_id"): errors.append("MISSING_FRONTIER_ID")
    if not receipt.get("query"): errors.append("MISSING_QUERY")
    results=receipt.get("results")
    if not isinstance(results,list): errors.append("RESULTS_NOT_LIST")
    return {"valid":not errors,"errors":errors}

def normalize_result(frontier_id:str, row:dict)->dict:
    url=str(row.get("url") or "").strip()
    title=str(row.get("title") or "").strip()
    source_class=str(row.get("source_class") or "UNKNOWN").upper()
    if source_class not in ALLOWED_SOURCE_CLASSES: source_class="UNKNOWN"
    identity=str(row.get("source_identity") or url or title).strip()
    return {
        "evidence_id":str(row.get("evidence_id") or _id(f"{frontier_id}|{identity}|{row.get('claim','')}")),
        "frontier_id":str(frontier_id),
        "source_id":row.get("source_id"),
        "source_identity":identity,
        "source_url":url or None,
        "source_domain":_domain(url) or None,
        "source_title":title or None,
        "source_class":source_class,
        "claim":row.get("claim"),
        "subject":row.get("subject"),
        "predicate":row.get("predicate"),
        "scope":row.get("scope"),
        "value":row.get("value"),
        "polarity":row.get("polarity"),
        "direct_support":bool(row.get("direct_support")),
        "fresh_enough":bool(row.get("fresh_enough",True)),
        "independent_support_count":int(row.get("independent_support_count",1) or 1),
        "published_at":row.get("published_at"),
        "retrieved_at":row.get("retrieved_at"),
        "excerpt_ref":row.get("excerpt_ref"),
        "adapter":row.get("adapter"),
    }

def ingest_receipt(receipt:dict)->dict:
    v=validate_receipt(receipt)
    if not v["valid"]:
        return {"schema":"TAKY_EXTERNAL_MINING_INGEST_V1","accepted":False,"errors":v["errors"],"evidence":[]}
    fid=str(receipt["frontier_id"])
    evidence=[normalize_result(fid,row) for row in receipt.get("results",[]) if isinstance(row,dict)]
    return {
        "schema":"TAKY_EXTERNAL_MINING_INGEST_V1",
        "accepted":True,
        "errors":[],
        "frontier_id":fid,
        "query":receipt.get("query"),
        "adapter":receipt.get("adapter"),
        "evidence":evidence,
        "result_count":len(evidence),
        "guards":{
            "adapter_result_is_not_canonical":True,
            "raw_source_authority_not_overwritten":True,
            "provider_independent_contract":True,
        },
    }
