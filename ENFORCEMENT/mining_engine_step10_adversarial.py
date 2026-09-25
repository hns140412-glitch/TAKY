#!/usr/bin/env python3
"""Adversarial review gate for TAKY Mining Engine V2.

The gate attempts to break CURRENT reconciliation, anticipation discipline,
and strategy/failure-memory boundaries. Passing means the known adversarial
attacks were resisted; it is not equivalent to full production promotion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from anticipation_evaluator import evaluate_anticipation
from current_reconciler import reconcile
from strategy_failure_memory import prepare_next_run


def _match(actual: dict, expected: dict) -> tuple[bool, list[str]]:
    errors = []
    for key, value in expected.items():
        if key == "selected_file_id":
            observed = (actual.get("selected") or {}).get("file_id")
        elif key.startswith("authority_guard."):
            observed = actual.get("authority_guard", {}).get(key.split(".", 1)[1])
        else:
            observed = actual.get(key)
        if observed != value:
            errors.append(f"{key}: expected={value!r} actual={observed!r}")
    return not errors, errors


def run_adversarial(payload: dict) -> dict:
    results = []

    for case in payload.get("current_attacks", []):
        output = reconcile(
            case.get("candidates", []),
            explicit_current_pointer=case.get("explicit_current_pointer"),
        )
        passed, errors = _match(output, case.get("expected", {}))
        results.append({
            "attack_id": case.get("attack_id"),
            "surface": "CURRENT",
            "pass": passed,
            "errors": errors,
            "output": output,
        })

    for case in payload.get("anticipation_attacks", []):
        output = evaluate_anticipation(case.get("run", {}), case.get("gold", {}))
        should_pass = bool(case.get("should_pass", False))
        passed = bool(output.get("pass")) == should_pass
        results.append({
            "attack_id": case.get("attack_id"),
            "surface": "ANTICIPATION",
            "pass": passed,
            "errors": [] if passed else [
                f"expected evaluator pass={should_pass} actual={output.get('pass')}"
            ],
            "output": output,
        })

    memory = payload.get("memory", {})
    for case in payload.get("memory_attacks", []):
        output = prepare_next_run(case.get("task", {}), memory)
        passed, errors = _match(output, case.get("expected", {}))
        results.append({
            "attack_id": case.get("attack_id"),
            "surface": "MEMORY",
            "pass": passed,
            "errors": errors,
            "output": output,
        })

    failed = [r["attack_id"] for r in results if not r["pass"]]
    return {
        "schema": "TAKY_MINING_ENGINE_STEP10_ADVERSARIAL_V1",
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": failed,
        "pass": bool(results) and not failed,
        "promotion_decision": "ADVERSARIAL_PASS" if results and not failed else "HOLD",
        "results": results,
        "guard": "Adversarial pass permits promotion review only; it does not prove unseen-goal generalization.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = run_adversarial(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
