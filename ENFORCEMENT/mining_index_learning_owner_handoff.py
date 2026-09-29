#!/usr/bin/env python3
"""Fail-closed, noncanonical Index-owner receipt -> Learning requery handoff.

Reference: PR #167 owner-verifier identity boundary and PR #174 staged source
projection. This is an isolated cross-engine adapter, not a merge or canonical
Index writer. A trusted host must independently supply the verifier, and the
Index owner supplies the reviewed row. Candidate/provider input cannot do so.
"""
from __future__ import annotations
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit
from learning_mining_gap_loop import requery_learning

OWNER = "INDEXING_OWNER"
STAGED = {"CANDIDATE", "STAGED", "PENDING", "HELD", "REJECTED", "EXTERNAL_DISCOVERY_STAGED", "BRIDGE_STAGED"}
USE_CLASSES = {"READY_WITH_GUARDS", "CONDITIONAL", "DIRECT_USE_READY"}
RELATIONS = {"EXACT_DUPLICATE_OF", "VERSION_OF", "SUPERSEDES", "NEW_SOURCE"}

def _clean(v: Any) -> str:
    return v.strip() if isinstance(v, str) else ""

def _hold(reason: str, *, candidate: dict | None = None) -> dict:
    return {
        "schema": "TAKY_MINING_INDEX_LEARNING_OWNER_HANDOFF_V1",
        "state": "HOLD_INDEX_OWNER",
        "reason": reason,
        "candidate_id": _clean((candidate or {}).get("candidate_id")),
        "index_rows_changed": False,
        "current_promoted": False,
        "learning_use_authorized": False,
        "learning_requery": None,
    }

def bind_owner_reviewed_source(
    candidate: dict,
    existing_index_rows: list[dict],
    learning_payload: dict,
    *,
    owner_verifier: Callable[[str, dict], object] | None = None,
) -> dict:
    """Accept *only* an independently host-injected Index owner response.

    The proposal and untrusted candidate are read-only. This does not attest
    the host's credential provisioning or independently inspect RAW bytes.
    """
    if not isinstance(candidate, dict):
        return _hold("CANDIDATE_INVALID")
    cid = _clean(candidate.get("candidate_id"))
    identity = candidate.get("identity") or {}
    if not isinstance(identity, dict):
        return _hold("CANDIDATE_IDENTITY_INVALID", candidate=candidate)
    sid = _clean(identity.get("source_id"))
    locator = _clean(identity.get("locator"))
    digest = _clean(identity.get("content_hash")).lower()
    if not cid or not sid or sid != cid:
        return _hold("CANDIDATE_SOURCE_BINDING_INVALID", candidate=candidate)
    parsed = urlsplit(locator)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return _hold("CANDIDATE_LOCATOR_INVALID", candidate=candidate)
    if digest and (len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
        return _hold("CANDIDATE_HASH_INVALID", candidate=candidate)
    if not callable(owner_verifier):
        return _hold("INDEX_OWNER_VERIFIER_NOT_CONFIGURED", candidate=candidate)
    existing = {str(x.get("source_id") or ""): x for x in existing_index_rows or []}
    if sid in existing:
        return _hold("CANDIDATE_COLLIDES_WITH_INDEX_OWNER_ID", candidate=candidate)

    # Only a host-owned callback can return a reviewed receipt + authoritative
    # row; never read 'verified', 'issuer', or 'index_result' from candidate.
    proposal = {"candidate_id": cid, "source_id": sid, "locator": locator,
                "content_hash": digest or None}
    try:
        review = owner_verifier(sid, dict(proposal))
    except Exception:
        return _hold("INDEX_OWNER_REVIEW_UNAVAILABLE", candidate=candidate)
    if not isinstance(review, dict):
        return _hold("INDEX_OWNER_RECEIPT_MISSING", candidate=candidate)
    receipt = review.get("receipt")
    row = review.get("index_row")
    if not isinstance(receipt, dict) or not isinstance(row, dict):
        return _hold("INDEX_OWNER_RECEIPT_OR_ROW_MISSING", candidate=candidate)
    refs = receipt.get("review_evidence_refs")
    expected = ("source_id", "source_ref", "index_version", "locator")
    if (receipt.get("issuer") != OWNER or receipt.get("reviewed") is not True
        or receipt.get("decision") != "INDEXED"
        or not all(_clean(receipt.get(k)) for k in expected)
        or not isinstance(refs, list) or not refs
        or any(not _clean(x) for x in refs)
        or receipt["source_id"] != sid or receipt["locator"] != locator
        or row.get("source_id") != sid or row.get("locator") != locator
        or row.get("source_ref") != receipt["source_ref"]
        or row.get("index_version") != receipt["index_version"]):
        return _hold("INDEPENDENT_INDEX_RECEIPT_INVALID", candidate=candidate)
    if digest and (receipt.get("content_hash") != digest or row.get("content_hash") != digest):
        return _hold("INDEX_OWNER_HASH_BINDING_MISMATCH", candidate=candidate)
    if row.get("content_hash") and receipt.get("content_hash") != row.get("content_hash"):
        return _hold("INDEX_OWNER_HASH_BINDING_MISMATCH", candidate=candidate)
    relation = receipt.get("relation")
    if not isinstance(relation, dict) or relation.get("type") not in RELATIONS:
        return _hold("INDEX_RELATION_NOT_REVIEWED", candidate=candidate)
    relation_type = relation["type"]
    target = _clean(relation.get("target_source_id"))
    if relation_type == "NEW_SOURCE" and target:
        return _hold("NEW_SOURCE_RELATION_HAS_TARGET", candidate=candidate)
    if relation_type != "NEW_SOURCE" and (not target or target not in existing or target == sid):
        return _hold("INDEX_RELATION_TARGET_INVALID", candidate=candidate)
    if (relation_type == "EXACT_DUPLICATE_OF"
        and (not row.get("content_hash") or row["content_hash"] != existing[target].get("content_hash"))):
        return _hold("EXACT_DUPLICATE_HASH_NOT_PROVEN", candidate=candidate)
    state = _clean(row.get("index_state")).upper()
    if not state or state in STAGED:
        return _hold("OWNER_ROW_NOT_INDEXED", candidate=candidate)
    use = _clean(row.get("authorization_class")).upper()
    if use not in USE_CLASSES:
        return _hold("DOMAIN_USE_NOT_AUTHORIZED", candidate=candidate)
    if receipt.get("domain_use_authorized") is not True:
        return _hold("OWNER_DOMAIN_USE_RECEIPT_MISSING", candidate=candidate)
    if receipt.get("canonical_promotion") is not False or receipt.get("current_promoted") is not False:
        return _hold("UNAUTHORIZED_CURRENT_PROMOTION", candidate=candidate)
    if not isinstance(learning_payload, dict):
        return _hold("LEARNING_PAYLOAD_INVALID", candidate=candidate)
    # A source/version is not renamed and a staged candidate is never treated
    # as a verified row. Only the actual owner-reviewed row is appended.
    updated = list(existing_index_rows or []) + [dict(row)]
    result = requery_learning(learning_payload, updated)
    return {
        "schema": "TAKY_MINING_INDEX_LEARNING_OWNER_HANDOFF_V1",
        "state": "OWNER_REVIEWED_REQUERY",
        "candidate_id": cid,
        "source_id": sid,
        "source_ref": receipt["source_ref"],
        "index_version": receipt["index_version"],
        "relation": dict(relation),
        "review_evidence_refs": list(refs),
        "index_rows_changed": False,  # only an ephemeral reviewed projection
        "reviewed_projection_count": len(updated),
        "current_promoted": False,
        "learning_use_authorized": True,  # explicitly domain-owner authorized
        "learning_requery": result,
        "guards": {"trusted_host_verifier_required": True,
                   "no_candidate_self_approval": True,
                   "owner_row_only": True,
                   "no_canonical_write": True,
                   "planner_date_not_assigned": True},
    }
