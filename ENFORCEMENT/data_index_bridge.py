#!/usr/bin/env python3
"""Explicit, non-authoritative external Source Universe bridge for TAKY search.

Locally synced CURRENT, CURRENT pointer and staged Drive manifest are read only.
No RAW upload, silent merge, policy decision or CURRENT pointer mutation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from data_index_search import load_index, normalize_record, search

BRIDGE_SCHEMA = "TAKY_INDEX_INCREMENTAL_SOURCE_RELATION_BRIDGE_V1"
BRIDGE_STATE = "STAGED_VERIFIED_DELTA_NON_PROMOTION"
DRIVE_SOURCE_RE = re.compile(r"^https://drive\.google\.com/file/d/([^/]+)/view(?:\?.*)?$")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _validate_current(current: dict[str, Any], pointer: dict[str, Any]) -> tuple[str, int]:
    link = pointer.get("current_utilization_index") or {}
    expected_id = link.get("id")
    expected_name = link.get("name")
    expected_total = (pointer.get("current_status") or {}).get("total")
    expected_source = ((pointer.get("source_authority") or {}).get("source_index") or {}).get("id")
    if not all([expected_id, expected_name, isinstance(expected_total, int), expected_source]):
        raise ValueError("CURRENT pointer is incomplete")
    if current.get("schema") != f"TAKY_DATA_UTILIZATION_INDEX_V{expected_name.split('_V')[-1].split('.')[0]}":
        raise ValueError("CURRENT schema disagrees with pointer")
    if ((current.get("source_authority") or {}).get("source_index_id")) != expected_source:
        raise ValueError("CURRENT source authority disagrees with pointer")
    entries = current.get("source_entries")
    if not isinstance(entries, list) or len(entries) != expected_total:
        raise ValueError("CURRENT source count disagrees with pointer")
    ids = [r.get("source_id") for r in entries if isinstance(r, dict)]
    if len(ids) != expected_total or len(set(ids)) != expected_total or not all(ids):
        raise ValueError("CURRENT source IDs invalid or duplicated")
    return expected_id, expected_total


def validate_and_project_bridge(bridge: dict[str, Any], expected_current_id: str) -> list[dict[str, Any]]:
    if bridge.get("schema") != BRIDGE_SCHEMA or bridge.get("state") != BRIDGE_STATE:
        raise ValueError("unsupported bridge schema or state")
    boundary = bridge.get("authority_boundaries") or {}
    if boundary.get("current_utilization_index") != expected_current_id:
        raise ValueError("bridge pinned to a different CURRENT index")
    if boundary.get("current_pointer_modified") is not False or boundary.get("cross_universe_relation_bridge_not_auto_add_to_679") is not True:
        raise ValueError("bridge would imply unapproved CURRENT promotion")
    family = (bridge.get("source_family") or {}).get("family_id")
    if not isinstance(family, str) or not family:
        raise ValueError("missing source family")
    entries, pairs = bridge.get("source_entries"), bridge.get("pair_relations")
    if not isinstance(entries, list) or not isinstance(pairs, list) or not entries or not pairs:
        raise ValueError("bridge must contain original source entries and pair relations")
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("non-object source entry")
        sid = entry.get("source_id")
        match = DRIVE_SOURCE_RE.fullmatch(str(entry.get("locator") or ""))
        if not isinstance(sid, str) or not sid or sid in by_id or not match or match.group(1) != sid:
            raise ValueError("duplicate/invalid source identity or locator")
        if entry.get("source_family") != family or entry.get("media_type") != "application/pdf":
            raise ValueError("source family or media type disagrees")
        if entry.get("content_hash") is not None or entry.get("hash_state") != "NOT_PROVIDED":
            raise ValueError("unverified source hash must remain unknown")
        by_id[sid] = entry
    seen_pairs: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError("invalid pair relation")
        pid, stu, tea = pair.get("pair_id"), pair.get("student_source_id"), pair.get("teacher_source_id")
        if not pid or pid in seen_pairs or stu == tea or stu not in by_id or tea not in by_id:
            raise ValueError("pair ID or endpoints invalid")
        seen_pairs.add(pid)
        for role, sid, other in (("student", stu, tea), ("teacher", tea, stu)):
            entry = by_id[sid]
            if entry.get("pair_id") != pid or entry.get("source_role") != role or entry.get("grade_band") != pair.get("grade_band") or entry.get("genre") != pair.get("genre"):
                raise ValueError("pair metadata mismatch")
            edges = entry.get("relations") or []
            if not any(isinstance(e, dict) and e.get("type") == "RELATED_TO" and e.get("target") == other and e.get("qualifier") == "STUDENT_TEACHER_PAIR" for e in edges):
                raise ValueError("pair must have verified reciprocal relationship")
    if len(by_id) != 2 * len(pairs) or any(e.get("pair_id") not in seen_pairs for e in by_id.values()):
        raise ValueError("every original must belong to exactly one verified student/teacher pair")
    projected = []
    for entry in entries:
        pair = next(p for p in pairs if p["pair_id"] == entry["pair_id"])
        role = entry["source_role"]
        other = pair["teacher_source_id"] if role == "student" else pair["student_source_id"]
        relations = []
        for edge in entry["relations"]:
            if (edge.get("type") == "RELATED_TO" and edge.get("target") == other
                    and edge.get("qualifier") == "STUDENT_TEACHER_PAIR"):
                # The reciprocal pair was validated above, but neither PDF content
                # nor independent owner approval is promoted by this annotation.
                relations.append({**edge, "verification_state": "STAGED_MANIFEST_VALIDATED",
                                  "evidence_ref": "BRIDGE_MANIFEST_PAIR:" + pair["pair_id"],
                                  "verification_scope": "RECIPROCAL_METADATA_ONLY"})
            else:
                relations.append(dict(edge))
        record = {
            "index_l1": {
                "identity": {"source_id": entry["source_id"], "canonical_title": entry["canonical_title"], "locator": entry["locator"], "media_type": entry["media_type"], "content_hash": None},
                "provenance": {"origin_type": entry["origin_type"], "origin_locator": (bridge.get("source_family") or {}).get("original_official_listing"), "publisher_or_account": (bridge.get("source_family") or {}).get("publisher")},
                "classification": {"source_family": family, "source_type": f"OFFICIAL_INSTRUCTIONAL_{role.upper()}_PDF", "authority_class": entry["authority_class"], "domain_facets": ["EDUCATION", "KOREAN_WRITING", f"GRADE_{entry['grade_band']}", f"GENRE_{entry['genre'].upper()}"]},
                "discovery": {"short_summary": f"{pair['title']} ({'학생용' if role == 'student' else '교사용'})", "controlled_terms": [pair["title"], str(pair["printed_standard_code"])], "keywords": [str(x) for x in pair.get("keywords", [])] + ["학생용" if role == "student" else "교사용"], "entities": [(bridge.get("source_family") or {}).get("publisher")], "consumer_candidates": []},
                "state": {"index_state": "BRIDGE_STAGED", "detail_available": False, "review_state": entry["review_state"], "current_relation": "EXTERNAL_BRIDGE_STAGED"},
                "relations": relations,
            },
            # A section hint is not a verified PDF page anchor: no fabricated DETAIL_L2.
        }
        normalized = normalize_record(record)
        normalized["field_lineage"] = {
            "source_family": "STAGED_MANIFEST_METADATA_NOT_CURRENT",
            "short_summary": "STAGED_PAIR_METADATA_NOT_PDF_CONTENT_REVIEW",
            "review_state": "STAGED_SOURCE_ENTRY",
        }
        projected.append(normalized)
    return projected


def load_explicit_overlay(index_path: Path, pointer_path: Path, bridge_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    primary, pointer = _read_json(index_path), _read_json(pointer_path)
    expected_id, expected_count = _validate_current(primary, pointer)
    base = load_index(index_path)
    if len(base) != expected_count:
        raise ValueError("CURRENT projection lost source rows")
    extra = validate_and_project_bridge(_read_json(bridge_path), expected_id)
    base_ids = {r["source_id"] for r in base}
    if base_ids.intersection(r["source_id"] for r in extra):
        raise ValueError("external bridge collides with existing CURRENT source ID; resolve explicitly")
    info = {"current_utilization_index_id": expected_id, "current_corpus_count": expected_count, "external_bridge_count": len(extra), "current_pointer_modified": False, "external_bridge_state": BRIDGE_STATE}
    return base + extra, info



def load_source_grounded_universe(source_index_path, current_index_path, pointer_path, bridge_path, external_manifest_path=None, external_evidence_path=None, external_manifest_document_id=None):
    """Read-only compose: 679 source-authoritative DATA + separately staged candidates."""
    from data_index_source_composer import compose_source_l1
    from data_index_external_intake import stage_external_candidates
    from data_index_evidence_overlay import attach_selected_section_notes
    current, pointer = _read_json(current_index_path), _read_json(pointer_path)
    expected_id, expected_count = _validate_current(current, pointer)
    base, source_receipt = compose_source_l1(_read_json(source_index_path), current, pointer)
    if len(base) != expected_count:
        raise ValueError("SOURCE_GROUNDED_COUNT_MISMATCH")
    bridge = validate_and_project_bridge(_read_json(bridge_path), expected_id)
    source_ids = {r["source_id"] for r in base}
    bridge_ids = {r["source_id"] for r in bridge}
    if len(bridge_ids) != len(bridge) or source_ids & bridge_ids:
        raise ValueError("BRIDGE_SOURCE_ID_COLLISION")
    external, external_receipt = [], {"state": "NOT_SUPPLIED", "candidate_count": 0}
    if external_manifest_path is not None:
        manifest = _read_json(external_manifest_path)
        boundary = manifest.get("authority") or {}
        if (manifest.get("schema") != "TAKY_EXTERNAL_DISCOVERY_MANIFEST_V1"
            or manifest.get("state") != "STAGED_LINK_ONLY_NOT_CURRENT"
            or boundary.get("current_pointer_modified") is not False
            or boundary.get("external_original_content_acquired") is not False
            or boundary.get("corpus_addition_to_DATA_679") is not False):
            raise ValueError("EXTERNAL_MANIFEST_AUTHORITY_INVALID")
        external, external_receipt = stage_external_candidates(
            manifest.get("sources"), existing_source_ids=source_ids | bridge_ids)
        if any(r["intake_envelope"]["privacy_class"] != "PUBLIC" for r in external):
            raise ValueError("EXTERNAL_PRIVATE_SOURCE_NOT_ELIGIBLE_FOR_PUBLIC_PROJECTION")
    evidence_receipt = {"state": "NOT_SUPPLIED", "notes_joined": 0}
    if external_evidence_path is not None:
        if external_manifest_path is None or not external_manifest_document_id:
            raise ValueError("EVIDENCE_REQUIRES_MANIFEST_AND_DOCUMENT_ID")
        external, evidence_receipt = attach_selected_section_notes(
            external, manifest, _read_json(external_evidence_path),
            external_manifest_document_id,
        )
    records = base + bridge + external
    if len({r["source_id"] for r in records}) != len(records):
        raise ValueError("UNIVERSE_SOURCE_ID_COLLISION")
    return records, {
        "projection_authoritative": False, "source_grounded": source_receipt,
        "data_current_count": expected_count, "writing_originals_staged_count": len(bridge),
        "external_discovery_link_only_count": len(external),
        "temporary_retrieval_candidate_count": len(records),
        "data_current_pointer_modified": False, "external_staged_not_current": True,
        "original_files_copied": False, "detail_content_auto_verified": False,
        "external_receipt": external_receipt,
        "external_evidence_receipt": evidence_receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search CURRENT plus separately staged external relation bridge")
    parser.add_argument("--current-index", required=True, type=Path)
    parser.add_argument("--current-pointer", required=True, type=Path)
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--source-index", type=Path)
    parser.add_argument("--external-manifest", type=Path)
    parser.add_argument("--external-evidence", type=Path)
    parser.add_argument("--external-manifest-doc-id")
    parser.add_argument("--query", required=True)
    parser.add_argument("--context-source-id", help="Explicit read-only one-hop relationship context for an authorized source ID")
    parser.add_argument("--require-relation-type", action="append", default=[], help="Relation type required for this context request; repeatable")
    parser.add_argument("--emit-context-gaps", action="store_true", help="Emit read-only Index-first gap proposals; never dispatch")
    parser.add_argument("--context-scope-namespace", help="Explicit namespace for gap proposals")
    parser.add_argument("--context-privacy-class", choices=["PUBLIC", "AUTHORIZED_PRIVATE", "RESTRICTED"])
    parser.add_argument("--context-raw-access", choices=["NOT_CHECKED", "ACCESSIBLE", "PARTIAL", "MISSING", "DENIED"], default="NOT_CHECKED")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--filter", action="append", default=[])
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("limit must be positive")
    if args.require_relation_type and not args.context_source_id:
        parser.error("--require-relation-type requires --context-source-id")
    if args.emit_context_gaps and not (args.context_source_id and args.context_scope_namespace and args.context_privacy_class):
        parser.error("--emit-context-gaps needs --context-source-id, --context-scope-namespace and --context-privacy-class")
    filters = {}
    for arg in args.filter:
        if "=" not in arg:
            parser.error("filter must be key=value")
        key, val = arg.split("=", 1)
        if not key.strip() or not val.strip():
            parser.error("filter key and value must be non-empty")
        filters[key.strip()] = val.strip()
    try:
        if args.external_evidence and (not args.external_manifest or not args.external_manifest_doc_id):
            parser.error("--external-evidence requires --external-manifest and --external-manifest-doc-id")
        if args.external_manifest and not args.source_index:
            parser.error("--external-manifest requires --source-index")
        if args.source_index:
            records, info = load_source_grounded_universe(args.source_index, args.current_index, args.current_pointer, args.bridge, args.external_manifest, args.external_evidence, args.external_manifest_doc_id)
        else:
            records, info = load_explicit_overlay(args.current_index, args.current_pointer, args.bridge)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    result = search(records, args.query, filters=filters, limit=args.limit)
    if args.context_source_id:
        from data_index_relation_context import assemble_relation_context
        from data_index_search import apply_filters
        eligible = {row["source_id"] for row in apply_filters(records, filters)}
        try:
            result["relation_context"] = assemble_relation_context(
                records, args.context_source_id, eligible_ids=eligible,
                required_types=set(args.require_relation_type))
        except ValueError as exc:
            parser.error(str(exc))
        if args.emit_context_gaps:
            from data_index_gap_router import proposals_from_relation_context
            try:
                result["index_gap_routing"] = proposals_from_relation_context(
                    result["relation_context"], scope_namespace=args.context_scope_namespace,
                    privacy_class=args.context_privacy_class, raw_access=args.context_raw_access)
            except ValueError as exc:
                parser.error(str(exc))
    result["overlay_provenance"] = info
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
