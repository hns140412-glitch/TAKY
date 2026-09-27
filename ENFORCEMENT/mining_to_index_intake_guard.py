#!/usr/bin/env python3
"""Audit-only seam from reviewed V2 Mining evidence to main Indexing intake.

The actual main Reference Intake Executor trusts an attached index_result
{verified:true}. A Mining/provider row must NEVER provide that flag. This
adapter strips it, preserves the result in an isolated append-only receipt and
requires a separately verified Indexing-owned result before INDEXED status.

No network, no real corpus writes, no promotion, no change to original V2.
"""
from __future__ import annotations

from urllib.parse import urlparse
from reference_intake_router import route
from reference_intake_executor import execute

SCHEMA="TAKY_MINING_CANDIDATE_TO_INDEX_INTAKE_AUDIT"

def _clean(v):
    return v.strip() if isinstance(v,str) else ""
def fail(reason):
    return {"ok":False,"reason":reason,"indexed":False,"canonical_promotion":False}

def persist_reviewed_candidate(screened,source_id,root,*,independent_index_receipt=None,
                               index_verifier=None):
    """Use only candidate evidence screened by the upstream separate guard.
    index_verifier must be a trusted Indexing-owned host capability. A caller
    supplied receipt/flag or Mining provider self-verified bit is not proof.
    """
    if not isinstance(screened,dict) or screened.get("ok") is not True or (
        screened.get("status")!="REVIEWED_MINING_EVIDENCE_CANDIDATE_ONLY" or
        screened.get("index_write_authorized") is not False or
        screened.get("learning_promotion_authorized") is not False):
        return fail("SCREENED_MINING_CANDIDATE_REQUIRED")
    sid=_clean(source_id)
    rows=screened.get("evidence")
    sidecars=screened.get("source_metadata_sidecar")
    if not sid or not isinstance(rows,list) or not isinstance(sidecars,list):
        return fail("SOURCE_EVIDENCE_AND_REVIEW_REQUIRED")
    matches=[x for x in rows if isinstance(x,dict) and x.get("source_id")==sid]
    reviewed=[x for x in sidecars if isinstance(x,dict) and x.get("source_id")==sid]
    if len(matches)!=1 or len(reviewed)!=1 or not reviewed[0].get("review_evidence_refs"):
        return fail("ONE_TO_ONE_REVIEWED_SOURCE_ID_REQUIRED")
    evidence=matches[0]
    url=_clean(evidence.get("source_url"))
    parsed=urlparse(url)
    if parsed.scheme!="https" or not parsed.netloc or parsed.username or parsed.password:
        return fail("SOURCE_URL_NOT_PRESERVED")
    if (evidence.get("source_class")!=reviewed[0].get("source_class") or
        evidence.get("source_identity") is None or
        not _clean(reviewed[0].get("constraint_sha256"))):
        return fail("EVIDENCE_REVIEW_BINDING_MISMATCH")
    record={"source_id":sid,"source_url":url,"intent_text":"학습 참고자료로 검토해",
            "domain":"learning","reference_intake_intent":True,
            "reference_intake_execution":{
                "acquisition_state":"ACCESSIBLE_REMOTE_SOURCE",
                "recorded_at":_clean(evidence.get("retrieved_at")) or
                    "2026-09-28T00:00:00+00:00"
            }}
    confirmed=None
    if independent_index_receipt is not None:
        if not callable(index_verifier):
            return fail("INDEPENDENT_INDEXING_VERIFIER_REQUIRED")
        try:
            confirmation=index_verifier(independent_index_receipt)
        except Exception:
            confirmation=None
        if (not isinstance(confirmation,dict) or confirmation.get("verified") is not True or
            confirmation.get("owner")!="INDEXING" or
            confirmation.get("source_id")!=sid or
            not _clean(confirmation.get("source_ref")) or
            not _clean(confirmation.get("index_version")) or
            not _clean(confirmation.get("review_evidence_ref"))):
            return fail("INDEPENDENT_INDEXING_RECEIPT_INVALID")
        confirmed=confirmation
        record["reference_intake_execution"]["index_result"]={
            "verified":True,"source_id":sid,
            "source_ref":confirmation["source_ref"],
            "index_version":confirmation["index_version"]
        }
    routed=route(record)
    if routed.get("route_type")!="REFERENCE_INTAKE_REVIEW":
        return fail("INDEXING_INTAKE_ROUTE_INVALID")
    result=execute(record,routed,root)
    if result.get("pass") is not True or result.get("canonical_promotion") is not False:
        return fail("MAIN_REFERENCE_EXECUTOR_REJECTED")
    states=[x.get("state") for x in result.get("emitted",[])]
    expected=(["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"] if confirmed
              else ["REGISTERED"])
    if states!=expected:
        return fail("MAIN_REFERENCE_DISPOSITION_UNEXPECTED")
    return {"ok":True,"schema":SCHEMA,"source_id":sid,
            "recorded_states":states,
            "next_handoff":result.get("next_handoff"),
            "indexed":bool(confirmed),"canonical_promotion":False,
            "learning_use_authorized":False,"external_dispatch_authorized":False,
            "receipt_review_refs":list(reviewed[0]["review_evidence_refs"]),
            "guard":"MINING_REVIEW_IS_NOT_INDEPENDENT_INDEX_CONFIRMATION"}
