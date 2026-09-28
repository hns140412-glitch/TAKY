#!/usr/bin/env python3
"""TAKY INDEX -> MINING gap handoff, read-only proposal builder.

Routing does not acquire sources, dispatch a task, mutate CURRENT, turn a
search result into source authority, or decide a consuming-domain policy.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

ROUTES = ("INDEXING_PRECHECK", "INDEXING_INTERNAL", "MINING_REQUEST_DRAFT", "DOMAIN_CONSUMER")
KINDS = {
    "ORIGINAL_MISSING", "ACCESS_BLOCKED", "PRIMARY_PROVENANCE_MISSING",
    "VERSION_UNRESOLVED", "CONTRADICTORY_SOURCES", "COVERAGE_MISSING",
    "DETAIL_ANCHOR_MISSING", "CLASSIFICATION_AMBIGUOUS", "RETRIEVAL_LOW_RECALL",
    "DUPLICATE_PROOF_MISSING", "RIGHTS_UNCLEAR", "DOMAIN_POLICY_QUESTION",
}
INDEX_CHECKS = {"NOT_CHECKED", "CHECKED_PRESENT", "CHECKED_MISSING", "CHECKED_INSUFFICIENT"}
RAW_ACCESS = {"NOT_CHECKED", "ACCESSIBLE", "PARTIAL", "MISSING", "DENIED"}
PRIVACY = {"PUBLIC", "AUTHORIZED_PRIVATE", "RESTRICTED"}
PROOF_NEEDED = {"ORIGINAL_MISSING", "ACCESS_BLOCKED", "PRIMARY_PROVENANCE_MISSING", "VERSION_UNRESOLVED", "CONTRADICTORY_SOURCES", "COVERAGE_MISSING", "RIGHTS_UNCLEAR"}
INDEX_FIRST = {"DETAIL_ANCHOR_MISSING", "CLASSIFICATION_AMBIGUOUS", "RETRIEVAL_LOW_RECALL", "DUPLICATE_PROOF_MISSING"}


def _required(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}_REQUIRED")
    return value.strip()


def build_gap_proposal(gap: dict[str, Any]) -> dict[str, Any]:
    """Produce a deterministic, deduplicatable candidate with human-review state."""
    if not isinstance(gap, dict):
        raise ValueError("GAP_OBJECT_REQUIRED")
    kind = _required(gap.get("gap_kind"), "GAP_KIND")
    if kind not in KINDS:
        raise ValueError("GAP_KIND_UNSUPPORTED")
    scope = _required(gap.get("scope_namespace"), "SCOPE_NAMESPACE")
    question = _required(gap.get("evidence_question"), "EVIDENCE_QUESTION")
    desired = _required(gap.get("desired_evidence"), "DESIRED_EVIDENCE")
    insufficient = _required(gap.get("why_index_insufficient"), "INSUFFICIENCY")
    index_check = gap.get("index_check")
    raw_access = gap.get("raw_access")
    privacy = gap.get("privacy_class")
    if index_check not in INDEX_CHECKS or raw_access not in RAW_ACCESS or privacy not in PRIVACY:
        raise ValueError("GAP_STATE_INVALID")
    refs = gap.get("source_refs")
    if not isinstance(refs, list) or any(not isinstance(r, str) or not r.strip() for r in refs):
        raise ValueError("SOURCE_REFS_INVALID")
    refs = sorted(set(refs))
    if len(refs) > 20:
        raise ValueError("SOURCE_REFS_TOO_MANY")
    attempts = gap.get("attempted_checks")
    if not isinstance(attempts, list) or any(not isinstance(a, str) or not a.strip() for a in attempts):
        raise ValueError("ATTEMPTED_CHECKS_INVALID")
    min_authority = _required(gap.get("minimum_authority"), "MINIMUM_AUTHORITY")
    freshness = _required(gap.get("freshness_requirement"), "FRESHNESS_REQUIREMENT")
    if kind == "DOMAIN_POLICY_QUESTION":
        route, reason = "DOMAIN_CONSUMER", "DOMAIN_DECISION_NOT_INDEX_OR_MINING"
    elif index_check == "NOT_CHECKED":
        route, reason = "INDEXING_PRECHECK", "CHECK_INDEX_BEFORE_MINING"
    elif kind in INDEX_FIRST and raw_access == "ACCESSIBLE":
        route, reason = "INDEXING_INTERNAL", "SOURCE_AVAILABLE_INDEX_OR_DETAIL_WORK"
    elif kind in INDEX_FIRST and raw_access == "NOT_CHECKED":
        route, reason = "INDEXING_PRECHECK", "CHECK_EXISTING_RAW_BEFORE_ACQUISITION"
    elif kind in PROOF_NEEDED and index_check == "CHECKED_PRESENT" and raw_access == "ACCESSIBLE" and kind not in {"VERSION_UNRESOLVED", "CONTRADICTORY_SOURCES", "COVERAGE_MISSING", "PRIMARY_PROVENANCE_MISSING", "RIGHTS_UNCLEAR"}:
        route, reason = "INDEXING_INTERNAL", "EXISTING_SOURCE_CAN_BE_VALIDATED_INTERNALLY"
    elif kind in PROOF_NEEDED or (kind in INDEX_FIRST and raw_access in {"MISSING", "PARTIAL", "DENIED"}):
        route, reason = "MINING_REQUEST_DRAFT", "ADDITIONAL_OR_ALTERNATE_SOURCE_EVIDENCE_REQUIRED"
    else:
        route, reason = "INDEXING_INTERNAL", "CHECK_SOURCE_EVIDENCE_IN_INDEX_FIRST"
    identity = {"scope_namespace": scope, "gap_kind": kind, "source_refs": refs, "evidence_question": question,
                "desired_evidence": desired, "why_index_insufficient": insufficient}
    stable_id = "IGAP-" + hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]
    privacy_constraint = ("NO_EXTERNAL_ACCOUNT_DISCLOSURE" if privacy != "PUBLIC" else "PUBLIC_SOURCE_METADATA_ALLOWED")
    response = {
        "schema": "TAKY_INDEX_EVIDENCE_GAP_PROPOSAL_V1",
        "request_id": stable_id,
        "state": "DRAFT_NOT_DISPATCHED",
        "route": route,
        "route_reason": reason,
        "index_evidence": {"scope_namespace": scope, "gap_kind": kind, "source_refs": refs,
                           "index_check": index_check, "raw_access": raw_access,
                           "attempted_checks": attempts, "why_index_insufficient": insufficient},
        "mining_handoff": {
            "evidence_gap": question,
            "desired_evidence_type": desired,
            "minimum_authority": min_authority,
            "freshness_requirement": freshness,
            "search_constraints": {"privacy_class": privacy, "privacy_constraint": privacy_constraint,
                                   "rights_state": gap.get("rights_state") or "UNKNOWN",
                                   "do_not_assume_source_is_verified": True,
                                   "do_not_overwrite_existing_raw": True},
            "expected_return": ["candidate_original_locator", "provider_native_id", "acquisition_receipt_or_link_only_status",
                                "observed_at", "origin_and_license_evidence", "source_access_status", "limitations_or_counterevidence"],
        } if route == "MINING_REQUEST_DRAFT" else None,
        "indexing_resume": {"validate_intake_first": True, "rerun_evidence_gap_check": True,
                            "rebuild_non_authoritative_projection_if_changed": True,
                            "current_promotion": "REQUIRES_SEPARATE_APPROVAL"},
        "actions_performed": [],
    }
    return response


def deduplicate_proposals(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for gap in gaps:
        proposal = build_gap_proposal(gap)
        by_id.setdefault(proposal["request_id"], proposal)
    return list(by_id.values())


def validate_mining_return(receipt: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Validate a mining response envelope without accepting its content as canonical."""
    if request.get("schema") != "TAKY_INDEX_EVIDENCE_GAP_PROPOSAL_V1" or request.get("route") != "MINING_REQUEST_DRAFT":
        raise ValueError("MINING_REQUEST_NOT_ELIGIBLE")
    if receipt.get("request_id") != request.get("request_id"):
        raise ValueError("MINING_REQUEST_ID_MISMATCH")
    status = receipt.get("outcome")
    if status not in {"ACQUIRED", "LINK_ONLY", "NOT_FOUND", "BLOCKED", "CONTRADICTORY_EVIDENCE"}:
        raise ValueError("MINING_OUTCOME_INVALID")
    if status in {"ACQUIRED", "LINK_ONLY", "CONTRADICTORY_EVIDENCE"}:
        for field in ("provider_native_id", "original_locator", "observed_at", "provenance_evidence", "access_status"):
            _required(receipt.get(field), field.upper())
    return {"request_id": request["request_id"], "outcome": status,
            "state": "RETURNED_FOR_INDEX_VALIDATION_NOT_CANONICAL",
            "current_promotion": False, "raw_overwritten": False,
            "indexing_next": "VALIDATE_SOURCE_ID_PROVENANCE_RIGHTS_CONTENT_AND_RELATIONS" if status in {"ACQUIRED", "LINK_ONLY", "CONTRADICTORY_EVIDENCE"} else "KEEP_EVIDENCE_GAP_OPEN"}
