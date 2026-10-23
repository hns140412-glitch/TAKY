#!/usr/bin/env python3
"""Build a Codex task contract from a TAKY runtime record.

The builder does not invent missing product scope. It converts already-authorized
runtime/task context into the canonical Codex task contract shape.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from codex_task_contract_validator import validate

REQUIRED_CONTEXT = [
    "project", "repository", "base_branch", "verified_base_head",
    "allowed_change_scope", "acceptance_tests"
]

def _effect_policy(record: dict) -> dict | None:
    configured = any(
        key in record
        for key in (
            "effect_class",
            "side_effect_request",
            "retry_budget",
            "reconcile_before_retry",
            "compensation_ref",
        )
    )
    if not configured:
        return None

    effect_class = str(record.get("effect_class", "READ_ONLY")).strip().upper()
    payload = record.get("side_effect_request")
    request_fingerprint = None
    if isinstance(payload, dict):
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        request_fingerprint = hashlib.sha256(canonical).hexdigest()

    return {
        "effect_class": effect_class,
        "request_fingerprint": request_fingerprint,
        "reconcile_before_retry": bool(
            record.get(
                "reconcile_before_retry",
                effect_class == "NON_IDEMPOTENT_MUTATION",
            )
        ),
        "retry_budget": record.get(
            "retry_budget",
            0 if effect_class == "READ_ONLY" else 1,
        ),
        "compensation_ref": record.get("compensation_ref"),
    }

def _user_intent(record: dict) -> tuple[dict | None, list[str]]:
    """Carry the user's literal request and latest correction into the task contract.

    Returns (fields, errors). No intent_contract -> nothing is invented (a material review
    then fails closed on ORIGINAL_USER_INTENT_MISSING). A present but untraceable one is an
    error so the user's words are never silently dropped or replaced by an assistant restatement.
    """
    contract = record.get("intent_contract")
    if contract is None:
        return None, []
    if not isinstance(contract, dict):
        return None, ["TASK_INTENT_CONTRACT_INVALID"]
    literal = contract.get("literal_user_request")
    correction = contract.get("latest_user_correction", "")
    source_id = contract.get("user_source_id")
    errors = []
    if not isinstance(literal, str) or not literal.strip():
        errors.append("TASK_INTENT_LITERAL_MISSING")
    if not isinstance(correction, str):
        errors.append("TASK_INTENT_CORRECTION_INVALID")
    refs = record.get("context_evidence_refs")
    known = {v.get("source_id") for v in refs if isinstance(v, dict)} if isinstance(refs, list) else set()
    if not isinstance(source_id, str) or source_id not in known:
        errors.append("TASK_INTENT_SOURCE_UNBOUND")
    if errors:
        return None, errors
    fields = {"original_user_intent": {"source": "user", "source_id": source_id, "text": literal}}
    if correction.strip():
        fields["latest_user_correction"] = {"source": "user", "source_id": source_id, "text": correction}
    return fields, []


def build(record: dict) -> dict:
    missing = [k for k in REQUIRED_CONTEXT if not record.get(k)]
    wm = record.get("working_model")
    if not isinstance(wm, dict):
        missing.append("working_model")
    if missing:
        return {"pass": False, "detected": [f"TASK_CONTEXT_MISSING:{x}" for x in missing]}
    intent_fields, intent_errors = _user_intent(record)
    if intent_errors:
        return {"pass": False, "detected": intent_errors, "task_contract": None}

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
            "preserve": record.get(
                "preserve_change_scope",
                wm.get("protected_state", []),
            ),
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
            "artifact_kind": str(record.get("artifact_kind") or "").lower(),
            "result_preview_required": bool(
                record.get("result_preview_required", False)
                or record.get("mobile_runtime_required", False)
                or str(record.get("artifact_kind") or "").lower()
                in {"ui", "pwa", "image", "asset", "document", "pdf", "presentation", "spreadsheet"}
            ),
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
    if intent_fields:
        task.update(intent_fields)
    effect_policy = _effect_policy(record)
    if effect_policy is not None:
        task["effect_policy"] = effect_policy

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
