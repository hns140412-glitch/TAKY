#!/usr/bin/env python3
"""Quantitative evaluator for Mining Engine V2 L5 anticipation.

Measures whether the engine anticipates useful next research without inflating
the frontier or choosing an unnecessarily deep research mode.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_SECTIONS = {
    "KNOWN",
    "WEAK",
    "UNKNOWN",
    "CONFLICT",
    "FOUNDATION_REQUIREMENTS",
    "ADVANCED_REQUIREMENTS",
    "ALTERNATIVE_PATHS",
    "SEARCH_FRONTIER",
    "READY_FOR_USER",
}


def _frontier_ids(run: dict) -> set[str]:
    out = set()
    for item in run.get("SEARCH_FRONTIER", []) or []:
        if not isinstance(item, dict):
            continue
        value = item.get("id") or item.get("frontier_id") or item.get("question")
        if value:
            out.add(str(value))
    return out


def evaluate_anticipation(run: dict, gold: dict) -> dict:
    present = sum(1 for key in REQUIRED_SECTIONS if run.get(key))
    structure_score = present / len(REQUIRED_SECTIONS)

    produced = _frontier_ids(run)
    expected = {str(x) for x in gold.get("expected_frontier_ids", [])}
    useful = len(produced & expected)

    precision = useful / len(produced) if produced else (1.0 if not expected else 0.0)
    recall = useful / len(expected) if expected else 1.0
    inflation = len(produced - expected)
    inflation_penalty = min(1.0, inflation / max(1, len(expected) or 1))

    expected_depth = gold.get("expected_depth")
    actual_depth = run.get("research_depth_decision")
    depth_match = actual_depth == expected_depth

    expected_ready = bool(gold.get("ready_for_user"))
    actual_ready = bool(run.get("READY_FOR_USER"))
    ready_match = actual_ready == expected_ready

    raw = (
        structure_score * 0.20
        + precision * 0.25
        + recall * 0.20
        + (1.0 if depth_match else 0.0) * 0.20
        + (1.0 if ready_match else 0.0) * 0.15
    )
    score = max(0.0, raw - 0.15 * inflation_penalty)

    threshold = float(gold.get("pass_threshold", 0.80))
    passed = (
        score >= threshold
        and precision >= float(gold.get("min_precision", 0.75))
        and depth_match
    )

    return {
        "pass": passed,
        "score": round(score, 4),
        "structure_score": round(structure_score, 4),
        "frontier_precision": round(precision, 4),
        "frontier_recall": round(recall, 4),
        "frontier_inflation": inflation,
        "research_depth_match": depth_match,
        "ready_for_user_match": ready_match,
        "expected_depth": expected_depth,
        "actual_depth": actual_depth,
    }


def evaluate_suite(payload: dict) -> dict:
    results = []
    for case in payload.get("cases", []):
        result = evaluate_anticipation(case.get("run", {}), case.get("gold", {}))
        result["case_id"] = case.get("case_id")
        result["task_family"] = case.get("task_family")
        results.append(result)

    passed = sum(1 for result in results if result["pass"])
    total = len(results)
    return {
        "pass": total > 0 and passed == total,
        "passed": passed,
        "total": total,
        "average_score": round(
            sum(result["score"] for result in results) / total, 4
        ) if total else 0.0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate_suite(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
