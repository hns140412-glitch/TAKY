#!/usr/bin/env python3
"""External mining result -> Index ingest candidate V1.

Converts provider/mining evidence into non-canonical Index candidates.
Per role contract, Mining may supply topical hints but persistent classification,
dedup/version/current decisions remain Indexing responsibilities.
"""
from __future__ import annotations
import hashlib, unicodedata
from urllib.parse import urlparse

def _norm(v):
    return unicodedata.normalize("NFKC",str(v or "")).strip().lower()

def _id(*parts):
    return hashlib.sha256("|".join(_norm(x) for x in parts).encode("utf-8")).hexdigest()[:20]

def build_candidate(evidence:dict)->dict:
    url=str(evidence.get("source_url") or evidence.get("source_identity") or "").strip()
    title=str(evidence.get("source_title") or evidence.get("source_identity") or "").strip()
    domain=urlparse(url).netloc.lower() if url else ""
    external_id=evidence.get("source_id")
    candidate_id=str(external_id or _id(url,title,evidence.get("claim")))
    return {
        "schema":"TAKY_INDEX_INGEST_CANDIDATE_V1",
        "candidate_id":candidate_id,
        "identity":{
            "source_id":candidate_id,
            "canonical_title":title or url or candidate_id,
            "locator":url or None,
            "media_type":evidence.get("media_type"),
            "content_hash":evidence.get("content_hash"),
            "captured_at":evidence.get("retrieved_at"),
        },
        "provenance":{
            "origin_type":"EXTERNAL_MINING",
            "origin_locator":url or None,
            "publisher_or_account":domain or None,
            "acquired_at":evidence.get("retrieved_at"),
            "acquisition_id":evidence.get("evidence_id"),
            "provenance_confidence":"EXPLICIT_PROVIDER_RECEIPT",
        },
        "classification_candidate":{
            "authority_hint":evidence.get("source_class"),
            "domain_facets":[],
            "source_family":None,
            "source_type":None,
        },
        "discovery_candidate":{
            "short_summary":evidence.get("claim"),
            "keywords":[],
            "consumer_candidates":[],
        },
        "relations_candidate":[],
        "state":{
            "index_state":"CANDIDATE",
            "review_state":"REQUIRES_INDEX_VALIDATION",
            "current_relation":None,
        },
        "guards":{
            "candidate_is_not_canonical":True,
            "mining_does_not_assign_persistent_family":True,
            "mining_does_not_assign_current":True,
            "mining_does_not_authorize_domain_use":True,
        },
    }

def build_candidates(evidence_rows:list[dict])->dict:
    candidates=[build_candidate(x) for x in evidence_rows or [] if isinstance(x,dict)]
    return {
        "schema":"TAKY_INDEX_INGEST_CANDIDATE_BATCH_V1",
        "candidates":candidates,
        "count":len(candidates),
        "guards":{"batch_is_not_index":True,"raw_external_evidence_preserved":True},
    }
