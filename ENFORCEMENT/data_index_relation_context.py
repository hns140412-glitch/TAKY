#!/usr/bin/env python3
"""Read-only, evidence-labelled relationship context for already authorized INDEX rows.

This is a derived INDEX retrieval view, not CURRENT, a domain use decision,
an independent Indexing-owner receipt, or a replacement for existing ranking.
The caller must restrict records to its authorized Source Universe beforehand.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "TAKY_INDEX_RELATION_CONTEXT_V1"
SOURCE_RELATIONS = frozenset({
    "PART_OF", "CONTAINS", "FRAGMENT_OF", "EXTRACTED_FROM", "DERIVED_FROM",
    "VERSION_OF", "SUPERSEDES", "EXACT_DUPLICATE_OF", "NEAR_DUPLICATE_OF",
    "SAME_FAMILY_AS", "REFERENCES", "RELATED_TO",
})
UNVERIFIED_QUALIFIERS = frozenset({
    "LEGACY_DUPLICATE_GROUP_UNVERIFIED", "LEGACY_FRAGMENT_GROUP_COMPAT",
})


def assemble_relation_context(
    records: list[dict[str, Any]],
    root_source_id: str,
    *,
    eligible_ids: set[str] | None = None,
    required_types: set[str] | None = None,
    max_edges: int = 24,
) -> dict[str, Any]:
    """Explain direct edges without merging identities or bypassing query filters.

    A referenced source outside eligible_ids is intentionally not disclosed.
    STAGED_MANIFEST_VALIDATED means a reciprocal metadata contract was checked,
    not that original content or an independent production receipt was checked.
    """
    if not isinstance(max_edges, int) or isinstance(max_edges, bool) or not 1 <= max_edges <= 100:
        raise ValueError("MAX_EDGES_INVALID")
    by_id: dict[str, dict[str, Any]] = {}
    for row in records:
        sid = row.get("source_id")
        if not isinstance(sid, str) or not sid or sid in by_id:
            raise ValueError("SOURCE_ID_MISSING_OR_DUPLICATED")
        by_id[sid] = row
    if root_source_id not in by_id:
        raise ValueError("ROOT_NOT_IN_AUTHORIZED_UNIVERSE")
    if eligible_ids is not None and root_source_id not in eligible_ids:
        raise ValueError("ROOT_OUTSIDE_QUERY_FILTER")
    required_types = set(required_types or ())
    if not required_types.issubset(SOURCE_RELATIONS):
        raise ValueError("REQUIRED_RELATION_TYPE_INVALID")

    root = by_id[root_source_id]
    edges: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    seen_types: set[str] = set()
    raw_edges = root.get("relations") or []
    if not isinstance(raw_edges, list):
        raise ValueError("RELATIONS_NOT_LIST")
    for relation in raw_edges[:max_edges]:
        if not isinstance(relation, dict):
            gaps.append({"reason": "INVALID_RELATION_RECORD"})
            continue
        typ, target_id = relation.get("type"), relation.get("target")
        edge: dict[str, Any] = {"type": typ, "status": None}
        if typ not in SOURCE_RELATIONS or not isinstance(target_id, str) or not target_id:
            edge["status"] = "INVALID_RELATION_TYPE_OR_TARGET"
        elif target_id == root_source_id:
            edge["status"] = "SELF_RELATION_REQUIRES_REVIEW"
        elif target_id not in by_id:
            # The schema permits family/package logical nodes; do not invent a physical source.
            if (relation.get("target_node_type") in {"FAMILY", "PACKAGE"} or
                    (typ == "PART_OF" and target_id == root.get("source_family"))):
                edge["status"] = "LOGICAL_NODE_NOT_MATERIALIZED"
            else:
                edge["status"] = "SOURCE_ENDPOINT_NOT_IN_UNIVERSE"
        elif eligible_ids is not None and target_id not in eligible_ids:
            # Avoid exposing a target excluded by a query or caller's access filter.
            edge["status"] = "TARGET_OUTSIDE_QUERY_FILTER"
        elif relation.get("qualifier") in UNVERIFIED_QUALIFIERS:
            edge["status"] = "LEGACY_RELATION_CANDIDATE_ONLY"
        else:
            target = by_id[target_id]
            proof = relation.get("evidence_ref")
            state = relation.get("verification_state")
            if typ == "EXACT_DUPLICATE_OF" and not (
                root.get("content_hash") and root.get("content_hash") == target.get("content_hash")
                and root.get("content_hash_verification") == "INDEPENDENT_BINARY_VERIFIED"
                and target.get("content_hash_verification") == "INDEPENDENT_BINARY_VERIFIED"
                and state == "VERIFIED" and isinstance(proof, str) and proof.strip()
            ):
                edge["status"] = "EXACT_DUPLICATE_PROOF_REQUIRED"
            elif state == "STAGED_MANIFEST_VALIDATED" and isinstance(proof, str) and proof.strip():
                edge["status"] = "STAGED_METADATA_LINK_NOT_CANONICAL"
            elif state == "VERIFIED" and isinstance(proof, str) and proof.strip():
                edge["status"] = "EVIDENCE_RECORDED_NOT_OWNER_ATTESTED"
            else:
                edge["status"] = "RELATION_EVIDENCE_MISSING"
            if edge["status"] in {"STAGED_METADATA_LINK_NOT_CANONICAL",
                                   "EVIDENCE_RECORDED_NOT_OWNER_ATTESTED"}:
                edge["target_source_ref"] = {
                    "source_id": target_id, "locator": target.get("locator"),
                    "title": target.get("canonical_title"),
                    "source_family": target.get("source_family"),
                    "review_state": target.get("review_state"),
                    "current_relation": target.get("current_relation"),
                }
                edge["evidence_ref"] = proof
                edge["verification_scope"] = relation.get("verification_scope")
        if edge["status"] in {"STAGED_METADATA_LINK_NOT_CANONICAL",
                              "EVIDENCE_RECORDED_NOT_OWNER_ATTESTED"}:
            seen_types.add(typ)
        else:
            gaps.append({"type": typ, "reason": edge["status"]})
        edges.append(edge)
    if len(raw_edges) > max_edges:
        gaps.append({"reason": "EDGE_BUDGET_EXCEEDED", "omitted": len(raw_edges) - max_edges})
    for typ in sorted(required_types - seen_types):
        gaps.append({"type": typ, "reason": "REQUIRED_RELATION_WITH_EVIDENCE_MISSING"})

    return {
        "schema": SCHEMA,
        "projection_authoritative": False,
        "current_promoted": False,
        "domain_use_approved": False,
        "index_owner_receipt_verified": False,
        "root_source_ref": {
            "source_id": root_source_id, "locator": root.get("locator"),
            "review_state": root.get("review_state"),
            "current_relation": root.get("current_relation"),
        },
        "edge_count": len(edges), "edges": edges, "evidence_gaps": gaps,
        "relation_context_complete_for_request": not gaps,
    }
