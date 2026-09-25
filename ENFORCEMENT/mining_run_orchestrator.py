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

DEPTH_ORDER = {"D0":0,"D1":1,"D2":2,"D3":3,"D4":4}

def build_frontier(task: dict, depth: str) -> list[dict]:
    if depth == "D0": return []
    items, seen = [], set()
    for kind, values in (
        ("UNKNOWN", task.get("unknown", [])),
        ("CONFLICT", task.get("conflict", [])),
        ("FOUNDATION", task.get("foundation_requirements", [])),
        ("ADVANCED", task.get("advanced_requirements", [])),
    ):
        for value in values or []:
            key = str(value).strip()
            if key and key not in seen:
                seen.add(key)
                items.append({"id": key, "kind": kind, "question": key})
    limit = {"D1":2,"D2":4,"D3":6,"D4":10}.get(depth, 0)
    return items[:limit]

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
    frontier = build_frontier(task, depth["research_depth_decision"])
    if not frontier and task.get("decomposed_frontier"):
        limit={"D0":0,"D1":2,"D2":4,"D3":6,"D4":10}.get(depth["research_depth_decision"],0)
        frontier=list(task.get("decomposed_frontier",[]))[:limit]
    blocked = prior["next_action"] == "HOLD_FAILED_ROUTE"
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
        },
    }

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); a=p.parse_args()
    out=orchestrate(json.loads(a.input.read_text(encoding="utf-8")))
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["plan"]["execution_allowed"] else 1
if __name__=="__main__": raise SystemExit(main())
