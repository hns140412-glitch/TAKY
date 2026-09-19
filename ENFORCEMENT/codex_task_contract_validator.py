#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

REQUIRED = [
    "task_id", "project", "repository", "base_branch", "verified_base_head",
    "role", "objective", "source_of_truth", "change_scope", "acceptance_tests",
    "validation", "human_approval", "deliverables", "requested_transition"
]

ALLOWED_TRANSITIONS = {
    "READY": {"ASSIGNED_TO_CODEX"},
    "ASSIGNED_TO_CODEX": {"IN_PROGRESS"},
    "IN_PROGRESS": {"CODEX_DONE"},
    "CODEX_DONE": {"TAKY_REVIEW"},
    "TAKY_REVIEW": {"REWORK", "HUMAN_APPROVAL"},
    "REWORK": {"ASSIGNED_TO_CODEX", "IN_PROGRESS"},
    "HUMAN_APPROVAL": {"MERGED"},
    "MERGED": {"DEPLOYED"},
    "DEPLOYED": set(),
}


def fail(errors, message):
    errors.append(message)


def validate(record):
    errors = []
    for field in REQUIRED:
        if field not in record or record[field] in (None, "", [], {}):
            fail(errors, f"TASK_CONTRACT_INCOMPLETE:{field}")

    role = record.get("role", {})
    if role.get("orchestrator") != "TAKY":
        fail(errors, "ROLE_OWNER_VIOLATION:orchestrator_must_be_TAKY")
    if role.get("executor") != "CODEX":
        fail(errors, "ROLE_OWNER_VIOLATION:executor_must_be_CODEX")

    scope = record.get("change_scope", {})
    if not scope.get("allowed"):
        fail(errors, "TASK_CONTRACT_INCOMPLETE:change_scope.allowed")
    forbidden = set(scope.get("forbidden", []))
    for required_lock in {"unrelated_refactor", "silent_requirement_change", "direct_production_deploy"}:
        if required_lock not in forbidden:
            fail(errors, f"SCOPE_LOCK_MISSING:{required_lock}")

    acceptance = record.get("acceptance_tests", [])
    if not acceptance:
        fail(errors, "TASK_CONTRACT_INCOMPLETE:acceptance_tests")

    checks = record.get("acceptance_checks", [])
    if checks:
        seen = set()
        for item in checks:
            if not isinstance(item, dict):
                fail(errors, "ACCEPTANCE_CHECK_INVALID")
                continue
            criterion = str(item.get("criterion", "")).strip()
            mode = str(item.get("mode", "")).strip().upper()
            if criterion not in acceptance:
                fail(errors, f"ACCEPTANCE_CHECK_UNKNOWN_CRITERION:{criterion or 'MISSING'}")
            if mode not in {"EVIDENCE_ONLY", "MANUAL", "PROFILE_CHECK"}:
                fail(errors, f"ACCEPTANCE_CHECK_INVALID_MODE:{mode or 'MISSING'}")
            if "command" in item:
                fail(errors, "UNTRUSTED_TASK_COMMAND:acceptance_checks.command")
            if criterion:
                seen.add(criterion)
        for criterion in acceptance:
            if criterion not in seen:
                fail(errors, f"ACCEPTANCE_CHECK_MISSING:{criterion}")

    validation = record.get("validation", {})
    required_validation = set(validation.get("required", []))
    for gate in {"diff_scope", "build", "relevant_tests", "regression"}:
        if gate not in required_validation:
            fail(errors, f"VALIDATION_GATE_MISSING:{gate}")
    profile = str(validation.get("profile", "")).strip()
    if not profile:
        fail(errors, "TASK_CONTRACT_INCOMPLETE:validation.profile")
    if "commands" in validation or "command" in validation:
        fail(errors, "UNTRUSTED_TASK_COMMAND:validation")

    automation = record.get("executor_automation", {})
    if automation:
        if not str(automation.get("profile", "")).strip():
            fail(errors, "TASK_CONTRACT_INCOMPLETE:executor_automation.profile")
        if "target_repository_local" not in automation:
            fail(errors, "TASK_CONTRACT_INCOMPLETE:executor_automation.target_repository_local")

    requested = record.get("requested_transition")
    if requested not in {"CODEX_DONE", "REWORK", "TAKY_REVIEW", "HUMAN_APPROVAL", "MERGED", "DEPLOYED"}:
        fail(errors, f"INVALID_REQUESTED_TRANSITION:{requested}")

    current = record.get("current_state")
    next_state = record.get("next_state")
    if current or next_state:
        if not current or not next_state:
            fail(errors, "STATE_TRANSITION_INCOMPLETE")
        elif next_state not in ALLOWED_TRANSITIONS.get(current, set()):
            fail(errors, f"FORBIDDEN_STATE_TRANSITION:{current}->{next_state}")

    approval = record.get("human_approval", {})
    if next_state == "MERGED" and approval.get("merge_required", False) and not record.get("human_approval_evidence"):
        fail(errors, "HUMAN_APPROVAL_MISSING:merge")
    if next_state == "DEPLOYED" and approval.get("production_deploy_required", False) and not record.get("human_approval_evidence"):
        fail(errors, "HUMAN_APPROVAL_MISSING:production_deploy")

    if record.get("claims_taky_pass") and record.get("current_state") in {"READY", "ASSIGNED_TO_CODEX", "IN_PROGRESS", "CODEX_DONE"}:
        fail(errors, "PREMATURE_PASS")

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    data = json.loads(args.record.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("CODEX_TASK_CONTRACT_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
