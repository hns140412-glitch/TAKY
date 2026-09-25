#!/usr/bin/env python3
"""Small observable-behavior evaluator for TAKY runtime evidence.

It evaluates selected invariants separately from final task outcome.
Only simple data assertions are supported; it never executes commands.
"""
from __future__ import annotations

from typing import Any

SUPPORTED_KINDS = {"REQUIRED_TRUE", "REQUIRED_FALSE", "EQUALS", "CONTAINS"}


def _get_path(value: Any, path: str):
    current = value
    for part in str(path or "").split("."):
        if not part:
            return None, False
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None, False
    return current, True


def evaluate(observed: dict, assertions: list[dict]) -> dict:
    results = []
    detected = []

    for index, assertion in enumerate(assertions or []):
        if not isinstance(assertion, dict):
            detected.append(f"BEHAVIOR_ASSERTION_INVALID:{index}")
            continue

        name = str(assertion.get("name") or f"assertion_{index}").strip()
        kind = str(assertion.get("kind", "")).strip().upper()
        path = str(assertion.get("path", "")).strip()

        if kind not in SUPPORTED_KINDS:
            detected.append(f"BEHAVIOR_ASSERTION_KIND_UNSUPPORTED:{name}")
            continue
        if not path:
            detected.append(f"BEHAVIOR_ASSERTION_PATH_MISSING:{name}")
            continue

        actual, exists = _get_path(observed, path)
        expected = assertion.get("expected")

        if kind == "REQUIRED_TRUE":
            passed = exists and actual is True
        elif kind == "REQUIRED_FALSE":
            passed = exists and actual is False
        elif kind == "EQUALS":
            passed = exists and actual == expected
        else:
            passed = exists and isinstance(actual, (list, tuple, set, str)) and expected in actual

        results.append(
            {
                "name": name,
                "kind": kind,
                "path": path,
                "pass": bool(passed),
                "actual": actual if exists else None,
                "expected": expected,
            }
        )
        if not passed:
            detected.append(f"BEHAVIOR_ASSERTION_FAILED:{name}")

    return {
        "pass": not detected,
        "detected": detected,
        "results": results,
        "invariant": "FINAL_OUTPUT_PASS != EXECUTION_PATH_PASS",
    }
