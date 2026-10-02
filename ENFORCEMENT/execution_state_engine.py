#!/usr/bin/env python3
"""TAKY execution state engine.

Owns task lifecycle transitions and rework routing for controlled repository runs.
It is intentionally small and deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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


def _canonical_bytes(value: dict) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def promotion_readiness(record: dict) -> tuple[dict | None, list[str]]:
    if record.get("canonical_promotion") is not True:
        return None, []

    failures: list[str] = []
    source_boundary_ref = str(record.get("source_boundary_ref", "")).strip()
    decision_lineage_ref = str(record.get("decision_lineage_ref", "")).strip()
    promotion_target_ref = str(record.get("promotion_target_ref", "")).strip()
    prerequisites = record.get("promotion_prerequisites")

    if not source_boundary_ref:
        failures.append("PROMOTION_SOURCE_BOUNDARY_MISSING")
    if not decision_lineage_ref:
        failures.append("PROMOTION_DECISION_LINEAGE_MISSING")
    if not promotion_target_ref:
        failures.append("PROMOTION_TARGET_REF_MISSING")
    if not isinstance(prerequisites, list) or not prerequisites:
        failures.append("PROMOTION_PREREQUISITES_MISSING")
        normalized_prerequisites = []
    else:
        normalized_prerequisites = []
        for item in prerequisites:
            if not isinstance(item, dict):
                failures.append("PROMOTION_PREREQUISITE_INVALID")
                continue
            pid = str(item.get("id", "")).strip()
            status = str(item.get("status", "")).strip().upper()
            evidence_ref = str(item.get("evidence_ref", "")).strip()
            if not pid:
                failures.append("PROMOTION_PREREQUISITE_ID_MISSING")
            if status != "PASS":
                failures.append(f"PROMOTION_PREREQUISITE_NOT_PASS:{pid or 'UNKNOWN'}")
            if not evidence_ref:
                failures.append(f"PROMOTION_PREREQUISITE_EVIDENCE_MISSING:{pid or 'UNKNOWN'}")
            normalized_prerequisites.append({
                "id": pid,
                "status": status,
                "evidence_ref": evidence_ref,
            })

    return {
        "source_boundary_ref": source_boundary_ref,
        "decision_lineage_ref": decision_lineage_ref,
        "promotion_target_ref": promotion_target_ref,
        "promotion_prerequisites": normalized_prerequisites,
    }, failures


def approval_context(record: dict, current: str, requested: str) -> tuple[dict, list[str]]:
    failures: list[str] = []
    task_id = str(record.get("task_id", "")).strip()
    target_ref = str(record.get("transition_target_ref", "")).strip()

    if not task_id:
        failures.append("APPROVAL_CONTEXT_TASK_ID_MISSING")
    if not target_ref:
        failures.append("APPROVAL_CONTEXT_TARGET_REF_MISSING")

    context = {
        "task_id": task_id,
        "from_state": current,
        "to_state": requested,
        "target_ref": target_ref,
    }
    promotion, promotion_failures = promotion_readiness(record)
    failures.extend(promotion_failures)
    if promotion is not None:
        context["canonical_promotion"] = promotion
    context["approval_context_hash"] = (
        "sha256:" + hashlib.sha256(_canonical_bytes(context)).hexdigest()
    )
    return context, failures


def validate_transition_approval(
    record: dict,
    current: str,
    requested: str,
) -> tuple[dict | None, dict, list[str]]:
    context, failures = approval_context(record, current, requested)
    evidence = record.get("human_approval_evidence")
    if not evidence:
        return None, context, failures
    if not isinstance(evidence, dict):
        failures.append("HUMAN_APPROVAL_EVIDENCE_INVALID")
        return None, context, failures

    approval_id = evidence.get("approval_id")
    approver_ref = evidence.get("approver_ref")
    decision = str(evidence.get("decision", "")).strip().upper()

    if not isinstance(approval_id, str) or not approval_id.strip():
        failures.append("APPROVAL_ID_MISSING")
    if not isinstance(approver_ref, str) or not approver_ref.strip():
        failures.append("APPROVER_REF_MISSING")
    if decision != "APPROVE":
        failures.append("APPROVAL_DECISION_NOT_APPROVED")

    if evidence.get("task_id") != context["task_id"]:
        failures.append("APPROVAL_EVIDENCE_TASK_ID_MISMATCH")
    if str(evidence.get("from_state", "")).strip().upper() != current:
        failures.append("APPROVAL_EVIDENCE_FROM_STATE_MISMATCH")
    if str(evidence.get("to_state", "")).strip().upper() != requested:
        failures.append("APPROVAL_EVIDENCE_TO_STATE_MISMATCH")
    if evidence.get("target_ref") != context["target_ref"]:
        failures.append("APPROVAL_EVIDENCE_TARGET_REF_MISMATCH")
    if evidence.get("approval_context_hash") != context["approval_context_hash"]:
        failures.append("APPROVAL_EVIDENCE_CONTEXT_HASH_MISMATCH")

    normalized = {
        "approval_id": approval_id.strip() if isinstance(approval_id, str) else None,
        "approver_ref": approver_ref.strip() if isinstance(approver_ref, str) else None,
        "decision": decision,
        **context,
    }
    return normalized, context, failures


def transition(record: dict) -> dict:
    current = str(record.get("current_state", "")).strip().upper()
    requested = str(record.get("requested_state", "")).strip().upper()
    if not current or not requested:
        return {"pass": False, "detected": ["STATE_TRANSITION_INCOMPLETE"]}

    if requested not in ALLOWED_TRANSITIONS.get(current, set()):
        return {
            "pass": False,
            "detected": [f"FORBIDDEN_STATE_TRANSITION:{current}->{requested}"],
            "current_state": current,
        }

    if requested == "REWORK":
        defects = record.get("defects")
        if not isinstance(defects, list) or not defects:
            return {
                "pass": False,
                "detected": ["REWORK_WITHOUT_DEFECT_EVIDENCE"],
                "current_state": current,
            }

    if record.get("canonical_promotion") is True and requested in {"HUMAN_APPROVAL", "MERGED"}:
        promotion, promotion_failures = promotion_readiness(record)
        if promotion_failures:
            return {
                "pass": False,
                "detected": promotion_failures,
                "current_state": current,
                "promotion_readiness": promotion,
            }

    approval_verified = None
    # MERGED/DEPLOYED are always human-approved lifecycle transitions.
    # Per-call booleans may not weaken this governance boundary.
    if requested == "MERGED" and record.get("merge_approval_required") is False:
        return {
            "pass": False,
            "detected": ["MERGE_APPROVAL_BYPASS_FORBIDDEN"],
            "current_state": current,
        }
    if requested == "DEPLOYED" and record.get("production_approval_required") is False:
        return {
            "pass": False,
            "detected": ["DEPLOY_APPROVAL_BYPASS_FORBIDDEN"],
            "current_state": current,
        }
    approval_required = requested in {"MERGED", "DEPLOYED"}
    if approval_required:
        missing_code = (
            "HUMAN_APPROVAL_MISSING:merge"
            if requested == "MERGED"
            else "HUMAN_APPROVAL_MISSING:production_deploy"
        )
        if not record.get("human_approval_evidence"):
            context, context_failures = approval_context(record, current, requested)
            return {
                "pass": False,
                "detected": [missing_code, *context_failures],
                "current_state": current,
                "required_approval_context": context,
            }

        approval_verified, context, approval_failures = validate_transition_approval(
            record,
            current,
            requested,
        )
        if approval_failures:
            return {
                "pass": False,
                "detected": approval_failures,
                "current_state": current,
                "required_approval_context": context,
            }

    return {
        "pass": True,
        "detected": [],
        "previous_state": current,
        "current_state": requested,
        "approval_verified": approval_verified,
        "rework": {
            "required": requested == "REWORK",
            "defects": record.get("defects", []) if requested == "REWORK" else [],
            "acceptance_delta": record.get("acceptance_delta", []) if requested == "REWORK" else [],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    args = ap.parse_args()
    data = json.loads(args.record.read_text(encoding="utf-8"))
    result = transition(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
