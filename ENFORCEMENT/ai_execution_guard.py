#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

FAIL = {
    "ADOPTION": "AI_ADOPTION_GATE_MISSING",
    "SUCCESS": "AI_OBSERVABLE_SUCCESS_EVIDENCE_MISSING",
    "COST": "AI_COST_GUARD_MISSING",
    "REVIEW": "AI_REVIEW_PASS_UNJUSTIFIED",
    "COMPUTER": "AI_COMPUTER_USE_GUARD_MISSING",
}

def _nonempty(v: object) -> bool:
    return isinstance(v, str) and bool(v.strip())

def _refs(v: object) -> bool:
    return isinstance(v, list) and any(isinstance(x, str) and x.strip() for x in v)

def _pos_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0

def _number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0

def validate_ai_execution(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    # Learning: NECESSITY-BEFORE-ADOPTION + CAPABILITY-GAP-BEFORE-TOOL +
    # SECURITY-BEFORE-CREDENTIAL + SUPPLY-CHAIN-IDENTITY-CHECK +
    # CONNECTOR-PERMISSION-BOUNDARY + SENSITIVE-AGENT-ISOLATION.
    if record.get("ai_tool_or_connector_adoption_planned") is True:
        a = record.get("ai_adoption_assessment")
        if not isinstance(a, dict):
            failures.append(FAIL["ADOPTION"])
        else:
            required_true = [
                "overlap_checked",
                "cost_checked",
                "security_checked",
                "upstream_identity_verified",
            ]
            if not _nonempty(a.get("capability_gap")):
                failures.append(FAIL["ADOPTION"])
            if any(a.get(k) is not True for k in required_true):
                failures.append(FAIL["ADOPTION"])
            if a.get("credentials_or_private_access_involved") is True:
                if (
                    a.get("credential_scope_defined") is not True
                    or a.get("permission_boundary_defined") is not True
                    or a.get("isolated_test_planned") is not True
                ):
                    failures.append(FAIL["ADOPTION"])

    # Learning: OBSERVABLE-SUCCESS-CRITERIA + SELF-REPORT-NOT-RUNTIME-PROOF +
    # DEVICE-OBSERVATION-BEFORE-CLOSE.
    if record.get("ai_success_claimed") is True:
        if not _refs(record.get("observable_success_evidence_refs")):
            failures.append(FAIL["SUCCESS"])
        if (
            record.get("device_or_ui_observation_required") is True
            and not _refs(record.get("device_or_ui_observation_refs"))
        ):
            failures.append(FAIL["SUCCESS"])

    # Learning: COST-GUARD-AS-CODE. This complements, rather than replaces,
    # the existing external call budget gate.
    if record.get("ai_autonomous_cost_exposure") is True:
        c = record.get("ai_cost_guard")
        if not isinstance(c, dict):
            failures.append(FAIL["COST"])
        else:
            if not _number(c.get("cost_ceiling")):
                failures.append(FAIL["COST"])
            if not _pos_int(c.get("iteration_limit")):
                failures.append(FAIL["COST"])
            if not _nonempty(c.get("stop_condition")):
                failures.append(FAIL["COST"])
            if c.get("approval_required_before_exceeding") is not True:
                failures.append(FAIL["COST"])

    # Learning: REVIEW-BUDGET-DOES-NOT-FORCE-PASS.
    if record.get("ai_review_loop") is True:
        unresolved = record.get("review_unresolved_material_issues") is True
        exhausted = record.get("review_round_limit_reached") is True
        decision = str(record.get("review_decision") or "").strip().upper()
        if unresolved and exhausted and decision in {"PASS", "APPROVE", "COMPLETE"}:
            failures.append(FAIL["REVIEW"])

    # Learning: SAFE-COMPUTER-USE-SEQUENCE + METADATA-FIRST-FILE-DIAGNOSIS.
    if record.get("ai_computer_use_action") is True:
        c = record.get("ai_computer_use_guard")
        if not isinstance(c, dict):
            failures.append(FAIL["COMPUTER"])
        else:
            required_true = [
                "read_only_diagnosis_completed",
                "change_plan_defined",
                "bounded_execution_defined",
                "observable_verification_defined",
                "rollback_or_recovery_defined",
            ]
            if any(c.get(k) is not True for k in required_true):
                failures.append(FAIL["COMPUTER"])
            if c.get("content_inspection_needed") is not True and c.get("metadata_first_used") is not True:
                failures.append(FAIL["COMPUTER"])
            if (
                c.get("sensitive_or_destructive_action") is True
                and c.get("explicit_approval_bound") is not True
            ):
                failures.append(FAIL["COMPUTER"])

    return list(dict.fromkeys(failures))
