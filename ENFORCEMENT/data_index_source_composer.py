#!/usr/bin/env python3
"""Read-only source-grounded INDEX L1 composer for the TAKY DATA scope.

This G1 experiment joins the original Source V6 with the derived utilization
CURRENT V26. It never writes those inputs, derives content hashes, promotes
classification, or promotes CURRENT. Source-original locators and reviewed
source summaries come from Source V6, never from domain value_statement.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from data_index_bridge import _read_json, _validate_current
from data_index_search import normalize_record, search

SOURCE_SCHEMA_RE = re.compile(r"^DATA_SOURCE_INDEX_[0-9]{4}-[0-9]{2}-[0-9]{2}_V([0-9]+)\.json$")
SOURCE_URL_HOSTS = {"drive.google.com", "docs.google.com"}


def _source_map(rows: Any, name: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError(f"{name}_ENTRIES_INVALID")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("source_id"), str) or not row["source_id"]:
            raise ValueError(f"{name}_SOURCE_ID_INVALID")
        sid = row["source_id"]
        if sid in result:
            raise ValueError(f"{name}_SOURCE_ID_DUPLICATE")
        result[sid] = row
    return result


def _valid_source_locator(sid: str, value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == "https" and parsed.netloc in SOURCE_URL_HOSTS
            and re.search(r"/d/([^/]+)/", parsed.path) is not None
            and re.search(r"/d/([^/]+)/", parsed.path).group(1) == sid)


def _conflict(source: dict[str, Any], util: dict[str, Any], key: str) -> bool:
    a, b = source.get(key), util.get(key)
    return bool(a and b and a != b)


def compose_source_l1(
    source_payload: dict[str, Any],
    current_payload: dict[str, Any],
    pointer_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fail closed on source identity/conflicts; attach explicit field lineage."""
    _, expected_total = _validate_current(current_payload, pointer_payload)
    source_ref = (pointer_payload.get("source_authority") or {}).get("source_index") or {}
    match = SOURCE_SCHEMA_RE.fullmatch(str(source_ref.get("name") or ""))
    if not match or source_payload.get("schema") != f"TAKY_DATA_SOURCE_INDEX_V{match.group(1)}":
        raise ValueError("SOURCE_SCHEMA_DISAGREES_WITH_CURRENT_POINTER")
    original = _source_map(source_payload.get("entries"), "SOURCE")
    utilization = _source_map(current_payload.get("source_entries"), "UTILIZATION")
    if len(original) != expected_total or set(original) != set(utilization):
        raise ValueError("SOURCE_IDS_DIFFER_FROM_CURRENT")
    source_first, derived_only, absent = 0, 0, 0
    reviewed_summary, missing_hash, candidate_group = 0, 0, 0
    records = []
    for sid, src in original.items():
        use = utilization[sid]
        if not _valid_source_locator(sid, src.get("url")):
            raise ValueError(f"SOURCE_LOCATOR_INVALID:{sid}")
        if any(_conflict(src, use, key) for key in ("title", "mime_type", "path")):
            raise ValueError(f"SOURCE_IDENTITY_CONFLICT:{sid}")
        embedded = use.get("index_l1") if isinstance(use.get("index_l1"), dict) else {}
        identity = embedded.get("identity") if isinstance(embedded.get("identity"), dict) else {}
        for key, expected in (("source_id", sid), ("canonical_title", src.get("title")), ("media_type", src.get("mime_type"))):
            if identity.get(key) and expected and identity[key] != expected:
                raise ValueError(f"EMBEDDED_IDENTITY_CONFLICT:{sid}:{key}")
        # Missing hash is UNKNOWN; group label or source ID is not digest proof.
        hash_a, hash_b = src.get("content_hash"), identity.get("content_hash") or use.get("content_hash")
        if hash_a and hash_b and hash_a != hash_b:
            raise ValueError(f"CONTENT_HASH_CONFLICT:{sid}")
        content_hash = hash_a or hash_b
        if not content_hash:
            missing_hash += 1
        family_a, family_b = src.get("source_family"), use.get("source_family")
        embedded_family = (embedded.get("classification") or {}).get("source_family")
        if family_a and family_b and family_a != family_b:
            raise ValueError(f"SOURCE_FAMILY_CONFLICT:{sid}")
        if embedded_family and family_a and embedded_family != family_a:
            raise ValueError(f"EMBEDDED_FAMILY_CONFLICT:{sid}")
        if embedded_family and family_b and embedded_family != family_b:
            raise ValueError(f"DERIVED_FAMILY_CONFLICT:{sid}")
        if family_a:
            family, family_origin = family_a, "SOURCE_V6_RECORDED"
            source_first += 1
        elif family_b or embedded_family:
            family, family_origin = family_b or embedded_family, "UTILIZATION_V26_DERIVED_CANDIDATE"
            derived_only += 1
        else:
            family, family_origin = None, "UNKNOWN"
            absent += 1
        review = src.get("review_state")
        summary = (src.get("content_summary") or src.get("summary")) if review == "CONTENT_REVIEWED" else None
        if summary:
            reviewed_summary += 1
        hints = {name: src[name] for name in ("duplicate_group", "fragment_group", "version_group", "version_relation", "temporal_group")
                 if src.get(name)}
        if hints:
            candidate_group += 1
        # No automatic EXACT_DUPLICATE_OF, unverified L2 page anchors, or
        # cross-domain utilization decisions enter the source-grounded L1.
        card = {
            "index_l1": {
                "identity": {
                    "source_id": sid,
                    "canonical_title": src.get("title"),
                    "locator": src["url"],
                    "media_type": src.get("mime_type"),
                    "content_hash": content_hash,
                    "size_bytes": src.get("size_bytes"),
                    "created_at": src.get("created_time"),
                    "modified_at": src.get("modified_time"),
                },
                "provenance": {
                    "origin_type": "DRIVE_PRESERVED_SOURCE_V6_RECORD",
                    "origin_locator": src["url"],
                    "publisher_or_account": None,
                },
                "classification": {
                    "source_family": family,
                    "source_type": None,
                    "domain_facets": [],
                    "authority_class": src.get("authority_level"),
                },
                "discovery": {"short_summary": summary, "controlled_terms": [], "keywords": [], "entities": [], "consumer_candidates": []},
                "state": {
                    "index_state": review,
                    "review_state": review,
                    "detail_available": False,
                    "current_relation": "DATA_SCOPE_SOURCE_IN_CURRENT_V26_VIEW",
                },
                "relations": [],
            }
        }
        norm = normalize_record(card)
        norm["field_lineage"] = {
            "source_id": "SOURCE_V6",
            "canonical_title": "SOURCE_V6",
            "locator": "SOURCE_V6_PRESERVED_DRIVE_COPY",
            "media_type": "SOURCE_V6",
            "short_summary": "SOURCE_V6_CONTENT_REVIEWED" if summary else "UNKNOWN_NOT_INFERRED",
            "source_family": family_origin,
            "review_state": "SOURCE_V6",
            "content_hash": "SOURCE_V6_OR_EMBEDDED_L1" if content_hash else "UNKNOWN",
        }
        norm["relation_candidates"] = hints
        norm["detail_reference_present_not_verified"] = bool(use.get("detail_l2"))
        norm["source_review_state"] = review
        records.append(norm)
    receipt = {
        "projection_authoritative": False,
        "source_index_ref_declared_from_pointer": source_ref.get("id"),
        "source_index_document_id_content_verified_by_connector": False,
        "current_pointer_modified": False,
        "current_count": expected_total,
        "original_locator_preserved": len(records),
        "source_content_reviewed_summary": reviewed_summary,
        "family_source_v6_recorded": source_first,
        "family_utilization_v26_derived_candidate": derived_only,
        "family_unknown": absent,
        "unknown_hash": missing_hash,
        "relation_candidate_sources": candidate_group,
        "content_reinspection_performed": False,
        "detail_page_fetch_performed": False,
    }
    return records, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Source V6 + V26 read-only L1 comparison and retrieval")
    parser.add_argument("--source-index", type=Path, required=True)
    parser.add_argument("--current-index", type=Path, required=True)
    parser.add_argument("--current-pointer", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be >= 1")
    try:
        records, receipt = compose_source_l1(_read_json(args.source_index), _read_json(args.current_index), _read_json(args.current_pointer))
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    result = search(records, args.query, limit=args.limit, relation_depth=0)
    for card in result["results"]:
        row = next(r for r in records if r["source_id"] == card["source_id"])
        card["field_lineage"] = row["field_lineage"]
        card["source_review_state"] = row["source_review_state"]
    result["source_composition_receipt"] = receipt
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
