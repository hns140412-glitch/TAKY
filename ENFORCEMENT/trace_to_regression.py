#!/usr/bin/env python3
"""Convert confirmed runtime failure evidence into a reusable regression case.

This module is intentionally narrow. It does not ingest arbitrary logs, does not
promote UNKNOWN outcomes, and does not mutate canonical policy.
"""
from __future__ import annotations

import hashlib
import json


CONFIRMED_FAILURE_STATES = {"FAILED_CONFIRMED", "REGRESSION_FAIL"}


def _clean(value):
    return str(value or "").strip()


def build_case(event: dict) -> dict:
    state = _clean(event.get("outcome_state")).upper()
    if state not in CONFIRMED_FAILURE_STATES:
        return {
            "pass": False,
            "detected": ["REGRESSION_SOURCE_NOT_CONFIRMED_FAILURE"],
            "regression_case": None,
        }

    source_ref = _clean(event.get("source_ref"))
    invariant = _clean(event.get("invariant"))
    observed = event.get("observed")
    expected = event.get("expected")
    task_family = _clean(event.get("task_family")).upper()

    missing = []
    if not source_ref:
        missing.append("source_ref")
    if not invariant:
        missing.append("invariant")
    if not task_family:
        missing.append("task_family")
    if observed is None:
        missing.append("observed")
    if expected is None:
        missing.append("expected")

    if missing:
        return {
            "pass": False,
            "detected": [f"REGRESSION_SOURCE_MISSING:{x}" for x in missing],
            "regression_case": None,
        }

    identity = {
        "task_family": task_family,
        "invariant": invariant,
        "source_ref": source_ref,
        "expected": expected,
        "observed": observed,
    }
    digest = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]

    return {
        "pass": True,
        "detected": [],
        "regression_case": {
            "case_id": "REG-" + digest,
            "task_family": task_family,
            "invariant": invariant,
            "expected": expected,
            "prior_observed_failure": observed,
            "source_ref": source_ref,
            "source_outcome_state": state,
            "status": "CANDIDATE",
            "auto_promote": False,
        },
    }
