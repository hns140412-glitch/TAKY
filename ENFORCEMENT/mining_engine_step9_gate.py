#!/usr/bin/env python3
"""Unified Step 9 quality gate for TAKY Mining Engine V2.

Runs CURRENT reconciliation, L5 anticipation evaluation, strategy/failure
memory checks, regression expectations, and cross-validation invariants in one
promotion-blocking decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from anticipation_evaluator import evaluate_suite
from current_reconciler import reconcile
from strategy_failure_memory import prepare_next_run


def _expect(result: dict, expected: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for key, value in expected.items():
        if key == "selected_file_id":
            actual = (result.get("selected") or {}).get("file_id")
        else:
            actual = result.get(key)
        if actual != value:
            errors.append(f"{key}: expected={value!r} actual={actual!r}")
    return (not errors, errors)


def _run_current_cases(cases: list[dict]) -> dict:
    results = []
    for case in cases:
        output = reconcile(
            case.get("candidates", []),
            explicit_current_pointer=case.get("explicit_current_pointer"),
        )
        passed, errors = _expect(output, case.get("expected", {}))
        results.append({
            "case_id": case.get("case_id"),
            "critical": bool(case.get("critical", True)),
            "pass": passed,
            "errors": errors,
            "output": output,
        })
    return {"results": results}


def _run_memory_cases(cases: list[dict], memory: dict) -> dict:
    results = []
    for case in cases:
        output = prepare_next_run(case.get("task", {}), memory)
        passed, errors = _expect(output, case.get("expected", {}))
        results.append({
            "case_id": case.get("case_id"),
            "critical": bool(case.get("critical", True)),
            "pass": passed,
            "errors": errors,
            "output": output,
        })
    return {"results": results}


def _cross_validate_current(cases: list[dict]) -> dict:
    results = []
    for case in cases:
        candidates = case.get("candidates", [])
        pointer = case.get("explicit_current_pointer")
        a = reconcile(candidates, explicit_current_pointer=pointer)
        b = reconcile(list(reversed(candidates)), explicit_current_pointer=pointer)
        same = (
            a.get("status") == b.get("status")
            and a.get("reason") == b.get("reason")
            and (a.get("selected") or {}).get("file_id")
            == (b.get("selected") or {}).get("file_id")
            and sorted(x.get("file_id") for x in a.get("duplicates", []))
            == sorted(x.get("file_id") for x in b.get("duplicates", []))
            and sorted(x for x in a.get("conflicts", []) if x is not None)
            == sorted(x for x in b.get("conflicts", []) if x is not None)
        )
        results.append({
            "case_id": case.get("case_id"),
            "pass": same,
            "forward": a,
            "reversed": b,
        })
    return {"results": results}


def run_gate(payload: dict) -> dict:
    current = _run_current_cases(payload.get("current_cases", []))
    anticipation = evaluate_suite(payload.get("anticipation_suite", {}))
    memory = _run_memory_cases(
        payload.get("memory_cases", []), payload.get("memory", {})
    )
    cross = _cross_validate_current(payload.get("current_cases", []))

    critical_failures = []
    for group_name, group in (("CURRENT", current), ("MEMORY", memory)):
        for result in group["results"]:
            if result["critical"] and not result["pass"]:
                critical_failures.append(f"{group_name}:{result['case_id']}")

    if not anticipation.get("pass", False):
        critical_failures.append("ANTICIPATION_SUITE")

    for result in cross["results"]:
        if not result["pass"]:
            critical_failures.append(f"CROSS_VALIDATION:{result['case_id']}")

    promotion_ready = not critical_failures
    return {
        "schema": "TAKY_MINING_ENGINE_STEP9_GATE_V1",
        "current_regression": current,
        "anticipation_eval": anticipation,
        "strategy_failure_memory": memory,
        "cross_validation": cross,
        "critical_failures": critical_failures,
        "promotion_ready": promotion_ready,
        "promotion_decision": "PASS_TO_ADVERSARIAL_REVIEW" if promotion_ready else "HOLD",
        "guard": "Step 9 passing does not itself promote the engine; adversarial review remains required.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = run_gate(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["promotion_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
