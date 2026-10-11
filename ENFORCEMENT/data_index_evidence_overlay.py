#!/usr/bin/env python3
"""Attach bounded source-section notes to separately staged public discovery records.

Validates record lineage and claim-type envelope; does not independently
authenticate factual truth, grant copyright rights or acquire original content.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any

SCHEMA = "TAKY_EXTERNAL_EVIDENCE_DELTA_V1"
STATE = "STAGED_SELECTED_SECTION_EVIDENCE_NOT_CURRENT"
FACT_KIND = {
    "OFFICIAL_STANDARD": ("OFFICIAL_WEB_SELECTED_SECTIONS", "OFFICIAL_STANDARD_SELECTED_SECTION"),
    "PUBLIC_API_LISTING": ("ISSUING_PORTAL_API_DETAIL_PAGE", "OFFICIAL_API_LISTING_SELECTED_SECTION"),
    "OPEN_SOURCE_ISSUE": ("GITHUB_ISSUE_CONNECTOR_BODY", "ISSUE_AUTHOR_REPORTED_NOT_REPRODUCED"),
    "COMMUNITY_DISCUSSION": ("COMMUNITY_ORIGINAL_POST_DIRECT", "COMMUNITY_AUTHOR_REPORTED_NOT_GENERALIZED"),
}

def required(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key + "_REQUIRED")
    return value.strip()

def attach_selected_section_notes(rows: list[dict], base_manifest: dict, evidence: dict,
                                  manifest_document_id: str) -> tuple[list[dict], dict]:
    """Fail closed; source links, native IDs, privilege and CURRENT stay unchanged."""
    expected_ref = required(manifest_document_id, "PARENT_DOCUMENT_ID")
    if base_manifest.get("schema") != "TAKY_EXTERNAL_DISCOVERY_MANIFEST_V1" or base_manifest.get("state") != "STAGED_LINK_ONLY_NOT_CURRENT":
        raise ValueError("BASE_EXTERNAL_MANIFEST_INVALID")
    if evidence.get("schema") != SCHEMA or evidence.get("state") != STATE:
        raise ValueError("EVIDENCE_SCHEMA_OR_STATE_INVALID")
    if evidence.get("parent_manifest_document_id") != expected_ref:
        raise ValueError("EVIDENCE_PARENT_MANIFEST_MISMATCH")
    authority = evidence.get("authority") or {}
    for key in ("current_pointer_modified", "source_manifest_modified", "raw_full_content_acquired", "rights_for_full_text_reuse_verified"):
        if authority.get(key) is not False:
            raise ValueError("EVIDENCE_AUTHORITY_OVERCLAIM:" + key)
    hashes = authority.get("source_hashes_verified")
    if type(hashes) is not int or hashes != 0:
        raise ValueError("EVIDENCE_HASH_PROOF_NOT_ALLOWED")
    originals, entries = base_manifest.get("sources"), evidence.get("entries")
    if not isinstance(originals, list) or not isinstance(entries, list) or not isinstance(rows, list):
        raise ValueError("EVIDENCE_ENTRIES_INVALID")
    if not originals or len(originals) != len(entries) or len(rows) != len(originals):
        raise ValueError("EVIDENCE_COVERAGE_MISMATCH")
    by_id = {}
    for original in originals:
        sid = "EXTERNAL::" + required(original.get("external_namespace"), "NAMESPACE") + "::" + required(original.get("provider_native_id"), "NATIVE_ID")
        if sid in by_id:
            raise ValueError("BASE_NATIVE_ID_COLLISION")
        by_id[sid] = original
    if len({r.get("source_id") for r in rows}) != len(rows) or {r.get("source_id") for r in rows} != set(by_id):
        raise ValueError("PROJECTED_SOURCE_ID_MISMATCH")
    attached = {}
    for note in entries:
        if not isinstance(note, dict):
            raise ValueError("EVIDENCE_ENTRY_INVALID")
        sid = required(note.get("source_id"), "EVIDENCE_SOURCE_ID")
        if sid not in by_id or sid in attached:
            raise ValueError("EVIDENCE_UNKNOWN_OR_DUPLICATE_ID")
        original = by_id[sid]
        if note.get("original_locator") != original.get("original_locator") or note.get("source_kind") != original.get("source_kind"):
            raise ValueError("EVIDENCE_ORIGIN_OR_ROLE_MISMATCH")
        kind = original["source_kind"]
        if kind not in FACT_KIND or (note.get("inspection_method"), note.get("fact_status")) != FACT_KIND[kind]:
            raise ValueError("EVIDENCE_METHOD_OR_FACT_ROLE_INVALID")
        summary = required(note.get("evidence_summary"), "EVIDENCE_SUMMARY")
        if len(summary) < 25 or len(summary) > 500:
            raise ValueError("EVIDENCE_SUMMARY_BOUNDS_INVALID")
        for key in ("section_ref", "reviewed_at", "limits"):
            required(note.get(key), "EVIDENCE_" + key.upper())
        if (note.get("content_hash") is not None or note.get("full_content_acquired") is not False
            or note.get("rights_verified") is not False or note.get("reuse_scope") != "SHORT_ORIGINAL_PARAPHRASE_ONLY"
            or note.get("detail_location_verified") != "SECTION_LABEL_NOT_SPATIAL_BBOX"):
            raise ValueError("EVIDENCE_CONTENT_OR_RIGHTS_OVERCLAIM")
        attached[sid] = note
    out = deepcopy(rows)
    for record in out:
        sid = record["source_id"]
        note = attached[sid]
        if (record.get("locator") != note["original_locator"] or record.get("content_hash") is not None
            or record.get("current_relation") != "NO_CURRENT_PROMOTION" or record.get("detail_available") is not False
            or record.get("intake_envelope", {}).get("privacy_class") != "PUBLIC"):
            raise ValueError("EVIDENCE_PROJECTION_BOUNDARY_INVALID")
        if record.get("short_summary"):
            raise ValueError("EVIDENCE_WOULD_OVERWRITE_EXISTING_SUMMARY")
        record["short_summary"] = note["evidence_summary"]
        record["evidence_note"] = {
            "section_ref": note["section_ref"], "inspection_method": note["inspection_method"],
            "fact_status": note["fact_status"], "reviewed_at": note["reviewed_at"],
            "source_ref": note["original_locator"], "limits": note["limits"],
            "scope": "SELECTED_SOURCE_SECTION_ONLY", "full_text_acquired": False,
            "rights_verified": False, "authority_not_promoted": True,
        }
    return out, {"state": STATE, "notes_joined": len(out), "full_content_acquired": False,
                 "rights_verified": False, "current_promoted": False,
                 "original_source_count_unchanged": True,
                 "evidence_authenticated_cryptographically": False}
