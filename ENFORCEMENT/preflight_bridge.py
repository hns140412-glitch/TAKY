#!/usr/bin/env python3
"""Canonical repository-level TAKY preflight bridge.

Combines evidence-reference integrity validation with the existing TAKY deterministic gate.
This proves repository-executable preflight only. It does NOT prove hosted ChatGPT native
tool calls automatically invoke this bridge.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from evidence_ref_validator import validate_manifest
from taky_gate import validate_record


def run(record: dict, repo_root: Path) -> dict:
    failures = []
    evidence_failures = validate_manifest(record, repo_root)
    if record.get("pre_execution_gate_required"):
        required = ["applicable_rule_refs", "context_evidence_refs", "history_query_refs"]
        if record.get("resumed_or_context_compacted"):
            required.append("preflight_rehydration_evidence_refs")
        for bucket in required:
            refs = record.get(bucket)
            if not isinstance(refs, list) or not refs:
                failures.append(f"{bucket}:MISSING")
    failures.extend(evidence_failures)
    failures.extend(validate_record(record))
    unique = list(dict.fromkeys(failures))
    return {
        "pass": not unique,
        "detected": unique,
        "runtime_claim_ceiling": "REPOSITORY_EXECUTABLE_CI_ENFORCED",
        "live_runtime_auto_invocation_verified": bool(record.get("live_runtime_auto_invocation_verified", False)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    a = ap.parse_args()
    record = json.loads(a.record.read_text(encoding="utf-8"))
    result = run(record, a.repo_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
