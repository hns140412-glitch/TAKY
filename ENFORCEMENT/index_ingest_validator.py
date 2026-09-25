#!/usr/bin/env python3
"""Index ingest validator V1.

Compares non-canonical ingest candidates against current index rows and emits
relation/review decisions. It never promotes CURRENT and never persists family.
"""
from __future__ import annotations
import unicodedata
from urllib.parse import urlparse

def _norm(v):
    return unicodedata.normalize("NFKC",str(v or "")).strip().lower()

def _domain(url):
    try:return urlparse(str(url or "")).netloc.lower()
    except Exception:return ""

def _candidate_fields(c):
    i=c.get("identity") or {}
    return {
        "id":i.get("source_id") or c.get("candidate_id"),
        "title":i.get("canonical_title"),
        "locator":i.get("locator"),
        "hash":i.get("content_hash"),
    }

def classify_candidate(candidate:dict,index_rows:list[dict])->dict:
    c=_candidate_fields(candidate)
    exact=[]; near=[]; version=[]
    for row in index_rows or []:
        rid=str(row.get("source_id") or "")
        if not rid: continue
        rh=row.get("content_hash")
        if c["hash"] and rh and c["hash"]==rh:
            exact.append(rid); continue
        same_locator=bool(c["locator"] and _norm(c["locator"])==_norm(row.get("locator")))
        same_title=bool(c["title"] and _norm(c["title"])==_norm(row.get("canonical_title")))
        same_domain=bool(c["locator"] and row.get("locator") and _domain(c["locator"])==_domain(row.get("locator")))
        if same_locator and same_title:
            near.append(rid)
        elif same_title and same_domain:
            version.append(rid)
    if exact:
        status="EXACT_DUPLICATE"
        review="AUTO_RELATION_CANDIDATE"
        hold=None
    elif near:
        status="NEAR_DUPLICATE"
        review="HUMAN_OR_RULE_REVIEW_REQUIRED"
        hold="CONTENT_HASH_OR_SEMANTIC_EQUIVALENCE_NOT_CONFIRMED"
    elif version:
        status="POSSIBLE_VERSION"
        review="HUMAN_OR_RULE_REVIEW_REQUIRED"
        hold="VERSION_DIRECTION_NOT_CONFIRMED"
    else:
        status="NEW_SOURCE_CANDIDATE"
        review="CLASSIFICATION_REQUIRED"
        hold=None
    return {
        "schema":"TAKY_INDEX_INGEST_VALIDATION_V1",
        "candidate_id":c["id"],
        "status":status,
        "exact_duplicate_of":exact,
        "near_duplicate_of":near,
        "possible_version_of":version,
        "review_state":review,
        "hold_reason":hold,
        "promotion_allowed":False,
        "guards":{
            "current_not_assigned":True,
            "persistent_family_not_assigned":True,
            "relation_is_candidate_until_validated":True,
        },
    }

def validate_batch(candidates:list[dict],index_rows:list[dict])->dict:
    rows=[classify_candidate(c,index_rows) for c in candidates or []]
    return {
        "schema":"TAKY_INDEX_INGEST_VALIDATION_BATCH_V1",
        "results":rows,
        "counts":{k:sum(1 for x in rows if x["status"]==k) for k in ("EXACT_DUPLICATE","NEAR_DUPLICATE","POSSIBLE_VERSION","NEW_SOURCE_CANDIDATE")},
        "guards":{"batch_validation_does_not_mutate_index":True},
    }
