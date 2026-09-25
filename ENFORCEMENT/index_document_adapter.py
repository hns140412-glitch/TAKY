#!/usr/bin/env python3
"""Adapter for TAKY Index documents and runtime projections.

Accepts mixed legacy V24 rows and schema-contract index_l1 rows.
Produces retrieval-ready, non-authoritative rows without mutating source data.
"""
from __future__ import annotations

def _pick(*values):
    for v in values:
        if v is not None:
            return v
    return None

def normalize_source_entry(row:dict)->dict:
    l1=row.get("index_l1") or {}
    identity=l1.get("identity") or {}
    classification=l1.get("classification") or {}
    discovery=l1.get("discovery") or {}
    state=l1.get("state") or {}
    return {
        "source_id":_pick(identity.get("source_id"),row.get("source_id")),
        "canonical_title":_pick(identity.get("canonical_title"),row.get("canonical_title"),row.get("title")),
        "locator":_pick(identity.get("locator"),row.get("locator"),row.get("path")),
        "media_type":_pick(identity.get("media_type"),row.get("media_type"),row.get("mime_type")),
        "content_hash":identity.get("content_hash"),
        "source_family":_pick(classification.get("source_family"),row.get("source_family")),
        "source_type":_pick(classification.get("source_type"),row.get("source_type"),row.get("role")),
        "authority_class":_pick(classification.get("authority_class"),row.get("authority_class"),row.get("authority_level")),
        "short_summary":_pick(discovery.get("short_summary"),row.get("short_summary"),row.get("value_statement"),row.get("role")),
        "controlled_terms":_pick(discovery.get("controlled_terms"),row.get("controlled_terms"),[]),
        "keywords":_pick(discovery.get("keywords"),row.get("keywords"),[]),
        "consumer_candidates":_pick(discovery.get("consumer_candidates"),row.get("consumer_candidates"),row.get("consumers"),[]),
        "index_state":_pick(state.get("index_state"),row.get("index_state")),
        "review_state":_pick(state.get("review_state"),row.get("review_state"),row.get("review_bucket")),
        "current_relation":_pick(state.get("current_relation"),row.get("current_relation")),
        "utilization_class":row.get("utilization_class"),
        "cannot_claim":row.get("cannot_claim") or [],
        "metadata_junk":bool(row.get("metadata_junk",False)),
    }

def load_index_document(document:dict)->dict:
    rows=document.get("source_entries") or []
    normalized=[normalize_source_entry(x) for x in rows if isinstance(x,dict)]
    normalized=[x for x in normalized if x.get("source_id")]
    return {
        "schema":"TAKY_INDEX_RUNTIME_LOAD_V1",
        "source_schema":document.get("schema"),
        "source_count":len(rows),
        "loaded_count":len(normalized),
        "rows":normalized,
        "guards":{
            "source_document_unchanged":True,
            "projection_non_authoritative":True,
            "legacy_and_index_l1_supported":True,
        },
    }
