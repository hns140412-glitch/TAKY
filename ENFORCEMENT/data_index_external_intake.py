#!/usr/bin/env python3
"""Stage multiple providers as discovery-only evidence; never promote external links."""
from __future__ import annotations
import re
from typing import Any
from urllib.parse import urlsplit
from data_index_search import normalize_record

SCHEMA="TAKY_EXTERNAL_DISCOVERY_INTAKE_V1"
KIND={"OFFICIAL_STANDARD","PUBLIC_API_LISTING","OPEN_SOURCE_ISSUE","COMMUNITY_DISCUSSION"}
EVIDENCE_EXTENT={"LISTING_METADATA","OPENING_PAGE_ONLY","LINK_ONLY"}
RIGHTS={"UNKNOWN_REVIEW_REQUIRED","PUBLIC_METADATA_ONLY","LICENSE_EVIDENCE_RECORDED"}
PRIVACY={"PUBLIC","AUTHORIZED_PRIVATE","RESTRICTED"}
NAMESPACE=re.compile(r"^[A-Z][A-Z0-9_]{1,40}$")

def must(value:Any,name:str)->str:
    if not isinstance(value,str) or not value.strip():raise ValueError(name+"_REQUIRED")
    return value.strip()

def project_external_candidate(c:dict)->dict:
    if not isinstance(c,dict) or c.get("schema")!=SCHEMA:raise ValueError("INTAKE_SCHEMA_INVALID")
    namespace=must(c.get("external_namespace"),"NAMESPACE")
    if not NAMESPACE.fullmatch(namespace):raise ValueError("NAMESPACE_FORMAT_INVALID")
    native=must(c.get("provider_native_id"),"PROVIDER_NATIVE_ID")
    title=must(c.get("source_title"),"TITLE")
    locator=must(c.get("original_locator"),"LOCATOR")
    u=urlsplit(locator)
    if u.scheme!="https" or not u.netloc or u.username or u.password:raise ValueError("LOCATOR_INVALID")
    if c.get("source_kind") not in KIND:raise ValueError("SOURCE_KIND_INVALID")
    if c.get("evidence_extent") not in EVIDENCE_EXTENT:raise ValueError("EVIDENCE_EXTENT_INVALID")
    if c.get("rights_state") not in RIGHTS:raise ValueError("RIGHTS_STATE_INVALID")
    if c.get("privacy_class") not in PRIVACY:raise ValueError("PRIVACY_CLASS_INVALID")
    must(c.get("observed_at"),"OBSERVED_AT")
    must(c.get("attribution"),"ATTRIBUTION")
    if c.get("content_hash") is not None or c.get("original_content_acquired") is not False:
        raise ValueError("LINK_ONLY_CANNOT_CLAIM_CONTENT_OR_HASH")
    if c.get("current_promoted") is not False:raise ValueError("PROMOTION_FORBIDDEN")
    sid=f"EXTERNAL::{namespace}::{native}"
    # Source ID is scoped; two different provider native IDs never collapse
    # solely on matching title, topic, or URL.
    r=normalize_record({"index_l1":{
        "identity":{"source_id":sid,"canonical_title":title,"locator":locator,
                    "media_type":"text/html","content_hash":None},
        "provenance":{"origin_type":"EXTERNAL_DISCOVERY_LINK_ONLY",
                      "origin_locator":locator,"publisher_or_account":c["attribution"]},
        "classification":{"source_type":c["source_kind"],"domain_facets":[],
                          "source_family":None,"authority_class":"UNASSESSED_SOURCE_METADATA"},
        "discovery":{"short_summary":None,"keywords":[],"controlled_terms":[],"entities":[],"consumer_candidates":[]},
        "state":{"index_state":"EXTERNAL_DISCOVERY_STAGED","detail_available":False,
                 "review_state":c["evidence_extent"],"current_relation":"NO_CURRENT_PROMOTION"},
        "relations":[]
    }})
    r["intake_envelope"]={
        "external_namespace":namespace,"provider_native_id":native,
        "evidence_extent":c["evidence_extent"],"rights_state":c["rights_state"],
        "privacy_class":c["privacy_class"],"observed_at":c["observed_at"],
        "original_content_acquired":False,"source_hash_state":"UNKNOWN_NOT_COMPUTED",
        "authority_verified":False,"current_promoted":False,
        "provenance_origin":"PROVIDER_ORIGINAL_LOCATOR_OBSERVED",
    }
    return r

def stage_external_candidates(rows:list[dict],existing_source_ids:set[str]|None=None)->tuple[list[dict],dict]:
    if not isinstance(rows,list):raise ValueError("CANDIDATES_ARRAY_INVALID")
    existing_source_ids=existing_source_ids or set()
    ids:set[str]=set()
    urls:dict[str,str]={}
    collisions:list[dict]=[]
    records=[]
    for row in rows:
        candidate=project_external_candidate(row)
        sid=candidate["source_id"]
        if sid in ids or sid in existing_source_ids:
            raise ValueError("NATIVE_SOURCE_ID_COLLISION")
        ids.add(sid)
        url=candidate["locator"]
        if url in urls and urls[url]!=sid:
            collisions.append({"source_id":sid,"other_source_id":urls[url],
                               "reason":"SAME_LOCATOR_CANDIDATE_NOT_AUTOMERGED"})
        else:
            urls[url]=sid
        records.append(candidate)
    return records,{"state":"STAGED_DISCOVERY_ONLY_NONCANONICAL",
                    "candidate_count":len(records),"same_locator_candidates":collisions,
                    "existing_source_count_unchanged":True,"raw_written":False,
                    "current_pointer_modified":False}
