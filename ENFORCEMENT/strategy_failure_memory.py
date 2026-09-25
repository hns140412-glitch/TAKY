#!/usr/bin/env python3
"""Executable Strategy/Failure memory for TAKY Mining Engine V2.

This module changes the next mining run from prior experience without allowing
memory to override CURRENT authority or evidence boundaries.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

TOKEN_RE = re.compile(r"[A-Za-z0-9_가-힣]+")


def _tokens(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(x) for x in value)
    else:
        text = str(value)
    return {
        match.group(0).lower()
        for match in TOKEN_RE.finditer(text)
        if len(match.group(0)) >= 2
    }


def _similarity(a, b) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def select_strategy(
    task: dict,
    strategies: Iterable[dict],
    min_similarity: float = 0.15,
) -> dict:
    family = str(task.get("task_family", "")).strip().upper()
    goal = task.get("goal", "")
    candidates = []

    for strategy in strategies:
        if str(strategy.get("status", "")).upper() != "PROMOTED":
            continue

        sfamily = str(strategy.get("task_family", "")).strip().upper()

        # A promoted strategy from another explicit task family must never leak
        # into this run merely because goal text happens to look similar.
        if family and sfamily and sfamily != family:
            continue

        family_score = 1.0 if family and sfamily == family else 0.0
        goal_score = _similarity(goal, strategy.get("goal_pattern", ""))
        score = 0.65 * family_score + 0.35 * goal_score
        if score >= min_similarity:
            candidates.append(
                (score, str(strategy.get("strategy_id", "")), strategy)
            )

    if not candidates:
        return {
            "selected": None,
            "score": 0.0,
            "reason": "NO_PROMOTED_MATCH",
        }

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    score, _, selected = candidates[0]
    return {
        "selected": selected,
        "score": round(score, 4),
        "reason": "PROMOTED_STRATEGY_MATCH",
    }


def apply_failure_memory(task: dict, failures: Iterable[dict]) -> dict:
    route = str(task.get("route_signature", "")).strip()
    family = str(task.get("task_family", "")).strip().upper()
    blocks = []
    replacements = []

    for failure in failures:
        if str(failure.get("state", "")).upper() not in {
            "RESOLVED",
            "QUARANTINED",
            "OPEN",
        }:
            continue

        failed_route = str(failure.get("route_signature", "")).strip()
        ffamily = str(failure.get("task_family", "")).strip().upper()

        if (
            route
            and failed_route == route
            and (not ffamily or not family or ffamily == family)
        ):
            unchanged_retry = (
                failure.get("new_evidence_required", True)
                and not task.get("has_new_evidence", False)
                and not task.get("materially_changed_method", False)
            )
            if unchanged_retry:
                blocks.append(failure)
                replacements.extend(failure.get("replacement_routes", []) or [])

    return {
        "blocked": bool(blocks),
        "matched_failure_ids": [
            failure.get("failure_id") for failure in blocks
        ],
        "replacement_routes": list(
            dict.fromkeys(str(route) for route in replacements if route)
        ),
        "reason": (
            "KNOWN_FAILED_ROUTE_BLOCKED"
            if blocks
            else "NO_BLOCKING_FAILURE_MEMORY"
        ),
    }


def prepare_next_run(task: dict, memory: dict) -> dict:
    failure = apply_failure_memory(task, memory.get("failures", []))
    strategy = select_strategy(task, memory.get("strategies", []))

    return {
        "task_family": task.get("task_family"),
        "goal": task.get("goal"),
        "failure_memory": failure,
        "strategy_memory": strategy,
        "authority_guard": {
            "memory_can_override_current": False,
            "memory_can_override_source_authority": False,
            "memory_role": "ADVISORY_EXECUTION_PRIOR",
        },
        "next_action": (
            "USE_REPLACEMENT_ROUTE"
            if failure["blocked"] and failure["replacement_routes"]
            else "HOLD_FAILED_ROUTE"
            if failure["blocked"]
            else "USE_PROMOTED_STRATEGY"
            if strategy["selected"]
            else "PLAN_WITHOUT_MEMORY_PRIOR"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--memory", type=Path, required=True)
    args = parser.parse_args()

    task = json.loads(args.task.read_text(encoding="utf-8"))
    memory = json.loads(args.memory.read_text(encoding="utf-8"))
    result = prepare_next_run(task, memory)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["next_action"] == "HOLD_FAILED_ROUTE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
