#!/usr/bin/env python3
"""STEP 11: executable Mining Engine V2 run orchestrator.

Connects goal intake -> memory prior -> depth routing -> frontier planning ->
execution receipt -> memory-learning proposal. It never promotes memory itself.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from strategy_failure_memory import prepare_next_run
from mining_goal_decomposition import apply_to_task
from mining_depth_router import route_depth
from mining_growth_loop import propose_growth
from mining_index_bridge import query_frontier
from mining_pending_actions import classify_pending, activate_next_batch
from mining_provider_execution_loop import build_requests
from mining_research_assurance import audit_research
from mining_live_execution import execute_batch
from mining_core import checkpoint as core_checkpoint, apply_external_receipts, normalize_goal

DEPTH_ORDER = {"D0":0,"D1":1,"D2":2,"D3":3,"D4":4}

def build_frontier(task: dict, depth: str, *, unbounded=False) -> list[dict]:
    """Prioritize explicit intent and critical evidence within the depth budget.

    Generic dimensions are research scaffolding, never allowed to displace an
    explicit critical requirement without exposing it as unplanned.
    """
    if depth == "D0" and not unbounded:
        return []
    items, seen = [], {}
    exact_targets={str(x).strip() for x in (task.get("exact_source_targets") or [])
                   if str(x).strip()}

    def add(item: dict) -> None:
        question = str(item.get("question") or item.get("id") or "").strip()
        if not question:
            return
        if question in exact_targets:
            item={**item,"expected_source_filename":question}
        if question in seen:
            previous = items[seen[question]]
            refs = [item.get("id"), item.get("decomposition_id"), *(item.get("aliases") or [])]
            existing = {previous.get("id"), previous.get("decomposition_id"),
                        *(previous.get("aliases") or [])}
            previous.setdefault("aliases", [])
            previous["aliases"].extend(str(x) for x in refs if x and x not in existing)
            return
        seen[question] = len(items)
        items.append(dict(item))

    decomposed = task.get("decomposed_frontier") or []
    # Preserve exact IDs from goal decomposition for downstream sufficiency checks.
    for kind in ("CRITICAL", "REQUIREMENT"):
        for item in decomposed:
            if item.get("kind") == kind:
                add(item)
    # Keep the established source-order and frontier IDs for normal questions;
    # only explicit critical/requirements receive new priority.
    for kind, field in (("UNKNOWN", "unknown"), ("CONFLICT", "conflict")):
        for value in task.get(field, []) or []:
            question = str(value).strip()
            if question:
                add({"id": question, "kind": kind, "question": question,
                     "origin": "TASK_SIGNAL"})
    has_explicit_scope = any(task.get(key) for key in (
        "critical_requirements", "requirements", "unknown", "conflict",
        "foundation_requirements", "advanced_requirements", "alternative_requirements"
    ))
    for kind in ("FOUNDATION", "ADVANCED", "ALTERNATIVE"):
        for item in decomposed:
            if item.get("kind") != kind:
                continue
            # Generic scaffolding is only a fallback for an otherwise vague goal;
            # do not inflate a concrete user's bounded research frontier.
            if (has_explicit_scope and item.get("origin") == "GENERIC_SCAFFOLD"
                    and not (kind == "ALTERNATIVE" and task.get("alternatives_required"))):
                continue
            # Legacy frontier consumers use the actual question as the ID.
            # Retain the decomposition ID separately for goal-sufficiency mapping.
            add({**item, "decomposition_id": item.get("id"), "id": item.get("question")})

    limit = {"D1": 2, "D2": 4, "D3": 6, "D4": 10}.get(depth, 0)
    return items if unbounded else items[:limit]

def _learning_proposal(task: dict, memory_prior: dict, receipt: dict) -> dict:
    success = bool(receipt.get("success"))
    strategy = memory_prior.get("strategy_memory", {}).get("selected")
    if success:
        return {
            "action": "PROPOSE_STRATEGY_OBSERVATION",
            "status": "CANDIDATE",
            "task_family": task.get("task_family"),
            "goal_pattern": task.get("goal"),
            "strategy_id": strategy.get("strategy_id") if strategy else None,
            "promotion_allowed": False,
            "reason": "SUCCESS_REQUIRES_REPEATED_VALIDATION_BEFORE_PROMOTION",
        }
    return {
        "action": "PROPOSE_FAILURE_OBSERVATION",
        "status": "OPEN",
        "task_family": task.get("task_family"),
        "route_signature": receipt.get("route_signature") or task.get("route_signature"),
        "failure_reason": receipt.get("failure_reason", "UNSPECIFIED"),
        "new_evidence_required": True,
        "promotion_allowed": False,
    }

def orchestrate(payload: dict) -> dict:
    task = apply_to_task(payload.get("task", {}))
    memory = payload.get("memory", {})
    receipt = payload.get("execution_receipt")
    prior = prepare_next_run(task, memory)
    depth = route_depth(task)
    full_frontier = build_frontier(task, depth["research_depth_decision"], unbounded=True)
    frontier = build_frontier(task, depth["research_depth_decision"])
    index_rows = payload.get("index_rows") or []
    index_result = query_frontier(
        frontier,
        index_rows,
        semantic_scores=payload.get("semantic_scores"),
        relations=payload.get("index_relations"),
        detail_rows=payload.get("detail_rows"),
        min_results=int(payload.get("index_min_results",1) or 1),
        top_k=int(payload.get("index_top_k",5) or 5),
    ) if frontier else {
        "schema":"TAKY_MINING_INDEX_FIRST_BRIDGE_V1",
        "resolved_from_index":[],
        "external_mining_frontier":[],
        "trace":[],
        "counts":{"frontier_total":0,"resolved_from_index":0,"external_required":0},
        "guards":{"index_does_not_decide_domain_use":True,"search_projection_is_not_source_of_truth":True},
    }
    external_frontier = index_result["external_mining_frontier"]
    verification_frontier = index_result.get("verification_frontier", [])
    blocked = prior["next_action"] == "HOLD_FAILED_ROUTE"
    verified_checkpoint = payload.get("verified_checkpoint")
    provider_results = payload.get("provider_results")
    if provider_results is None and isinstance(payload.get("execution_batch"), dict):
        provider_results = payload["execution_batch"].get("results")
    pending = classify_pending(
        task, full_frontier, frontier, index_result,
        route_blocked=blocked, provider_results=provider_results,
        depth=depth["research_depth_decision"],
        verified_checkpoint=verified_checkpoint,
    )
    unplanned = [x for x in pending["items"] if x["classification"] in
                 {"DEPTH_DEFERRED", "DEPTH_CONFLICT"}]
    unplanned_critical = [x["frontier_id"] for x in unplanned if x["kind"] == "CRITICAL"]
    unplanned_required = [x["frontier_id"] for x in unplanned if x["required_for_goal"]]
    follow_up = activate_next_batch(
        pending, frontier, verified_checkpoint,
        depth=depth["research_depth_decision"], route_blocked=blocked,
    )
    prepared_requests = build_requests(pending["ready_query_plans"]) if not blocked else []
    if follow_up.get("state") == "READY_NEXT_BATCH":
        # A verified checkpoint activates the next bounded batch. Consult the
        # shared Index again before proposing any external provider request.
        next_frontier = follow_up["frontier"]
        next_index = query_frontier(
            next_frontier, index_rows,
            semantic_scores=payload.get("semantic_scores"),
            relations=payload.get("index_relations"),
            detail_rows=payload.get("detail_rows"),
            min_results=int(payload.get("index_min_results", 1) or 1),
            top_k=int(payload.get("index_top_k", 5) or 5),
        )
        next_pending = classify_pending(
            task, next_frontier, next_frontier, next_index,
            depth=depth["research_depth_decision"],
            verified_checkpoint=verified_checkpoint,
            provider_results=provider_results,
        )
        follow_up["index_first"] = next_index
        follow_up["pending_actions"] = next_pending
        follow_up["planned_provider_requests"] = build_requests(next_pending["ready_query_plans"])
        follow_up["verification_frontier"] = next_index.get("verification_frontier", [])
        follow_up["external_execution_performed"] = False
    assurance = audit_research(
        task, full_frontier, verified_checkpoint,
        source_snapshots=payload.get("source_snapshots"),
        claim_reviews=payload.get("claim_reviews"),
        # Never take reviewer authority from a caller-supplied research payload.
        # A host with verified reviewer identity may invoke audit_research
        # separately with its authenticated, server-owned policy.
        trusted_reviewer_ids=None,
        source_access_results=payload.get("source_access_results"),
    )
    route = (
        prior["failure_memory"]["replacement_routes"][0]
        if prior["next_action"] == "USE_REPLACEMENT_ROUTE" and prior["failure_memory"]["replacement_routes"]
        else task.get("route_signature")
    )
    plan = {
        "goal": task.get("goal"),
        "task_family": task.get("task_family"),
        "next_action": prior["next_action"],
        "selected_route": route,
        **depth,
        "search_frontier": frontier,
        "index_first": index_result,
        "external_search_frontier": external_frontier,
        "external_search_required": bool(external_frontier),
        "index_verification_required": bool(verification_frontier),
        "unplanned_critical_frontier_ids": unplanned_critical,
        "unplanned_required_frontier_ids": unplanned_required,
        "pending_actions": pending,
        "research_assurance": assurance,
        "operational_research_ready": assurance["operational_research_ready"],
        "next_batch_preview": pending["next_batch_preview"],
        "follow_up_activation": follow_up,
        "planned_provider_requests": prepared_requests,
        "research_complete_eligible": pending["research_complete_eligible"],
        "execution_allowed": not blocked,
    }
    return {
        "schema": "TAKY_MINING_RUN_ORCHESTRATOR_V1",
        "memory_prior": prior,
        "plan": plan,
        "execution_receipt": receipt,
        "memory_learning_proposal": _learning_proposal(task, prior, receipt) if receipt else None,
        "growth_proposal": propose_growth({"task_family":task.get("task_family"),"goal":task.get("goal"),"selected_route":route}, payload.get("outcome",{})) if payload.get("outcome") else None,
        "authority_guard": {
            "current_authority_unchanged": True,
            "memory_auto_promotion": False,
            "failure_auto_resolution": False,
            "user_not_debugger": True,
            "index_retrieval_does_not_decide_domain_use": True,
            "external_mining_only_for_unresolved_index_gap": True,
        },
    }


def advance_provider_batch(payload: dict, runtime_results: dict) -> dict:
    """Bounded receipt-driven continuation using the existing provider/Core contracts.

    The caller supplies a result for each chosen request; this function does
    not access the network, persist a queue, modify CURRENT, or promote data.
    Only the first preferred request for each frontier is dispatched per
    batch. A failed/empty request may advertise the next *different*
    permitted provider on the following turn.
    """
    task = payload.get("task") or {}
    prior_checkpoint = payload.get("verified_checkpoint")
    if prior_checkpoint is not None:
        goal = (prior_checkpoint.get("goal") or {}) if isinstance(prior_checkpoint, dict) else {}
        if (prior_checkpoint.get("schema") != "TAKY_MINING_CORE_CHECKPOINT_V1"
                or goal.get("goal_id") != normalize_goal(task)["goal_id"]):
            return {
                "schema": "TAKY_MINING_PROVIDER_BATCH_ADVANCE_V1",
                "state": "HOLD_CHECKPOINT_GOAL_MISMATCH",
                "execution_batch": None,
                "plan": None,
                "guards": {"network_calls_performed_by_orchestrator": False,
                           "current_authority_unchanged": True},
            }

    initial = orchestrate(payload)
    plan = initial["plan"]
    if not plan["execution_allowed"]:
        return {"schema": "TAKY_MINING_PROVIDER_BATCH_ADVANCE_V1",
                "state": "HOLD_FAILED_ROUTE",
                "execution_batch": None, "plan": plan,
                "guards": {"network_calls_performed_by_orchestrator": False,
                           "current_authority_unchanged": True}}
    requests = plan.get("planned_provider_requests") or []
    follow_up = plan.get("follow_up_activation") or {}
    using_deferred_batch = False
    active_frontier = plan["search_frontier"]
    if not requests and follow_up.get("state") == "READY_NEXT_BATCH":
        requests = follow_up.get("planned_provider_requests") or []
        active_frontier = follow_up["frontier"]
        using_deferred_batch = bool(requests)
    if not requests:
        return {"schema": "TAKY_MINING_PROVIDER_BATCH_ADVANCE_V1",
                "state": "NO_PROVIDER_ACTION", "execution_batch": None, "plan": plan,
                "guards": {"network_calls_performed_by_orchestrator": False,
                           "current_authority_unchanged": True}}

    first_by_frontier = {}
    for req in requests:
        first_by_frontier.setdefault(str(req.get("frontier_id")), req)
    selected = list(first_by_frontier.values())
    batch = execute_batch(selected, runtime_results or {})
    selected_ids = {str(req.get("request_id")) for req in selected}
    access_errors = {"ACCESS_DENIED", "AUTH_REQUIRED", "LOGIN_REQUIRED",
                     "PERMISSION_DENIED", "RESTRICTED", "PAYWALL", "ACCESS_HOLD"}
    successful = {str(row.get("frontier_id")) for row in batch["results"]
                  if row.get("state") == "SUCCESS"
                  and (row.get("receipt") or {}).get("results")}
    for row in batch["results"]:
        fid = str(row.get("frontier_id"))
        error = str(row.get("error") or "").upper()
        if (fid in successful or row.get("state") not in {"FAILED", "EMPTY"}
                or error in access_errors):
            continue
        alternative = next((
            req for req in requests
            if str(req.get("frontier_id")) == fid
            and str(req.get("request_id")) not in selected_ids
            and str(req.get("provider")).upper() != str(row.get("provider")).upper()
        ), None)
        if alternative:
            row["next_provider"] = alternative["provider"]

    prior = prior_checkpoint if prior_checkpoint is not None else core_checkpoint(
        task, plan["search_frontier"], []
    )
    if using_deferred_batch:
        # Extend, never replace, the original Core frontier and goal contract.
        # Previously verified evidence is carried forward exactly once.
        carried = [{
            key: row.get(key) for key in
            ("id", "question", "kind", "origin", "decomposition_id")
            if key in row
        } for row in prior.get("frontier", [])]
        known = {str(row.get("id")) for row in carried}
        carried.extend(dict(row) for row in active_frontier
                       if str(row.get("id")) not in known)
        prior = core_checkpoint(
            prior.get("task_contract") or task,
            carried, list(prior.get("evidence") or []), prior,
        )
    current_checkpoint = (
        apply_external_receipts(
            prior, batch["receipts"],
            index_rows=payload.get("index_rows"),
            index_relations=payload.get("index_relations"),
        ) if batch["receipts"] else prior
    )
    next_input = dict(payload)
    next_input.pop("provider_results", None)
    next_input["verified_checkpoint"] = current_checkpoint
    next_input["execution_batch"] = batch
    updated = orchestrate(next_input)
    return {
        "schema": "TAKY_MINING_PROVIDER_BATCH_ADVANCE_V1",
        "state": "RECONCILED",
        "batch_scope": "DEFERRED_REQUIRED" if using_deferred_batch else "CURRENT",
        "dispatched_request_ids": [req["request_id"] for req in selected],
        "execution_batch": batch,
        "checkpoint": current_checkpoint,
        "plan": updated["plan"],
        "next_run_input": next_input,
        "guards": {
            "network_calls_performed_by_orchestrator": False,
            "results_are_provider_supplied_not_independently_verified": True,
            "checkpoint_is_not_canonical": True,
            "memory_auto_promotion": False,
            "current_authority_unchanged": True,
        },
    }


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); a=p.parse_args()
    out=orchestrate(json.loads(a.input.read_text(encoding="utf-8")))
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["plan"]["execution_allowed"] else 1
if __name__=="__main__": raise SystemExit(main())
