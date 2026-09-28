#!/usr/bin/env python3
"""Read-only, deterministic evidence review for TKY-GROWTH-001.

This is a small manual/CI review helper, NOT a monitor, task scheduler,
autonomous agent, owner decision, permission check, or proof of live outcomes.
Owner supplies meaningful outcome assessment; the helper only checks
provenance and whether declared changes/evidence justify reconsideration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AFTER_STATES = {"OBSERVED", "NOT_OBSERVED", "UNVERIFIED"}
OUTCOMES = {"MET", "MISSED", "UNKNOWN"}
TRIGGER_STATES = {"MATERIAL_CHANGE", "NO_MATERIAL_CHANGE", "UNKNOWN"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def refs(value):
    return isinstance(value, list) and bool(value) and all(nonempty(v) for v in value)


def assess(record):
    """No implicit cross-domain comparison; never grants approval or execution."""
    errors = []
    for field in ("observation_id", "owner", "target_ref", "human_outcome",
                  "change_ref", "required_evidence_scope"):
        if not nonempty(record.get(field)):
            errors.append("REQUIRED:" + field)
    base = record.get("before")
    after = record.get("after")
    trigger = record.get("trigger")
    if not isinstance(base, dict) or base.get("state") not in {"OBSERVED", "UNVERIFIED"}:
        errors.append("BEFORE_STATE_INVALID")
        base = {}
    if not isinstance(after, dict) or after.get("state") not in AFTER_STATES:
        errors.append("AFTER_STATE_INVALID")
        after = {}
    if not isinstance(trigger, dict) or trigger.get("state") not in TRIGGER_STATES:
        errors.append("TRIGGER_STATE_INVALID")
        trigger = {}
    if base.get("state") == "OBSERVED" and not refs(base.get("evidence_refs")):
        errors.append("BEFORE_OBSERVATION_REFS_REQUIRED")
    if after.get("state") == "OBSERVED":
        if after.get("outcome") not in OUTCOMES:
            errors.append("AFTER_OUTCOME_INVALID")
        if not nonempty(after.get("evidence_scope")) or not refs(after.get("evidence_refs")):
            errors.append("AFTER_OBSERVATION_REFS_SCOPE_REQUIRED")
    if trigger.get("state") == "MATERIAL_CHANGE":
        if not nonempty(trigger.get("change_kind")) or not refs(trigger.get("evidence_refs")):
            errors.append("MATERIAL_CHANGE_EVIDENCE_REQUIRED")

    def result(status, reason):
        return {
            "observation_id": record.get("observation_id"),
            "owner": record.get("owner"),
            "status": status,
            "reason": reason,
            "errors": errors,
            "execution_authorized": False,
            "owner_decision_made": False,
            "automatic_current_promotion": False,
        }

    if errors:
        return result("RECORD_INVALID", "Malformed or unsupported evidence; no outcome claim")
    if trigger["state"] == "MATERIAL_CHANGE":
        return result("RECHECK_REQUIRED", "Owner-declared material change has cited evidence")
    if after["state"] != "OBSERVED" or after.get("outcome") == "UNKNOWN":
        return result("AWAITING_OUTCOME", "No verified outcome assessment in requested scope")
    if after["outcome"] == "MISSED":
        return result("OUTCOME_GAP", "Observed result did not meet owner-declared target")
    if trigger["state"] == "UNKNOWN":
        return result("WATCH_UNVERIFIED", "Material change status not established")
    if after["evidence_scope"] != record["required_evidence_scope"]:
        return result("EVIDENCE_SCOPE_GAP", "Available result does not prove requested evidence scope")
    if base["state"] != "OBSERVED":
        return result("BASELINE_UNVERIFIED", "Cannot claim a before/after improvement without baseline evidence")
    return result("OBSERVED_TARGET_MET_CANDIDATE",
                  "Evidence matches declared scope; only owner review can adopt or close")


def self_test(path):
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = fixture["cases"]
    names = set()
    for item in cases:
        name = item["name"]
        assert name not in names, "duplicate fixture: " + name
        names.add(name)
        evaluated = assess(item["record"])
        assert evaluated["status"] == item["expected_status"], (name, evaluated)
        assert not any(evaluated[k] for k in ("execution_authorized", "owner_decision_made",
                                             "automatic_current_promotion")), name
    assert len(cases) >= 7, "Insufficient negative-case coverage"
    print(f"PASS: outcome observation replay: {len(cases)} cases / no auto action or promotion")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="Observation record JSON or list of records")
    parser.add_argument("--self-test", dest="fixture", help="Run local fixture cases")
    args = parser.parse_args()
    if args.fixture:
        self_test(args.fixture)
        return
    if not args.input:
        parser.error("provide an input JSON file or --self-test")
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    records = data if isinstance(data, list) else [data]
    output = [assess(record) for record in records]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if any(item["status"] == "RECORD_INVALID" for item in output):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
