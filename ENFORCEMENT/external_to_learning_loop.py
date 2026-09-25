#!/usr/bin/env python3
"""Cross-engine external evidence ingest loop V1.

External mining receipt -> mining evidence ingest -> index candidate ->
index validation -> non-authoritative runtime projection update -> learning requery.

No canonical RAW/INDEX/CURRENT mutation occurs here.
"""
from __future__ import annotations
from mining_external_adapter import ingest_receipt
from index_ingest_candidate import build_candidates
from index_ingest_validator import validate_batch
from learning_mining_gap_loop import requery_learning

def candidate_to_runtime_row(candidate:dict, validation:dict)->dict:
    i=candidate.get("identity") or {}
    p=candidate.get("provenance") or {}
    c=candidate.get("classification_candidate") or {}
    d=candidate.get("discovery_candidate") or {}
    return {
        "source_id":i.get("source_id"),
        "canonical_title":i.get("canonical_title"),
        "locator":i.get("locator"),
        "media_type":i.get("media_type"),
        "content_hash":i.get("content_hash"),
        "source_family":c.get("source_family"),
        "source_type":c.get("source_type"),
        "authority_class":c.get("authority_hint"),
        "short_summary":d.get("short_summary"),
        "keywords":d.get("keywords") or [],
        "controlled_terms":[],
        "consumer_candidates":d.get("consumer_candidates") or [],
        "index_state":"CANDIDATE",
        "review_state":validation.get("review_state"),
        "current_relation":None,
        "utilization_class":"REFERENCE_ONLY",
        "cannot_claim":["CANDIDATE_NOT_CANONICAL","DOMAIN_USE_NOT_AUTHORIZED"],
        "origin":p.get("origin_locator"),
    }

def process_external_receipt(receipt:dict,index_rows:list[dict],learning_payload:dict|None=None)->dict:
    ing=ingest_receipt(receipt)
    if not ing.get("accepted"):
        return {
            "schema":"TAKY_EXTERNAL_TO_LEARNING_LOOP_V1",
            "accepted":False,
            "ingest":ing,
            "validation":None,
            "projection_added":0,
            "learning_requery":None,
        }
    batch=build_candidates(ing.get("evidence") or [])
    validation=validate_batch(batch.get("candidates") or [],index_rows or [])
    by_id={x["candidate_id"]:x for x in validation.get("results",[])}
    add=[]
    held=[]
    for c in batch.get("candidates",[]):
        v=by_id.get(c.get("candidate_id"))
        if not v: continue
        if v.get("status")=="NEW_SOURCE_CANDIDATE":
            add.append(candidate_to_runtime_row(c,v))
        else:
            held.append({"candidate_id":c.get("candidate_id"),"status":v.get("status"),"hold_reason":v.get("hold_reason")})
    updated=list(index_rows or [])+add
    learning=None
    if learning_payload is not None:
        learning=requery_learning(learning_payload,updated)
    return {
        "schema":"TAKY_EXTERNAL_TO_LEARNING_LOOP_V1",
        "accepted":True,
        "ingest":ing,
        "candidate_batch":batch,
        "validation":validation,
        "projection_added":len(add),
        "projection_held":held,
        "updated_projection_count":len(updated),
        "learning_requery":learning,
        "guards":{
            "runtime_projection_only":True,
            "canonical_index_unchanged":True,
            "exact_near_version_not_auto_added":True,
            "current_not_promoted":True,
            "learning_consumes_index_projection_not_raw_provider_output":True,
        },
    }
