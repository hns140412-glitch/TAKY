#!/usr/bin/env python3
"""Fail-closed Indexing owner receipt boundary for reference intake.

A provider, Mining receipt or request JSON cannot approve its own indexing.
Only an independently injected, owner-provisioned receipt verifier may return
a reviewed Indexing receipt. This module has no credential, network, index
mutation or domain-policy authority. None is guessed when not connected.
"""
from __future__ import annotations

from typing import Callable, Any

OWNER="INDEXING_OWNER"
def clean(value: object) -> str:
    return str(value or "").strip()

def bind_verified_index_result(
    record: dict[str, Any],
    proposed: object,
    independent_owner_verifier: Callable[[str, dict], object] | None = None,
) -> dict[str, Any]:
    """Return independent reviewed metadata, never raw request-side flags.

    The caller provisions the verifier from the Indexing owner trust boundary,
    not from record/reference_intake_execution. Its reviewed source identity,
    index version, source locator and evidence reference must match a submitted
    proposal before an INDEXED disposition can be recorded.
    """
    source_id=clean(record.get("source_id")) if isinstance(record,dict) else ""
    if not source_id:
        return {"ok":False,"reason":"INDEX_SOURCE_ID_NOT_YET_ASSIGNED"}
    if not isinstance(proposed,dict):
        return {"ok":False,"reason":"INDEX_RESULT_PROPOSAL_MISSING"}
    if not callable(independent_owner_verifier):
        return {"ok":False,"reason":"INDEX_OWNER_VERIFIER_NOT_CONFIGURED"}
    proposed_id=clean(proposed.get("source_id"))
    proposed_ref=clean(proposed.get("source_ref"))
    proposed_version=clean(proposed.get("index_version"))
    if not all((proposed_id,proposed_ref,proposed_version)) or proposed_id!=source_id:
        return {"ok":False,"reason":"INDEX_RESULT_SOURCE_BINDING_INVALID"}
    try:
        review=independent_owner_verifier(source_id,{
            "source_id":proposed_id,"source_ref":proposed_ref,
            "index_version":proposed_version,
        })
    except Exception:
        return {"ok":False,"reason":"INDEX_OWNER_REVIEW_UNAVAILABLE"}
    if not isinstance(review,dict):
        return {"ok":False,"reason":"INDEX_OWNER_RECEIPT_MISSING"}
    refs=review.get("review_evidence_refs")
    if (review.get("issuer")!=OWNER or review.get("reviewed") is not True
            or review.get("decision")!="INDEXED"
            or clean(review.get("source_id"))!=source_id
            or clean(review.get("source_ref"))!=proposed_ref
            or clean(review.get("index_version"))!=proposed_version
            or not isinstance(refs,list) or not refs or
            any(not isinstance(x,str) or not x.strip() for x in refs)):
        return {"ok":False,"reason":"INDEPENDENT_INDEX_RECEIPT_INVALID"}
    return {"ok":True,"result":{
        "source_id":source_id,
        "source_ref":clean(review["source_ref"]),
        "index_version":clean(review["index_version"]),
        "duplicate_relation":review.get("duplicate_relation"),
        "version_relation":review.get("version_relation"),
        "review_evidence_refs":[x.strip() for x in refs],
        "review_issuer":OWNER,
        "review_decision":"INDEXED",
    },"authority":"INDEPENDENT_INDEXING_OWNER_REVIEW_ONLY",
    "canonical_promotion":False,"learning_use_authorized":False}
