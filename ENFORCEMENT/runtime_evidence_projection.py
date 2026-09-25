#!/usr/bin/env python3
"""Project runtime results into compact success or diagnostic failure evidence.

This is an output projection only. It never changes the underlying runtime result.
"""
from __future__ import annotations


SUCCESS_FIELDS = (
    "pass",
    "authorized_to_continue",
    "route",
    "claim_ceiling",
)

FAILURE_FIELDS = (
    "pass",
    "authorized_to_continue",
    "detected",
    "runtime_state",
    "route",
    "checkpoint_guard",
    "reference_intake_route",
    "learning_evidence_gap_route",
    "claim_ceiling",
)


def project(result: dict) -> dict:
    passed = result.get("pass") is True
    fields = SUCCESS_FIELDS if passed else FAILURE_FIELDS
    evidence = {key: result.get(key) for key in fields if key in result}
    evidence["projection_mode"] = "SUCCESS_COMPACT" if passed else "FAILURE_DIAGNOSTIC"
    evidence["full_result_preserved"] = True
    return evidence
