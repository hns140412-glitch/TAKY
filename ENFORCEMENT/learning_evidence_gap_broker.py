#!/usr/bin/env python3
"""Route Learning evidence gaps to the correct resolver.

Reference evidence gaps:
Learning -> Index existence check -> Mining only if insufficient.

Learner-performance gaps:
Learning -> specialist evidence acquisition. External Mining is forbidden.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from data_index_search import load_index, search

VERSION="TAKY_LEARNING_EVIDENCE_GAP_BROKER_V2"

def _clean(v): return str(v or "").strip()

def _query_from_gap(gap):
    terms=gap.get("query_terms")
    if isinstance(terms,list):
        vals=[_clean(x) for x in terms if _clean(x)]
        if vals:return " ".join(vals)
    scope=gap.get("scope") if isinstance(gap.get("scope"),dict) else {}
    return " ".join(x for x in (_clean(scope.get("subject")),_clean(scope.get("concept_skill_target")),_clean(gap.get("gap_type"))) if x)

def _eligible(hit,gap):
    fam=set(gap.get("acceptable_source_families") or [])
    auth=set(gap.get("acceptable_authority_classes") or [])
    if fam and hit.get("source_family") not in fam:return False
    if auth and hit.get("authority_class") not in auth:return False
    return True

# V26 retains descriptive authority labels such as AUTHORITY_LAYER rather
# than silently converting source metadata to OFFICIAL. This is a *review
# candidate*, never an equivalent trusted official class or domain approval.
# Keep the set narrow: uncertain/historical/derived labels do not qualify.
OFFICIAL_TAXONOMY_REVIEW_CANDIDATES=frozenset({"AUTHORITY_LAYER"})

def _pending_authority_review(hit,gap):
    if not isinstance(hit,dict):return False
    fam=set(gap.get("acceptable_source_families") or [])
    auth=set(gap.get("acceptable_authority_classes") or [])
    if "OFFICIAL" not in auth:return False
    if fam and hit.get("source_family") not in fam:return False
    if hit.get("authority_class") not in OFFICIAL_TAXONOMY_REVIEW_CANDIDATES:return False
    ref=hit.get("source_ref") or {}
    # No source_ref, no safe escalation. A search label alone is not proof.
    return isinstance(ref,dict) and bool(ref.get("source_id")) and (
        ref.get("source_id")==hit.get("source_id")) and bool(
        ref.get("locator") or (hit.get("provenance") or {}).get("origin_locator"))

def route_gap(gap:dict[str,Any],*,index_path:Path,min_results:int=1,consumer:str="LEARNING_ENGINE")->dict[str,Any]:
    if not isinstance(gap,dict): return {"pass":False,"detected":["EVIDENCE_GAP_REQUIRED"]}
    if gap.get("owner")!="LEARNING_ENGINE_CORE": return {"pass":False,"detected":["EVIDENCE_GAP_OWNER_INVALID"]}
    if gap.get("mining_request_authorized") is True: return {"pass":False,"detected":["LEARNING_MINING_AUTHORIZATION_FORBIDDEN"]}

    path=gap.get("resolution_path")
    if path=="SPECIALIST_EVIDENCE_ACQUISITION":
        return {
            "pass":True,"version":VERSION,"gap_id":gap.get("gap_id"),
            "index_checked":False,"index_sufficient":False,
            "decision":"SPECIALIST_EVIDENCE_REQUEST","mining_request":None,
            "specialist_request":{
                "request_type":"LEARNER_EVIDENCE_ACQUISITION_REQUEST",
                "scope":gap.get("scope") or {},
                "gap_type":gap.get("gap_type"),
                "requested_capability":gap.get("requested_capability"),
            },
            "invariant":"LEARNER_PERFORMANCE_GAP_NEVER_TRIGGERS_EXTERNAL_MINING"
        }

    if path!="INDEX_THEN_MINING_IF_INSUFFICIENT" or gap.get("index_check_required") is not True:
        return {"pass":False,"detected":["REFERENCE_GAP_RESOLUTION_PATH_INVALID"]}

    query=_query_from_gap(gap)
    if not query:return {"pass":False,"detected":["EVIDENCE_GAP_QUERY_EMPTY"]}
    if min_results<1:return {"pass":False,"detected":["MIN_RESULTS_INVALID"]}

    records=load_index(index_path)
    result=search(records,query,filters={},limit=max(min_results,10),relation_depth=1)
    eligible=[x for x in result.get("results",[]) if _eligible(x,gap)]

    if len(eligible)>=min_results:
        return {
            "pass":True,"version":VERSION,"gap_id":gap.get("gap_id"),
            "index_checked":True,"index_sufficient":True,
            "decision":"INDEX_REQUERY","mining_request":None,
            "retrieval":{**result,"eligible_results":eligible},
            "invariant":"INDEX_FIRST__MINING_ONLY_IF_REFERENCE_EVIDENCE_INSUFFICIENT"
        }

    # Source already found under V26's descriptive authority taxonomy can
    # be held for independent authority review. Do not auto-convert it to an
    # OFFICIAL result, but also do not send unnecessary external Mining until
    # the candidate's review is resolved. The ORIGINAL index/class stays intact.
    pending=[x for x in result.get("results",[]) if _pending_authority_review(x,gap)]
    if len(eligible)+len(pending)>=min_results:
        return {
            "pass":True,"version":VERSION,"gap_id":gap.get("gap_id"),
            "index_checked":True,"index_sufficient":False,
            "decision":"INDEX_AUTHORITY_REVIEW_REQUIRED","mining_request":None,
            "authority_review_request":{
                "request_type":"INDEPENDENT_INDEX_SOURCE_AUTHORITY_REVIEW",
                "scope":gap.get("scope") or {},
                "requested_authority_classes":gap.get("acceptable_authority_classes") or [],
                "source_candidates":[{
                    "source_id":hit["source_id"],
                    "source_ref":hit["source_ref"],
                    "source_family":hit.get("source_family"),
                    "source_authority_literal":hit.get("authority_class"),
                    "review_status":"PENDING_INDEPENDENT_SOURCE_VERIFICATION",
                } for hit in pending],
                "guards":{
                    "raw_authority_label_preserved":True,
                    "candidate_is_not_official_proof":True,
                    "candidate_is_not_learning_authorization":True,
                    "no_automatic_mining_or_index_promotion":True,
                }
            },
            "retrieval":{**result,"eligible_results":eligible,
                         "authority_review_candidates":pending},
            "invariant":"INDEX_FIRST__UNCERTAIN_EXISTING_AUTHORITY_REVIEW_BEFORE_EXTERNAL_MINING"
        }

    request={
        "request_type":"DOMAIN_EVIDENCE_GAP_MINING_REQUEST",
        "requester":consumer,
        "gap_id":gap.get("gap_id"),"gap_type":gap.get("gap_type"),
        "priority":gap.get("priority"),"scope":gap.get("scope") or {},
        "query_terms":gap.get("query_terms") or [],
        "existing_source_refs":gap.get("existing_source_refs") or [],
        "requested_capability":gap.get("requested_capability") or "EXTERNAL_REFERENCE_EVIDENCE",
        "acceptable_source_families":gap.get("acceptable_source_families") or [],
        "acceptable_authority_classes":gap.get("acceptable_authority_classes") or [],
        "required_provenance":gap.get("required_provenance") or [],
        "index_check":{"performed":True,"result_count":len(result.get("results",[])),"eligible_result_count":len(eligible),"minimum_required":min_results,"semantic_mode":result.get("semantic_mode")},
        "constraints":["MINING_DISCOVERS_AND_ACQUIRES_ONLY","INDEXING_OWNS_PERSISTENT_CLASSIFICATION","LEARNING_OWNS_FINAL_EVIDENCE_USE_DECISION","NO_CANONICAL_PROMOTION"]
    }
    return {
        "pass":True,"version":VERSION,"gap_id":gap.get("gap_id"),
        "index_checked":True,"index_sufficient":False,"decision":"MINING_REQUEST",
        "mining_request":request,"retrieval":{**result,"eligible_results":eligible},
        "invariant":"INDEX_FIRST__MINING_ONLY_IF_REFERENCE_EVIDENCE_INSUFFICIENT"
    }

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--gap",type=Path,required=True); ap.add_argument("--index",type=Path,required=True); ap.add_argument("--min-results",type=int,default=1)
    a=ap.parse_args(); gap=json.loads(a.gap.read_text(encoding="utf-8")); r=route_gap(gap,index_path=a.index,min_results=a.min_results)
    print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r.get("pass") else 1

if __name__=="__main__": raise SystemExit(main())