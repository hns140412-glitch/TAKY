from __future__ import annotations

from typing import Any, Mapping


SYSTEM_NAME = "TAKY"
SYSTEM_IDENTITY_NAME = "TAKY_SYSTEM_IDENTITY"
SYSTEM_IDENTITY_VERSION = 1
SYSTEM_IDENTITY_REF = f"{SYSTEM_IDENTITY_NAME}@{SYSTEM_IDENTITY_VERSION}"
SYSTEM_SLOGANS = [
    "Think Again, Keep Your Key.",
    "Think Again, You're The Key.",
]

CONTRACT_NAME = "TAKY_SHEPHERDING_COOPERATIVE_EXECUTION"
CONTRACT_VERSION = 3
EXECUTION_MODEL = "SHEPHERDING_COOPERATIVE_EXECUTION_MODEL"
CANONICAL_SYSTEMWIDE_REF = "TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL@2026-10-06"
PURPOSE = "GUIDE_TO_RESULT"
CONTROL_ROLES = ["NAVIGATOR", "GUARDIAN", "DRIVER", "SCOUT"]
ECONOMY_POLICY = "SAVEY_AI_ECONOMY"
GUIDANCE_LOOP = [
    "OBSERVE",
    "CLASSIFY",
    "ASSIGN",
    "EXECUTE",
    "CROSS_CHECK",
    "REDIRECT",
    "VERIFY",
    "DELIVER",
]
REQUIRED_ROLES = {
    "orchestrator": "CHATGPT_LEAD_ORCHESTRATOR",
    "implementer": "CODE_WRITER",
    "verifier": "CODEX",
    "independent_reviewer": "CLAUDE",
    "final_authority": "USER",
}
IMPLEMENTER_ASSIGNMENT_POLICY = "TASK_FIT_NECESSITY"
GATE_VALIDATOR_OWNERSHIP = {
    "KEY": {
        "trigger": "PRE_EXECUTION_OR_KEY_CHANGE",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "KEY_AMEND_OR_CANONICAL_AUTHORITY_CHANGE",
        "receipt_custodian": "GUARDIAN",
    },
    "CONTEXT": {
        "trigger": "START_OR_CONTEXT_DELTA_CHANGE",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "CONTEXT_CONFLICT_CHANGES_KEY_OR_AUTHORITY",
        "receipt_custodian": "GUARDIAN",
    },
    "ROUTE": {
        "trigger": "FAILURE_OR_REROUTE",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "ROUTE_BUDGET_EXTENSION_OR_PROTECTED_SCOPE_CHANGE",
        "receipt_custodian": "GUARDIAN",
    },
    "COST": {
        "trigger": "BEFORE_EXTERNAL_OR_METERED_CALL",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "EXPLICITLY_GATED_HIGH_COST_OR_FORBIDDEN_COST_PATH",
        "receipt_custodian": "DRIVER",
    },
    "DONE": {
        "trigger": "BEFORE_PASS_DONE_OR_USER_CONFIRMED",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "USER_RESERVED_CONFIRMATION_OR_AUTHORITY_DECISION",
        "receipt_custodian": "GUARDIAN",
    },
}


def validator_profile(gate: str) -> dict[str, str]:
    key = str(gate or "").upper()
    profile = GATE_VALIDATOR_OWNERSHIP.get(key)
    if profile is None:
        raise ValueError(f"unknown gate validator profile: {gate}")
    return dict(profile)


def _trusted_user_statement(trusted: Mapping[str, Any], ref: Any) -> bool:
    if not isinstance(ref, str) or not ref:
        return False
    src = trusted.get("source_registry", {}).get(ref)
    return (
        isinstance(src, Mapping)
        and src.get("actor") == "USER"
        and src.get("kind") == "statement"
        and src.get("status") != "SUPERSEDED"
    )


def validate_orchestration_contract(
    trusted: Mapping[str, Any],
) -> tuple[bool, str]:
    identity = trusted.get("system_identity")
    if not isinstance(identity, Mapping):
        return False, "TAKY top-level system identity missing"
    if identity.get("name") != SYSTEM_NAME:
        return False, "top-level system must remain TAKY"
    if identity.get("identity_name") != SYSTEM_IDENTITY_NAME:
        return False, "TAKY system identity name mismatch"
    if identity.get("version") != SYSTEM_IDENTITY_VERSION:
        return False, "TAKY system identity version mismatch"
    if identity.get("slogans") != SYSTEM_SLOGANS:
        return False, "TAKY top-level slogans mismatch"
    if identity.get("key_owner") != "USER":
        return False, "USER must remain TAKY Key owner"
    if identity.get("user_not_debugger") is not True:
        return False, "USER != DEBUGGER top-level policy missing"
    if not _trusted_user_statement(trusted, identity.get("source_ref")):
        return False, "TAKY system identity lacks trusted USER provenance"

    contract = trusted.get("orchestration_contract")
    if not isinstance(contract, Mapping):
        return False, "TAKY shepherding cooperative execution contract missing"
    if contract.get("name") != CONTRACT_NAME:
        return False, "orchestration contract name mismatch"
    if contract.get("version") != CONTRACT_VERSION:
        return False, "orchestration contract version mismatch"
    if contract.get("parent_system_ref") != SYSTEM_IDENTITY_REF:
        return False, "execution model must remain subordinate to TAKY"
    if contract.get("execution_model") != EXECUTION_MODEL:
        return False, "shepherding cooperative execution model mismatch"
    if contract.get("canonical_systemwide_ref") != CANONICAL_SYSTEMWIDE_REF:
        return False, "systemwide canonical reconciliation reference mismatch"
    if not _trusted_user_statement(trusted, contract.get("canonical_source_ref")):
        return False, "systemwide canonical reconciliation lacks trusted USER provenance"
    if "slogan_parent" in contract:
        return False, "parent slogans belong to TAKY system identity, not execution model"
    if contract.get("purpose") != PURPOSE:
        return False, "orchestration purpose must be GUIDE_TO_RESULT"
    if not _trusted_user_statement(trusted, contract.get("source_ref")):
        return False, "execution model lacks trusted USER provenance"

    control_roles = contract.get("control_roles")
    if control_roles != CONTROL_ROLES:
        return False, "canonical shepherding control roles mismatch"
    if contract.get("economy_policy") != ECONOMY_POLICY:
        return False, "canonical SAVEY AI economy policy mismatch"

    roles = contract.get("roles")
    if not isinstance(roles, Mapping):
        return False, "orchestration roles missing"
    for role, expected in REQUIRED_ROLES.items():
        if roles.get(role) != expected:
            return False, f"orchestration role mismatch: {role}"

    role_policy = contract.get("role_policy")
    if not isinstance(role_policy, Mapping):
        return False, "orchestration role policy missing"
    if role_policy.get("implementer_assignment") != IMPLEMENTER_ASSIGNMENT_POLICY:
        return False, "implementer must be selected by task fit and necessity"
    if role_policy.get("role_labels_do_not_authorize_calls") is not True:
        return False, "role labels must not authorize calls"
    if role_policy.get("role_not_agent") is not True:
        return False, "ROLE != AGENT policy missing"
    if role_policy.get("routing_does_not_transfer_semantic_ownership") is not True:
        return False, "routing must not transfer semantic ownership"
    if role_policy.get("semantic_owner_remains_domain_owner") is not True:
        return False, "semantic owner boundary missing"

    implementation_status = contract.get("implementation_status")
    if not isinstance(implementation_status, Mapping):
        return False, "canonical implementation-status split missing"
    for field in (
        "control_role_schema",
        "semantic_owner_binding",
        "worker_role_contracts",
        "shared_savey_economy_policy",
    ):
        if implementation_status.get(field) not in {"OPEN", "IMPLEMENTED"}:
            return False, f"invalid implementation status: {field}"

    loop = contract.get("guidance_loop")
    if loop != GUIDANCE_LOOP:
        return False, "guidance loop mismatch"

    gate_policy = contract.get("gate_policy")
    if not isinstance(gate_policy, Mapping):
        return False, "gate policy missing"
    if gate_policy.get("default") != "REDIRECT_BEFORE_ESCALATE":
        return False, "gate policy must redirect before escalation"
    if gate_policy.get("user_not_debugger") is not True:
        return False, "USER != DEBUGGER policy missing"
    if gate_policy.get("block_is_not_goal") is not True:
        return False, "gate must guide, not treat blocking as the goal"
    return True, "TAKY hierarchy and shepherding cooperative execution contract verified"


def role_assignment(
    action: Mapping[str, Any],
    *,
    verification_tier: str,
) -> dict[str, Any]:
    assigned = action.get("assigned_implementer")
    implementer_actor = assigned.strip() if isinstance(assigned, str) and assigned.strip() else None
    return {
        "system": SYSTEM_NAME,
        "system_identity_ref": SYSTEM_IDENTITY_REF,
        "execution_model": EXECUTION_MODEL,
        "canonical_systemwide_ref": CANONICAL_SYSTEMWIDE_REF,
        "available_control_roles": list(CONTROL_ROLES),
        "economy_policy": ECONOMY_POLICY,
        "orchestrator": "CHATGPT_LEAD_ORCHESTRATOR",
        "implementer": "CODE_WRITER",
        "implementer_role": "CODE_WRITER",
        "implementer_actor": implementer_actor,
        "implementer_assignment_policy": IMPLEMENTER_ASSIGNMENT_POLICY,
        "verifier": "CODEX",
        "independent_reviewer": "CLAUDE",
        "final_authority": "USER",
        "verification_tier": verification_tier,
        "independent_review_policy": (
            "REQUIRED_BY_TIER_OR_NECESSITY"
            if verification_tier == "STRONG"
            else "ON_NECESSITY"
        ),
        "external_ai_calls": "NECESSITY_GATE_ONLY",
        "action_kind": action.get("kind"),
    }


def guidance_for_failure(
    gate: str,
    state: str,
    reason: str,
) -> dict[str, Any]:
    gate = str(gate or "").upper()
    state = str(state or "").upper()

    if state == "USER_DECISION_REQUIRED":
        return {
            "mode": "USER_DECISION_REQUIRED",
            "owner": "CHATGPT_LEAD_ORCHESTRATOR",
            "system": SYSTEM_NAME,
            "system_identity_ref": SYSTEM_IDENTITY_REF,
            "execution_model": EXECUTION_MODEL,
            "principle": PURPOSE,
            "terminal": False,
            "next_action": (
                "exhaust safe alternative routes, package cause/options/recommendation, "
                "then ask USER for the single authority decision only"
            ),
            "user_role": "FINAL_AUTHORITY_NOT_DEBUGGER",
        }

    if state == "ABANDONED":
        return {
            "mode": "BLOCKED",
            "owner": "CHATGPT_LEAD_ORCHESTRATOR",
            "system": SYSTEM_NAME,
            "system_identity_ref": SYSTEM_IDENTITY_REF,
            "execution_model": EXECUTION_MODEL,
            "principle": PURPOSE,
            "terminal": True,
            "detected": {"gate": gate, "state": state, "reason": reason},
            "next_action": "respect explicit USER stop; do not continue this receipt",
            "user_role": "FINAL_AUTHORITY_NOT_DEBUGGER",
        }

    if state == "READ_ONLY":
        next_action = (
            "continue safe read-only work, rebuild or rebind trusted authority, "
            "and retry mutation without asking USER to debug"
        )
    elif state == "KEY_NOT_LOCKED":
        next_action = (
            "reconstruct the Key from trusted USER intent; ask USER only if an authority "
            "ambiguity remains after available evidence is exhausted"
        )
    elif state == "USER_DEBUGGER_VIOLATION":
        next_action = "resume the required AI/tool work internally and keep debugging away from USER"
    elif gate == "CONTEXT":
        next_action = "rebuild or narrow to verified snapshot/delta, then retry"
    elif gate == "ROUTE":
        next_action = "classify failure and choose a materially different permitted route"
    elif gate == "COST":
        next_action = "skip unnecessary call or reroute to the cheapest sufficient local path"
    elif gate == "DONE":
        next_action = "return to missing evidence/verification/rework before completion claim"
    elif gate == "KEY":
        next_action = "restore trusted Key/registered action without changing USER intent"
    else:
        next_action = "correct the failed precondition and rerun from the nearest safe point"

    return {
        "mode": "REDIRECT",
        "owner": "CHATGPT_LEAD_ORCHESTRATOR",
        "system": SYSTEM_NAME,
        "system_identity_ref": SYSTEM_IDENTITY_REF,
        "execution_model": EXECUTION_MODEL,
        "principle": PURPOSE,
        "terminal": False,
        "detected": {"gate": gate, "state": state, "reason": reason},
        "next_action": next_action,
        "user_role": "FINAL_AUTHORITY_NOT_DEBUGGER",
    }
