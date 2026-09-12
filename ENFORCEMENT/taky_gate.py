#!/usr/bin/env python3
"""Deterministic TAKY enforcement/replay gate.

Stdlib-only by design so CI can run without dependency installation.
This gate validates representative execution-state records. It does not invoke an LLM
and therefore does not prove live model behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

HARD_FAILURE_CLASSES = {
    "INTENT_DRIFT",
    "SCOPE_SHRINKAGE",
    "SUBSTITUTE_RESULT",
    "OUTPUT_FORM_MISMATCH",
    "OMISSION",
    "STALE_STATE",
    "UNCLASSIFIED_CONFLICT",
    "PREMATURE_PASS",
    "USER_AS_QA",
    "RECOVERY_FAILED",
    "FALSE_MISSING_DECLARATION",
    "USER_FORCED_RECOVERY",
    "POST_CORRECTION_REOCCURRENCE",
    "MISSING",
    "WRONG_REFLECTION",
    "HANDOFF_LOSS",
    "UNJUSTIFIED_HOLD",
    "UNJUSTIFIED_REJECT",
    "UNRESOLVED_CONFLICT",
    "RULE_NOT_APPLIED",
    "ENFORCEMENT_MISSING",
    "REPLAY_NOT_PERFORMED",
    "STATE_CLAIM_MISMATCH",
    "HUMAN_APPROVAL_MISSING",
}


def b(record: Dict[str, Any], key: str, default: bool = False) -> bool:
    return bool(record.get(key, default))


def i(record: Dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(record.get(key, default))
    except (TypeError, ValueError):
        return default


def validate_record(record: Dict[str, Any]) -> List[str]:
    """Return canonical failure/discrepancy tokens detected for one record."""
    failures: List[str] = []

    # Intent/result fidelity.
    if b(record, "intent_drift"):
        failures.append("INTENT_DRIFT")
    if b(record, "scope_shrunk_without_authority"):
        failures.append("SCOPE_SHRINKAGE")
    if b(record, "substitute_result"):
        failures.append("SUBSTITUTE_RESULT")
    if b(record, "output_form_mismatch"):
        failures.append("OUTPUT_FORM_MISMATCH")
    if b(record, "material_omission"):
        failures.append("OMISSION")
    if b(record, "stale_state_used"):
        failures.append("STALE_STATE")
    if b(record, "unclassified_conflict"):
        failures.append("UNCLASSIFIED_CONFLICT")

    # Negative-existence/recovery pre-response gate.
    if b(record, "negative_existence_claim"):
        paths = i(record, "recovery_paths_checked")
        alternate = b(record, "material_alternate_path_available")
        if paths < 2 and alternate:
            failures.append("RECOVERY_FAILED")
        if b(record, "source_found_after_claim"):
            failures.extend(["RECOVERY_FAILED", "FALSE_MISSING_DECLARATION"])

    if b(record, "user_had_to_recover") and b(record, "source_recoverable_by_taky", True):
        failures.extend(["USER_FORCED_RECOVERY", "USER_AS_QA"])

    if b(record, "post_correction_reoccurrence"):
        failures.append("POST_CORRECTION_REOCCURRENCE")

    # F-02 second-pass/full-scan gate.
    if b(record, "explicit_full_global_scan"):
        if not b(record, "source_family_inventory_complete"):
            failures.append("OMISSION")
        if not b(record, "second_semantic_pass_performed"):
            failures.append("REPLAY_NOT_PERFORMED")

    # F-03 handoff portability gate.
    if b(record, "handoff_requested_maximum"):
        recipient_access = b(record, "recipient_repo_access")
        full_snapshot = b(record, "portable_source_snapshots")
        diff_with_base = b(record, "portable_diff_with_base")
        pointers_only = b(record, "repo_pointers_only")
        if not recipient_access and (pointers_only or not (full_snapshot or diff_with_base)):
            failures.extend(["HANDOFF_LOSS", "SCOPE_SHRINKAGE", "SUBSTITUTE_RESULT"])
        if not b(record, "source_manifest_present"):
            failures.append("OMISSION")
        if not b(record, "evidence_authority_classified"):
            failures.append("UNCLASSIFIED_CONFLICT")
        if not b(record, "resume_simulation_passed"):
            failures.append("HANDOFF_LOSS")

    # F-04 stale handoff/latest correction.
    if b(record, "latest_correction_exists") and not b(record, "latest_correction_applied"):
        failures.extend(["STALE_STATE", "WRONG_REFLECTION"])

    # Mechanically-checkable rule must have an enforcement expression where feasible.
    if b(record, "mechanically_checkable_rule") and not b(record, "enforcement_expression_present"):
        failures.append("ENFORCEMENT_MISSING")

    # F-06 rule application.
    if b(record, "rule_cited") and b(record, "rule_violated"):
        failures.append("RULE_NOT_APPLIED")

    # Replay requirement after correction.
    if b(record, "recurrence_prevention_claim") and not b(record, "representative_replay_performed"):
        failures.append("REPLAY_NOT_PERFORMED")

    # Human approval.
    if b(record, "human_approval_required") and not b(record, "human_approval_present"):
        failures.append("HUMAN_APPROVAL_MISSING")

    # State/history wording consistency.
    if not b(record, "state_manifest_consistent", True):
        failures.append("STATE_CLAIM_MISMATCH")
    ext_state = str(record.get("external_validation_state", "")).upper()
    if b(record, "claims_complete") and ext_state in {"PENDING", "FAIL", "NOT_PERFORMED", "UNVERIFIED"}:
        failures.append("STATE_CLAIM_MISMATCH")

    # External live repository truth boundary.
    if b(record, "claims_live_head_verified") and not b(record, "live_head_independently_verified"):
        failures.append("STATE_CLAIM_MISMATCH")

    # Completion is blocked by any detected hard failure.
    if b(record, "claims_complete") and any(f in HARD_FAILURE_CLASSES for f in failures):
        failures.append("PREMATURE_PASS")

    # De-duplicate while preserving order.
    return list(dict.fromkeys(failures))


def run_case(case: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    detected = validate_record(case.get("record", {}))
    expected = case.get("expected_detected", [])
    expected_set = set(expected)
    detected_set = set(detected)
    mode = case.get("expectation", "exact")

    if mode == "exact":
        ok = detected_set == expected_set
    elif mode == "contains":
        ok = expected_set.issubset(detected_set)
    elif mode == "clean":
        ok = not detected
    else:
        raise ValueError(f"Unknown expectation mode: {mode}")

    return ok, {
        "id": case.get("id"),
        "phase": case.get("phase"),
        "expectation": mode,
        "expected_detected": expected,
        "detected": detected,
        "pass": ok,
    }


def replay(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    results = []
    failed = 0
    for case in cases:
        ok, result = run_case(case)
        results.append(result)
        if not ok:
            failed += 1

    out = {
        "fixture_version": payload.get("fixture_version"),
        "case_count": len(results),
        "passed": len(results) - failed,
        "failed": failed,
        "results": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=Path, help="Replay fixture JSON")
    parser.add_argument("--record", type=Path, help="Validate one execution-state JSON record")
    args = parser.parse_args()

    if bool(args.replay) == bool(args.record):
        parser.error("Provide exactly one of --replay or --record")

    if args.replay:
        return replay(args.replay)

    record = json.loads(args.record.read_text(encoding="utf-8"))
    failures = validate_record(record)
    print(json.dumps({"detected": failures, "pass": not failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
