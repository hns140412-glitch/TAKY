#!/usr/bin/env python3
"""Convert an unfinished Mining plan into classified, actionable follow-up.

This is a bounded planning/checkpoint helper, NOT a second engine, external
executor, persistent INDEX owner, or authority-promotion mechanism.
"""
from __future__ import annotations

from collections import Counter

DEPTH_LIMIT = {"D0": 0, "D1": 2, "D2": 4, "D3": 6, "D4": 10}
SOURCE_PREFER = ["PRIMARY", "OFFICIAL", "ACADEMIC"]
PRIORITY = {"CRITICAL": 0, "REQUIREMENT": 1, "CONFLICT": 2,
            "UNKNOWN": 3, "FOUNDATION": 4, "ADVANCED": 5, "ALTERNATIVE": 6}
ACCESS_ERRORS = {"ACCESS_DENIED", "AUTH_REQUIRED", "LOGIN_REQUIRED",
                 "PERMISSION_DENIED", "RESTRICTED", "PAYWALL", "ACCESS_HOLD"}


def _ids(item: dict) -> set[str]:
    return {str(x) for x in (item.get("id"), item.get("decomposition_id"),
                              *(item.get("aliases") or [])) if x}


def _required(item: dict, task: dict) -> bool:
    if item.get("kind") == "ALTERNATIVE" and task.get("alternatives_required"):
        return True
    return item.get("origin") != "GENERIC_SCAFFOLD"


def _provider_receipt(provider_results, ids: set[str]) -> dict | None:
    if isinstance(provider_results, dict):
        for fid in ids:
            value = provider_results.get(fid)
            if isinstance(value, dict):
                return value
        return None
    if isinstance(provider_results, list):
        for row in provider_results:
            if isinstance(row, dict) and str(row.get("frontier_id") or "") in ids:
                return row
    return None


def _verified_checkpoint_items(frontier: list[dict], checkpoint: dict | None) -> dict[str, list[str]]:
    """Re-assess Core evidence: an asserted CLOSED flag or provider success is not proof."""
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != "TAKY_MINING_CORE_CHECKPOINT_V1":
        return {}
    evidence = checkpoint.get("evidence")
    if not isinstance(evidence, list):
        return {}
    from mining_core import assess_frontier
    assessed = {str(x.get("id")): x for x in assess_frontier(frontier, evidence)}
    declared = {str(x.get("id")): x for x in checkpoint.get("frontier", [])
                if isinstance(x, dict)}
    closed = {}
    for item in frontier:
        fid = str(item.get("id") or "")
        if assessed.get(fid, {}).get("status") != "CLOSED" or declared.get(fid, {}).get("status") != "CLOSED":
            continue
        anchors = [
            e for e in evidence if isinstance(e, dict)
            and str(e.get("frontier_id")) in _ids(item)
            and (e.get("source_identity") or e.get("source_id") or e.get("source_url"))
            and e.get("excerpt_ref") and (e.get("claim") or e.get("subject"))
            and e.get("direct_support") is True and e.get("fresh_enough", True) is not False
        ]
        if anchors:
            closed[fid] = list(dict.fromkeys(
                str(e.get("source_id") or e.get("source_identity") or e.get("source_url"))
                for e in anchors
            ))
    return closed


def _action(item: dict, category: str, *, source_ids=None, next_provider=None) -> dict:
    fid = str(item.get("id") or "")
    question = str(item.get("question") or fid)
    source_ids = list(source_ids or [])
    common = {"frontier_id": fid, "question": question,
              "source_ids": source_ids, "external_execution_performed": False}
    if category == "EVIDENCE_VERIFIED":
        return {**common, "type": "NO_ACTION", "when": "ALREADY_VERIFIED"}
    if category == "DEPTH_DEFERRED":
        return {**common, "type": "QUEUE_NEXT_BOUNDED_BATCH",
                "when": "AFTER_VERIFIED_CURRENT_BATCH_CHECKPOINT"}
    if category == "OPTIONAL_SCOPE_REVIEW":
        return {**common, "type": "REVIEW_OPTIONAL_RELEVANCE",
                "when": "ONLY_IF_USER_GOAL_REQUIRES_DEEPER_RESEARCH"}
    if category == "DEPTH_CONFLICT":
        return {**common, "type": "RECONCILE_KNOWN_COMPLETE_WITH_REQUIRED_GAP",
                "when": "NEW_EXPLICIT_SCOPE_DECISION"}
    if category == "ROUTE_BLOCKED":
        return {**common, "type": "REPLAN_WITH_FAILURE_MEMORY",
                "when": "NEW_EVIDENCE_OR_MATERIALLY_DIFFERENT_ROUTE"}
    if category == "ACCESS_HOLD":
        return {**common, "type": "FIND_PERMITTED_ALTERNATIVE_OR_HOLD",
                "when": "AUTHORIZED_ROUTE_OR_ACCESS_STATUS_CHANGE"}
    if category == "PROVIDER_FAILURE":
        return {**common, "type": "TRY_NEXT_PROVIDER" if next_provider else "HOLD_FAILED_ROUTE",
                "next_provider": next_provider,
                "when": "DIFFERENT_PROVIDER_AVAILABLE" if next_provider else "NEW_EVIDENCE_OR_CHANGED_METHOD"}
    if category == "EMPTY_PROVIDER_RESULT":
        return {**common, "type": "TRY_NEXT_PROVIDER" if next_provider else "REVISE_QUERY_OR_HOLD",
                "next_provider": next_provider,
                "when": "DIFFERENT_PROVIDER_AVAILABLE" if next_provider else "NEW_QUERY_OR_CHANGED_METHOD"}
    if category == "INDEX_EVIDENCE_UNVERIFIED":
        return {**common, "type": "VERIFY_INDEX_SOURCE_AND_EXACT_ANCHOR",
                "when": "SOURCE_ANCHOR_AND_CLAIM_CHECK"}
    if category == "PROVIDER_RESULT_UNVERIFIED":
        return {**common, "type": "VALIDATE_PROVIDER_RECEIPT_AND_EXACT_EVIDENCE",
                "when": "SOURCE_ANCHOR_AND_CLAIM_CHECK"}
    if category == "SOURCE_REFRESH_REQUIRED":
        return {**common, "type": "REACQUIRE_CURRENT_SOURCE_THEN_INDEX_VERSION_REVIEW",
                "when": "NEW_PRIMARY_OR_CURRENT_SOURCE_FOUND"}
    if category == "SOURCE_REVIEW_HOLD":
        return {**common, "type": "REQUEST_INDEX_REVIEW_OR_FIND_PERMITTED_PRIMARY",
                "when": "REVIEW_RECEIPT_OR_ALTERNATIVE_SOURCE"}
    if category == "CONFLICT_UNRESOLVED":
        return {**common, "type": "CROSS_VALIDATE_INDEPENDENT_COUNTEREVIDENCE",
                "when": "INDEPENDENT_PRIMARY_OR_OFFICIAL_SOURCE"}
    return {**common, "type": "EXPAND_SOURCE_DISCOVERY",
            "when": "NEW_ROUTE_OR_SOURCE_FAMILY"}


def _query_plan(item: dict, category: str, *, next_provider=None) -> dict | None:
    if category not in {"SOURCE_GAP", "SOURCE_REFRESH_REQUIRED",
                        "CONFLICT_UNRESOLVED", "EMPTY_PROVIDER_RESULT",
                        "PROVIDER_FAILURE"}:
        return None
    if category in {"PROVIDER_FAILURE", "EMPTY_PROVIDER_RESULT"} and not next_provider:
        return None
    fid = str(item.get("id") or "")
    return {
        "frontier_id": fid,
        "query": str(item.get("question") or fid),
        "purpose": "RESOLVE_CONFLICT" if category == "CONFLICT_UNRESOLVED" else "FILL_EVIDENCE_GAP",
        "prefer": SOURCE_PREFER,
        **({"next_provider": next_provider}
           if category in {"PROVIDER_FAILURE", "EMPTY_PROVIDER_RESULT"} else {}),
    }


def classify_pending(task: dict, full_frontier: list[dict], selected: list[dict],
                     index_result: dict, *, route_blocked=False,
                     provider_results=None, depth="D1",
                     verified_checkpoint=None) -> dict:
    """Preserve *all* questions, classify why each is pending and provide action instructions.

    A source hit or a provider SUCCESS is only a candidate; actual closure is
    established by Mining Core's evidence-assessed checkpoint.
    """
    selected_ids = set().union(*(_ids(x) for x in selected)) if selected else set()
    verified = _verified_checkpoint_items(full_frontier, verified_checkpoint)
    verifying = {str(x.get("id")): x for x in index_result.get("verification_frontier", [])}
    trace_by_id = {str(x.get("frontier_id")): x for x in index_result.get("trace", [])}
    entries = []
    for position, item in enumerate(full_frontier):
        fid = str(item.get("id") or "")
        ids = _ids(item)
        required = _required(item, task)
        is_selected = bool(ids & selected_ids)
        trace = trace_by_id.get(fid, {})
        candidate_ids = list(dict.fromkeys(
            list(trace.get("source_ids") or []) + verified.get(fid, [])
        ))
        rejected = list(trace.get("rejected_index_candidates") or [])
        receipt = _provider_receipt(provider_results, ids) if is_selected else None
        provider_state = str((receipt or {}).get("state") or "").upper()
        provider_error = str((receipt or {}).get("error_code") or (receipt or {}).get("error") or "").upper()
        next_provider = (receipt or {}).get("next_provider")
        next_provider = str(next_provider).strip() if next_provider else None
        attempted_provider = str((receipt or {}).get("provider") or "")
        if next_provider:
            from mining_provider_executor import SUPPORTED_PROVIDERS
            if (next_provider.upper() == attempted_provider.upper()
                    or next_provider.upper() not in SUPPORTED_PROVIDERS):
                next_provider = None  # never retry the same or an unsupported route
        provider_evidence = ((receipt or {}).get("receipt") or {}).get("results") or (receipt or {}).get("results") or []
        if not isinstance(provider_evidence, list):
            provider_evidence = []
        if provider_evidence:
            candidate_ids = list(dict.fromkeys(candidate_ids + [
                str(x.get("source_id")) for x in provider_evidence
                if isinstance(x, dict) and x.get("source_id")
            ]))

        if fid in verified:
            category = "EVIDENCE_VERIFIED"
        elif not is_selected:
            category = ("DEPTH_CONFLICT" if depth == "D0" and required else
                        "DEPTH_DEFERRED" if required else "OPTIONAL_SCOPE_REVIEW")
        elif route_blocked:
            category = "ROUTE_BLOCKED"
        elif provider_error in ACCESS_ERRORS or provider_state in ACCESS_ERRORS:
            category = "ACCESS_HOLD"
        elif provider_state == "FAILED":
            category = "PROVIDER_FAILURE"
        elif provider_state == "EMPTY" or (provider_state == "SUCCESS" and not provider_evidence):
            category = "EMPTY_PROVIDER_RESULT"
        elif provider_state == "SUCCESS":
            category = "PROVIDER_RESULT_UNVERIFIED"
        elif fid in verifying:
            category = "INDEX_EVIDENCE_UNVERIFIED"
        elif item.get("kind") == "CONFLICT":
            category = "CONFLICT_UNRESOLVED"
        elif rejected:
            causes = {str(x.get("reason") or "").upper() for x in rejected}
            category = ("SOURCE_REFRESH_REQUIRED" if causes & {"STALE", "SUPERSEDED"}
                        else "SOURCE_REVIEW_HOLD")
        else:
            category = "SOURCE_GAP"
        state = ("CLOSED" if category == "EVIDENCE_VERIFIED" else
                 "HOLD" if category in {"ROUTE_BLOCKED", "ACCESS_HOLD", "DEPTH_CONFLICT",
                                       "SOURCE_REVIEW_HOLD"} or
                 (category in {"PROVIDER_FAILURE", "EMPTY_PROVIDER_RESULT"}
                  and not next_provider)
                 else "CANDIDATE" if category == "OPTIONAL_SCOPE_REVIEW"
                 else "DEFERRED" if category == "DEPTH_DEFERRED" else "READY")
        action = _action(item, category, source_ids=candidate_ids, next_provider=next_provider)
        entry = {
            "frontier_id": fid,
            "decomposition_id": item.get("decomposition_id"),
            "question": item.get("question") or fid,
            "kind": item.get("kind"),
            "origin": item.get("origin"),
            "priority": PRIORITY.get(str(item.get("kind") or ""), 7),
            "order": position,
            "required_for_goal": required,
            "selected_this_batch": is_selected,
            "classification": category,
            "state": state,
            "owner": "MINING",  # INDEX handles persistent source/version metadata after a handoff.
            "handoff_to": "INDEXING" if category in {"SOURCE_REFRESH_REQUIRED", "SOURCE_REVIEW_HOLD"} else None,
            "source_ids": candidate_ids,
            "excluded_source_candidates": rejected,
            "next_action": action,
            "query_plan": (_query_plan(item, category, next_provider=next_provider)
                           if state == "READY" else None),
            "completion_evidence": ("A source-anchored, conflict-checked Mining Core frontier CLOSED checkpoint"
                                    if required else "An explicit relevance decision; optional scope is not silently mandatory"),
            "retry_condition": action["when"],
            "automatic_promotion_allowed": False,
        }
        entries.append(entry)

    required_open = [x for x in entries if x["required_for_goal"] and x["state"] != "CLOSED"]
    deferred = [x for x in entries if x["classification"] == "DEPTH_DEFERRED"]
    deferred.sort(key=lambda x: (x["priority"], x["order"]))
    limit = DEPTH_LIMIT.get(depth, 0)
    return {
        "schema": "TAKY_MINING_PENDING_ACTIONS_V1",
        "items": entries,
        "counts": {
            "total": len(entries),
            "required_open": len(required_open),
            "deferred_required": len(deferred),
            "held": sum(x["state"] == "HOLD" for x in entries),
            "by_classification": dict(sorted(Counter(x["classification"] for x in entries).items())),
        },
        "ready_query_plans": [x["query_plan"] for x in entries if x["query_plan"]],
        "next_batch_preview": [x["frontier_id"] for x in deferred[:limit]],
        "next_batch_activation": "AFTER_VERIFIED_CURRENT_BATCH_CHECKPOINT",
        "research_complete_eligible": (not route_blocked and not required_open
                                        and (bool(full_frontier) or bool(task.get("known_complete")))
                                        and (bool(task.get("known_complete")) or not any(
                                            x["classification"] == "OPTIONAL_SCOPE_REVIEW" for x in entries))),
        "guards": {
            "no_unprocessed_required_item_is_silently_dropped": True,
            "search_hit_is_not_evidence_closure": True,
            "no_repeat_same_blocked_route": True,
            "no_auto_external_action_or_current_promotion": True,
        },
    }


def activate_next_batch(pending: dict, selected: list[dict], checkpoint: dict,
                        *, depth="D1", route_blocked=False) -> dict:
    """Prepare the deferred batch only after current required items are evidence-CLOSED.

    This produces actionable query plans, not an external execution, schedule,
    authoritative ledger mutation, or source promotion.
    """
    if route_blocked:
        return {"state": "HOLD_ROUTE", "frontier": [], "query_plans": []}
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != "TAKY_MINING_CORE_CHECKPOINT_V1":
        return {"state": "WAIT_VERIFIED_CHECKPOINT", "frontier": [], "query_plans": []}
    # A caller-provided CLOSED label is not proof. Reassess the evidence with
    # the existing Mining Core and demand source identity + an exact anchor.
    from mining_core import assess_frontier

    evidence = checkpoint.get("evidence")
    if not isinstance(evidence, list):
        return {"state": "WAIT_VERIFIED_CHECKPOINT", "reason": "MISSING_EVIDENCE_LEDGER",
                "frontier": [], "query_plans": []}
    assessed = {str(x.get("id")): x for x in assess_frontier(selected, evidence)}
    declared = {str(x.get("id")): x for x in checkpoint.get("frontier", [])
                if isinstance(x, dict)}
    required_selected = {
        str(item.get("frontier_id")) for item in pending.get("items", [])
        if item.get("selected_this_batch") and item.get("required_for_goal")
    }
    remaining = []
    missing_anchors = []
    for item in selected:
        fid = str(item.get("id"))
        if fid not in required_selected:
            continue
        actual = assessed.get(fid, {})
        reported = declared.get(fid, {})
        closed = actual.get("status") == "CLOSED" and reported.get("status") == "CLOSED"
        if not closed:
            remaining.append(fid)
            continue
        anchored = any(
            isinstance(e, dict) and str(e.get("frontier_id")) in _ids(item)
            and (e.get("source_identity") or e.get("source_id") or e.get("source_url"))
            and e.get("excerpt_ref") and (e.get("claim") or e.get("subject"))
            and e.get("direct_support") is True
            for e in evidence
        )
        if not anchored:
            missing_anchors.append(fid)
    if missing_anchors:
        return {"state": "WAIT_SOURCE_ANCHOR", "missing_anchor_ids": missing_anchors,
                "unresolved_current": remaining, "frontier": [], "query_plans": []}
    if remaining:
        return {"state": "WAIT_CURRENT_BATCH_EVIDENCE", "unresolved_current": remaining,
                "frontier": [], "query_plans": []}
    deferred = [
        x for x in pending.get("items", [])
        if x.get("classification") == "DEPTH_DEFERRED" and x.get("required_for_goal")
    ]
    deferred.sort(key=lambda x: (x.get("priority", 9), x.get("order", 0)))
    limit = DEPTH_LIMIT.get(depth, 0)
    batch = deferred[:limit]
    if not batch:
        return {"state": "NO_DEFERRED_REQUIRED", "frontier": [], "query_plans": []}
    next_frontier = [{
        "id": x["frontier_id"], "decomposition_id": x.get("decomposition_id"),
        "question": x["question"], "kind": x["kind"], "origin": x.get("origin"),
    } for x in batch]
    return {
        "state": "READY_NEXT_BATCH",
        "frontier": next_frontier,
        "query_plans": [{
            "frontier_id": x["frontier_id"], "query": x["question"],
            "purpose": "RESOLVE_CONFLICT" if x["kind"] == "CONFLICT" else "FILL_EVIDENCE_GAP",
            "prefer": SOURCE_PREFER,
        } for x in batch],
        "remaining_deferred_ids": [x["frontier_id"] for x in deferred[limit:]],
        "checkpoint_resume_key": checkpoint.get("resume_key"),
        "external_execution_performed": False,
        "automatic_promotion_allowed": False,
    }
