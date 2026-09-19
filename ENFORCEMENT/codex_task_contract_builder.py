#!/usr/bin/env python3
"""Build a Codex task contract from a TAKY runtime record.

The builder does not invent missing product scope. It converts already-authorized
runtime/task context into the canonical Codex task contract shape.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from codex_task_contract_validator import validate

REQUIRED_CONTEXT = [
    "project", "repository", "base_branch", "verified_base_head",
    "allowed_change_scope", "acceptance_tests"
]

def build(record: dict) -> dict:
    missing = [k for k in REQUIRED_CONTEXT if not record.get(k)]
    wm = record.get("working_model")
    if not isinstance(wm, dict):
        missing.append("working_model")
    if missing:
        return {"pass": False, "detected": [f"TASK_CONTEXT_MISSING:{x}" for x in missing]}

    task = {
        "task_id": record.get("task_id"),
        "project": record["project"],
        "repository": record["repository"],
        "base_branch": record["base_branch"],
        "verified_base_head": record["verified_base_head"],
        "role": {"orchestrator": "TAKY", "executor": "CODEX"},
        "objective": wm.get("primary_outcome"),
        "working_model": wm,
        "source_of_truth": record.get("source_of_truth", [
            "current_user_instruction",
            "taky_canonical_rules",
            "verified_live_repository_state",
        ]),
        "change_scope": {
            "allowed": record["allowed_change_scope"],
            "forbidden": record.get("forbidden_change_scope", [
                "unrelated_refactor",
                "silent_requirement_change",
                "direct_production_deploy",
            ]),
        },
        "investigate": record.get("investigate", []),
        "acceptance_tests": record["acceptance_tests"],
        "acceptance_checks": record.get("acceptance_checks", [
            {"criterion": x, "mode": "EVIDENCE_ONLY"} for x in record["acceptance_tests"]
        ]),
        "validation": {
            "required": record.get("required_validation", [
                "diff_scope", "build", "relevant_tests", "regression"
            ]),
            "profile": record.get("validation_profile", "GENERIC_EVIDENCE_V1"),
            "mobile_runtime_required": bool(record.get("mobile_runtime_required", False)),
        },
        "executor_automation": {
            "profile": record.get("executor_profile", "GENERIC_CODEX_V1"),
            "target_repository_local": bool(record.get("target_repository_local", False)),
        },
        "human_approval": {
            "merge_required": bool(record.get("merge_approval_required", True)),
            "production_deploy_required": bool(record.get("production_approval_required", True)),
        },
        "deliverables": record.get("deliverables", [
            "root_cause_or_rationale",
            "changed_files",
            "validation_commands",
            "validation_results",
            "unresolved_risks",
            "commit_ref",
        ]),
        "current_state": "IN_PROGRESS",
        "next_state": "CODEX_DONE",
        "requested_transition": "CODEX_DONE",
        "claims_taky_pass": False,
    }
    errors = validate(task)
    return {
        "pass": not errors,
        "detected": errors,
        "task_contract": task if not errors else None,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = build(record)
    if result["pass"] and args.output:
        args.output.write_text(
            json.dumps(result["task_contract"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
