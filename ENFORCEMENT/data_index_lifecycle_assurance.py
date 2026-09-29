#!/usr/bin/env python3
"""Read-only Source Universe conservation, graph integrity and delta-impact audit.

No new authority, graph database, original bytes, CURRENT promotion or producer
approval. Use the already scope-filtered, normalized INDEX projection as input.
Summary output contains counts, never private source IDs, URLs or source text.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any

from data_index_relation_context import SOURCE_RELATIONS, relation_has_recorded_evidence

SCHEMA = "TAKY_INDEX_LIFECYCLE_ASSURANCE_V1"
DEPENDENCY_EDGES = frozenset({
    "DERIVED_FROM", "EXTRACTED_FROM", "FRAGMENT_OF", "PART_OF",
    "VERSION_OF", "SUPERSEDES", "REFERENCES",
})
CHANGE_TYPES = frozenset({
    "NEW", "MODIFIED", "REMOVED", "ACCESS_REVOKED", "RESTORED",
    "METADATA_CHANGED", "ASSET_REVISION",
})


def _source_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("ROWS_NOT_LIST")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ROW_NOT_OBJECT")
        sid = row.get("source_id")
        if not isinstance(sid, str) or not sid.strip() or sid != sid.strip():
            raise ValueError("SOURCE_ID_INVALID")
        if sid in by_id:
            raise ValueError("DUPLICATE_SOURCE_ID_NO_SILENT_MERGE")
        by_id[sid] = row
    return by_id


def _logical_node(row: dict[str, Any], edge: dict[str, Any]) -> bool:
    return bool(
        edge.get("target_node_type") in {"FAMILY", "PACKAGE"}
        or (edge.get("type") == "PART_OF" and edge.get("target") == row.get("source_family")
            and row.get("source_family"))
    )


def _cycle_count(graph: dict[str, set[str]]) -> int:
    # Count nontrivial strongly connected components, not paths or duplicate cycles.
    order: list[str] = []
    seen: set[str] = set()
    def visit(root: str) -> None:
        stack = [(root, False)]
        while stack:
            node, finished = stack.pop()
            if finished:
                order.append(node)
            elif node not in seen:
                seen.add(node)
                stack.append((node, True))
                stack.extend((target, False) for target in graph.get(node, ()) if target not in seen)
    for root in graph:
        if root not in seen:
            visit(root)
    reverse: dict[str, set[str]] = defaultdict(set)
    for origin, targets in graph.items():
        for target in targets:
            reverse[target].add(origin)
    assigned: set[str] = set()
    count = 0
    for root in reversed(order):
        if root in assigned:
            continue
        group = set()
        stack = [root]
        while stack:
            node = stack.pop()
            if node in assigned:
                continue
            assigned.add(node)
            group.add(node)
            stack.extend(reverse.get(node, ()) - assigned)
        if len(group) > 1 or any(n in graph.get(n, ()) for n in group):
            count += 1
    return count


def audit_projected_universe(
    rows: list[dict[str, Any]], *, expected_source_ids: set[str] | None = None
) -> dict[str, Any]:
    by_id = _source_map(rows)
    if expected_source_ids is not None:
        if not isinstance(expected_source_ids, set) or any(
            not isinstance(sid, str) or not sid for sid in expected_source_ids
        ):
            raise ValueError("EXPECTED_SOURCE_IDS_INVALID")
    issues: Counter[str] = Counter()
    evidence: Counter[str] = Counter()
    graph: dict[str, set[str]] = defaultdict(set)
    titles: dict[str, set[str]] = defaultdict(set)
    relations = 0
    for sid, row in by_id.items():
        title = row.get("canonical_title")
        if isinstance(title, str) and title:
            titles[title.casefold().strip()].add(sid)
        if not isinstance(row.get("locator"), str) or not row["locator"].strip():
            issues["SOURCE_LOCATOR_ABSENT"] += 1
        lineage = row.get("field_lineage") or {}
        if not isinstance(lineage, dict):
            issues["FIELD_LINEAGE_INVALID"] += 1
            lineage = {}
        family_lineage = lineage.get("source_family")
        if family_lineage == "SOURCE_V6_RECORDED":
            evidence["family_source_recorded"] += 1
        elif family_lineage == "UTILIZATION_V26_DERIVED_CANDIDATE":
            evidence["family_derived_candidate"] += 1
        elif family_lineage == "STAGED_MANIFEST_METADATA_NOT_CURRENT":
            evidence["family_staged_metadata"] += 1
        else:
            evidence["family_unattested_or_unknown"] += 1
        if row.get("short_summary"):
            if lineage.get("short_summary") == "SOURCE_V6_CONTENT_REVIEWED":
                evidence["summary_source_reviewed"] += 1
            else:
                evidence["summary_not_source_content_attested"] += 1
        if not row.get("content_hash"):
            evidence["content_hash_unknown"] += 1
        elif row.get("content_hash_verification") != "INDEPENDENT_BINARY_VERIFIED":
            evidence["content_hash_not_independently_verified"] += 1
        if (row.get("detail_available") or row.get("detail_l2")) and not row.get(
            "detail_location_independent_receipt"
        ):
            evidence["detail_location_independent_receipt_absent"] += 1
        envelope = row.get("intake_envelope") or {}
        privacy = envelope.get("privacy_class") if isinstance(envelope, dict) else None
        if privacy not in {"PUBLIC", "AUTHORIZED_PRIVATE", "RESTRICTED"}:
            evidence["privacy_scope_not_attested_in_projection"] += 1
        edges = row.get("relations") or []
        if not isinstance(edges, list):
            issues["RELATIONS_NOT_LIST"] += 1
            continue
        for edge in edges:
            relations += 1
            if not isinstance(edge, dict):
                issues["EDGE_NOT_OBJECT"] += 1
                continue
            kind, target = edge.get("type"), edge.get("target")
            if kind not in SOURCE_RELATIONS or not isinstance(target, str) or not target:
                issues["EDGE_KIND_OR_TARGET_INVALID"] += 1
            elif target == sid:
                issues["SELF_RELATION"] += 1
            elif target not in by_id:
                if _logical_node(row, edge):
                    evidence["logical_family_or_package_unmaterialized"] += 1
                else:
                    issues["DANGLING_PHYSICAL_EDGE"] += 1
            else:
                evidence["resolved_physical_edge"] += 1
                if kind == "EXACT_DUPLICATE_OF" and not relation_has_recorded_evidence(row, edge, by_id[target]):
                    issues["EXACT_DUPLICATE_PROOF_MISSING"] += 1
                if kind == "SUPERSEDES" and relation_has_recorded_evidence(row, edge, by_id[target]):
                    graph[sid].add(target)
                    graph.setdefault(target, set())
    title_collision_groups = sum(len(ids) > 1 for ids in titles.values())
    cycles = _cycle_count(graph)
    if cycles:
        issues["RECORDED_SUPERSESSION_CYCLE"] = cycles
    expected_missing = unexpected = None
    if expected_source_ids is not None:
        expected_missing = len(expected_source_ids - by_id.keys())
        unexpected = len(by_id.keys() - expected_source_ids)
        if expected_missing:
            issues["EXPECTED_SOURCE_IDS_MISSING"] = expected_missing
        if unexpected:
            issues["UNEXPECTED_SOURCE_IDS"] = unexpected
    return {
        "schema": SCHEMA,
        "state": "STRUCTURAL_GAPS" if issues else "METADATA_OBSERVATION_ONLY",
        "projection_authoritative": False,
        "index_owner_receipt_verified": False,
        "current_promoted": False,
        "domain_use_approved": False,
        "source_count": len(by_id),
        "expected_source_count": len(expected_source_ids) if expected_source_ids is not None else None,
        "source_identity_conserved": (not expected_missing and not unexpected)
            if expected_source_ids is not None else None,
        "missing_expected_count": expected_missing, "unexpected_count": unexpected,
        "relation_record_count": relations,
        "casefold_title_collision_groups_not_merged": title_collision_groups,
        "issue_counts": dict(sorted(issues.items())),
        "evidence_state_counts": dict(sorted(evidence.items())),
        "claim_ceiling": "SOURCE_ID_AND_METADATA_CONSERVATION_AUDIT_ONLY",
    }


def plan_incremental_impact(
    rows: list[dict[str, Any]], events: list[dict[str, Any]], *,
    start_cursor: str, end_cursor: str | None,
    change_feed_exhausted: bool, max_affected: int = 10000,
) -> dict[str, Any]:
    """Calculate reverse dependency impact without deleting, fetching or committing."""
    by_id = _source_map(rows)
    if not isinstance(start_cursor, str) or not start_cursor:
        raise ValueError("START_CURSOR_REQUIRED")
    if not isinstance(events, list) or not isinstance(change_feed_exhausted, bool):
        raise ValueError("DELTA_ENVELOPE_INVALID")
    if not isinstance(max_affected, int) or isinstance(max_affected, bool) or max_affected < 1:
        raise ValueError("MAX_AFFECTED_INVALID")
    seen: dict[str, tuple[str, str]] = {}
    changed: set[str] = set()
    kind_counts: Counter[str] = Counter()
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("CHANGE_EVENT_INVALID")
        event_id, sid, kind = event.get("event_id"), event.get("source_id"), event.get("change_type")
        if not isinstance(event_id, str) or not event_id or not isinstance(sid, str) or not sid or kind not in CHANGE_TYPES:
            raise ValueError("CHANGE_EVENT_IDENTITY_INVALID")
        prior = seen.get(event_id)
        if prior is not None:
            if prior != (sid, kind):
                raise ValueError("CONFLICTING_REPLAY_EVENT_ID")
            continue  # exact idempotent replay
        seen[event_id] = (sid, kind)
        if kind != "NEW" and sid not in by_id:
            raise ValueError("CHANGE_SOURCE_NOT_IN_PRIOR_SNAPSHOT")
        changed.add(sid)
        kind_counts[kind] += 1
    reverse: dict[str, set[str]] = defaultdict(set)
    review_only: dict[str, set[str]] = defaultdict(set)
    for sid, row in by_id.items():
        for edge in row.get("relations") or []:
            if not isinstance(edge, dict):
                continue
            target = edge.get("target")
            if target in by_id and target != sid and isinstance(target, str):
                if edge.get("type") in DEPENDENCY_EDGES:
                    reverse[target].add(sid)
                elif edge.get("type") == "RELATED_TO":
                    review_only[target].add(sid)
    affected = set(changed)
    queue = deque(changed)
    while queue:
        node = queue.popleft()
        for dependent in reverse.get(node, ()):
            if dependent not in affected:
                affected.add(dependent)
                if len(affected) > max_affected:
                    raise ValueError("IMPACT_SCOPE_LIMIT_EXCEEDED")
                queue.append(dependent)
    review_neighbors = set().union(*(review_only.get(sid, set()) for sid in affected)) - affected
    return {
        "schema": "TAKY_INDEX_INCREMENTAL_IMPACT_PLAN_V1",
        "state": "READ_ONLY_DELTA_REVALIDATION_REQUIRED",
        "unique_event_count": len(seen),
        "changed_source_count": len(changed),
        "dependency_impacted_count": len(affected),
        "related_review_only_count": len(review_neighbors),
        "change_type_counts": dict(sorted(kind_counts.items())),
        "change_feed_end_seen": change_feed_exhausted,
        "end_cursor_present": bool(end_cursor),
        "cursor_committed": False,
        "current_promoted": False,
        "raw_deleted": False,
        "source_index_rebuild_required_for_affected": bool(affected),
        "detail_anchor_recheck_required": bool(affected),
        "search_projection_invalidation_required": bool(affected),
        "consumer_artifact_recheck_required": bool(affected),
        "authority_and_access_recheck_required": any(
            kind_counts[k] for k in ("REMOVED", "ACCESS_REVOKED", "RESTORED", "ASSET_REVISION")
        ),
        "cursor_commit_gate": "INDEPENDENT_PAGE_COMPLETENESS_AND_INDEX_OWNER_RECEIPT_REQUIRED",
        "source_identifiers_returned": False,
    }
