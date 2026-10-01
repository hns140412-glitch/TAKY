#!/usr/bin/env python3
"""Bridge shared Index Retrieval Runtime into Mining without merging roles.

Retrieval can locate candidate sources; it cannot establish evidence sufficiency
or replace the domain owner's utilization decision. Only uncovered source gaps
need external acquisition, while retrieved candidates still require verification.
"""
from __future__ import annotations
from index_retrieval import retrieve
from urllib.parse import unquote, urlsplit
import re
import unicodedata


def _filename(value):
    """Normalize only presentation differences; never match by topic/snippet."""
    v=unicodedata.normalize("NFKC",unquote(str(value or ""))).strip()
    if not v: return ""
    if "://" in v:
        v=urlsplit(v).path
    v=v.replace("\\","/").rsplit("/",1)[-1]
    return " ".join(v.split()).casefold().strip()


def _exact_source_file(row, expected):
    wanted=_filename(expected)
    if not wanted: return False
    identity=row.get("identity") if isinstance(row.get("identity"),dict) else {}
    for value in (row.get("canonical_title"), row.get("title"),
                  row.get("locator"), row.get("path"),
                  identity.get("canonical_title"), identity.get("locator")):
        if _filename(value)==wanted: return True
    return False


def _candidate_usable(row: dict) -> bool:
    """Reject explicitly stale or held records as satisfying an index-first gap.

    Unknown status is allowed as a retrieval candidate for backward compatibility,
    but no retrieved candidate is marked as verified *evidence* here.
    """
    state = row.get("state") if isinstance(row.get("state"), dict) else {}
    for key in ("stale_state", "review_state", "index_state", "current_relation"):
        value = str(row.get(key) or state.get(key) or "").upper()
        if (value.startswith(("STALE", "SUPERSEDED", "REJECTED", "HELD", "HOLD"))
                or value in {"REVIEW_REQUIRED", "REFERENCE_ONLY", "UNVERIFIED"}):
            return False
    authority = row.get("authority_class") or (row.get("classification") or {}).get("authority_class")
    if str(authority or "").upper() in {"REFERENCE_ONLY", "UNKNOWN_UNVERIFIED"}:
        return False
    return True


def _excluded_candidate_reason(row: dict) -> str | None:
    state = row.get("state") if isinstance(row.get("state"), dict) else {}
    for key in ("stale_state", "current_relation", "review_state", "index_state"):
        value = str(row.get(key) or state.get(key) or "").upper()
        if value.startswith("STALE"):
            return "STALE"
        if value.startswith("SUPERSEDED"):
            return "SUPERSEDED"
        if value.startswith(("HELD", "HOLD")):
            return "SOURCE_REVIEW_HOLD"
        if value.startswith("REJECTED"):
            return "REJECTED"
        if value in {"REVIEW_REQUIRED", "REFERENCE_ONLY", "UNVERIFIED"}:
            return "SOURCE_REVIEW_HOLD"
    classification = row.get("classification") if isinstance(row.get("classification"), dict) else {}
    authority = str(row.get("authority_class") or classification.get("authority_class") or "").upper()
    if authority in {"REFERENCE_ONLY", "UNKNOWN_UNVERIFIED"}:
        return "SOURCE_REVIEW_HOLD"
    return None


def query_frontier(frontier, index_rows, *, semantic_scores=None, relations=None,
                   detail_rows=None, min_results=1, top_k=5,
                   allowed_source_families=None, allowed_authority_classes=None):
    located, unresolved, verification, traces = [], [], [], []
    required_count = max(1, int(min_results))
    allowed_families={str(x).strip() for x in (allowed_source_families or []) if str(x).strip()}
    allowed_authorities={str(x).strip().upper() for x in (allowed_authority_classes or []) if str(x).strip()}
    for item in frontier or []:
        fid = str(item.get("id") or "")
        question = str(item.get("question") or fid)
        expected_name = str(item.get("expected_source_filename") or "").strip()
        pool = ([row for row in (index_rows or [])
                 if _exact_source_file(row, expected_name)]
                if expected_name else (index_rows or []))
        result = retrieve(
            pool, "" if expected_name else question,
            semantic_scores=None if expected_name else semantic_scores,
            relations=relations,
            detail_rows=detail_rows,
            top_k=top_k,
            relation_hops=1,
        )
        primary = result.get("primary", [])
        approximate = []
        if expected_name and not primary:
            near = retrieve(index_rows or [], question, top_k=top_k)
            approximate = [
                {"source_id": hit.get("source_id"), "reason": "SOURCE_IDENTITY_MISMATCH"}
                for hit in near.get("primary", []) if
                not _exact_source_file(hit.get("row") or {}, expected_name)
            ]
        def constraint_reason(hit):
            row=hit.get("row") or {}
            if not _candidate_usable(row):
                return _excluded_candidate_reason(row)
            if allowed_families and str(row.get("source_family") or "") not in allowed_families:
                return "SOURCE_FAMILY_CONSTRAINT"
            authority=str(row.get("authority_class") or (row.get("classification") or {}).get("authority_class") or "").upper()
            if allowed_authorities and authority not in allowed_authorities:
                return "AUTHORITY_CLASS_CONSTRAINT"
            return None
        qualified = [x for x in primary if constraint_reason(x) is None]
        rejected = [
            {"source_id": x.get("source_id"), "reason": constraint_reason(x)}
            for x in primary if constraint_reason(x) is not None
        ] + approximate
        enough = len(qualified) >= required_count
        traces.append({
            "frontier_id": fid,
            "query": question,
            "exact_source_filename": expected_name or None,
            "exact_identity_match_required": bool(expected_name),
            "approximate_candidate_rejected_count": len(approximate),
            "sufficient": enough,  # legacy: retrieval coverage ONLY, never evidence sufficiency
            "retrieval_sufficient": enough,
            "evidence_sufficient": False,
            "retrieval_hit_count": len(primary),
            "qualified_index_hits": len(qualified),
            "rejected_index_candidates": rejected,
            "verification_required": enough,
            "retrieval_counts": result.get("counts", {}),
            "source_ids": [x.get("source_id") for x in primary],
        })
        if enough:
            located.append({
                "frontier_id": fid,
                "question": question,
                "index_result": result,
                "evidence_sufficient": False,
            })
            verification.append({
                **item,
                "candidate_source_ids": [x.get("source_id") for x in qualified],
                "reason": "INDEX_HIT_NOT_VERIFIED_EVIDENCE",
            })
        else:
            unresolved.append(item)
    return {
        "schema": "TAKY_MINING_INDEX_FIRST_BRIDGE_V1",
        "resolved_from_index": located,  # historical name: source retrieval, NOT research completion
        "verification_frontier": verification,
        "external_mining_frontier": unresolved,
        "trace": traces,
        "counts": {
            "frontier_total": len(frontier or []),
            "resolved_from_index": len(located),
            "verification_required": len(verification),
            "external_required": len(unresolved),
        },
        "guards": {
            "index_does_not_decide_domain_use": True,
            "index_result_is_evidence_candidate": True,
            "index_hit_does_not_prove_evidence_sufficiency": True,
            "external_mining_only_for_remaining_gap": True,
            "search_projection_is_not_source_of_truth": True,
        },
    }
