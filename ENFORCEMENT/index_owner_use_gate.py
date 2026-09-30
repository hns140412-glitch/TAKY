"""Require independently host-injected Index owner review before Learning use.
Retrieved rows and caller payload flags cannot certify their own trust state.
Does not perform network IO, mutate Index/CURRENT, or provision credentials.
"""
from __future__ import annotations
import re
from typing import Callable, Any

OWNER = "INDEXING_OWNER"
USE = {"READY_WITH_GUARDS","CONDITIONAL","DIRECT_USE_READY"}

def clean(v: Any) -> str:
    return v.strip() if isinstance(v,str) else ""

def reviewed_learning_row(candidate: dict, verifier: Callable | None) -> dict | None:
    if not isinstance(candidate,dict) or not callable(verifier):
        return None
    if clean(candidate.get("index_state")).upper() != "INDEXED":
        return None
    keys=("source_id","source_ref","index_version","locator","content_hash")
    proposed={k:clean(candidate.get(k)) for k in keys}
    if not all(proposed.values()) or not re.fullmatch(r"[a-fA-F0-9]{64}",proposed["content_hash"]):
        return None
    try:
        owner=verifier(proposed["source_id"],dict(proposed))
    except Exception:
        return None
    if not isinstance(owner,dict):
        return None
    receipt=owner.get("receipt"); row=owner.get("index_row")
    if not isinstance(receipt,dict) or not isinstance(row,dict):
        return None
    refs=receipt.get("review_evidence_refs")
    if (receipt.get("issuer")!=OWNER or receipt.get("reviewed") is not True
        or receipt.get("decision")!="INDEXED"
        or not isinstance(refs,list) or not refs
        or any(not clean(ref) for ref in refs)
        or receipt.get("domain_use_authorized") is not True
        or receipt.get("canonical_promotion") is not False
        or receipt.get("current_promoted") is not False):
        return None
    for k,v in proposed.items():
        if clean(row.get(k))!=v or clean(receipt.get(k))!=v:
            return None
    if clean(row.get("index_state")).upper()!="INDEXED":
        return None
    use=clean(row.get("authorization_class")).upper()
    if use not in USE or clean(candidate.get("authorization_class")).upper()!=use:
        return None
    # Build from the trusted owner's row, never from the request-side row.
    return dict(row)
