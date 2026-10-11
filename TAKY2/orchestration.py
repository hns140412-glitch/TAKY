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

CONTRACT_NAME = "TAKY_ROLE_BASED_COLLABORATIVE_EXECUTION"
CONTRACT_VERSION = 5
EXECUTION_MODEL = "ROLE_BASED_COLLABORATIVE_EXECUTION_STRUCTURE"
METAPHOR_MODEL = "SHEPHERDING_COOPERATIVE_EXECUTION_MODEL"
CANONICAL_SYSTEMWIDE_REF = "TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL@2026-10-06"
PURPOSE = "GUIDE_TO_RESULT"
CONTROL_ROLES = ["NAVIGATOR", "GUARDIAN", "DRIVER", "SCOUT"]
ECONOMY_POLICY = "SAVEY_AI_ECONOMY"
ECONOMY_CONTRACT = {
    "operating_mode": "CORRECTIVE_ROUTER_OPTIMIZER",
    "priority": "ACCEPTANCE_BEFORE_COST",
    "normal_flow": [
        "ALLOW",
        "CORRECT_AND_RUN",
        "SHRINK_AND_RUN",
        "REROUTE_AND_RUN",
        "VERIFY",
    ],
    "requirement_classes": [
        "CAPABILITY_REQUIRED",
        "QUALITY_REQUIRED",
        "OPTIONAL_CONVENIENCE",
    ],
    "resource_classes": {
        "REMOTE_LOCAL": "UNMETERED",
        "SUBSCRIPTION_MODELS": "SUBSCRIPTION_QUOTA",
        "PAID_API": "PAID_API",
    },
    "capability_examples": [
        "UI_IMAGE_GENERATION",
        "TTS_AUDIO_GENERATION",
    ],
    "dry_run_policy": {
        "mode": "AUTO_DERIVE_REDUNDANT_FIELDS",
        "derive": [
            "EXPECTED_CALLS",
            "OPERATIONS_DEFAULT",
            "BATCH_STRATEGY",
            "FALLBACK",
            "PAID_API_FROM_BILLING_CLASS",
        ],
        "explicit_conflict": "CORRECT_OR_REJECT",
        "packet_only_requires": [
            "PACKET_ONLY_BINDING",
            "PACKET_DIGEST",
        ],
    },
    "same_failure_repeat_forbidden": True,
    "user_decision_reserved_for": [
        "REAL_INCREMENTAL_PAID_SPEND",
        "PROTECTED_AUTHORITY_OR_SCOPE_CHANGE",
        "IRREVERSIBLE_ACTION",
        "EXPLICIT_USER_STOP",
    ],
}
ROLE_REGISTRY = {
    "orchestrator": "LEAD_ORCHESTRATOR",
    "implementer": "CODE_WRITER",
    "verifier": "VERIFIER",
    "independent_reviewer": "INDEPENDENT_REVIEWER",
    "final_authority": "FINAL_AUTHORITY",
}
DEFAULT_ACTOR_BINDINGS = {
    "orchestrator": "CHATGPT",
    "implementer": None,
    "verifier": "CODEX",
    "independent_reviewer": "CLAUDE",
    "final_authority": "USER",
}
WORKER_ROLE_REGISTRY = {
    "SCOPE_PLANNER": {
        "mission": "define bounded task scope, acceptance and non-scope",
        "evidence_required": "scope/acceptance trace",
    },
    "SCREEN_EXPERIENCE_DESIGNER": {
        "mission": "define user-facing screen/interaction behavior when applicable",
        "evidence_required": "experience artifact or interaction evidence",
    },
    "DATA_STATE_ARCHITECT": {
        "mission": "define data/state ownership, transitions and invariants",
        "evidence_required": "state/data contract evidence",
    },
    "BUILDER": {
        "mission": "implement the selected bounded change",
        "evidence_required": "diff/artifact/runtime evidence",
    },
    "TEST_ENGINEER": {
        "mission": "verify expected and negative behavior",
        "evidence_required": "targeted/regression test evidence",
    },
    "BUG_FIXER": {
        "mission": "repair a reproduced defect without scope inflation",
        "evidence_required": "reproduction plus fix regression",
    },
    "RELEASE_CHECKER": {
        "mission": "verify release readiness without granting deploy authority",
        "evidence_required": "release-readiness evidence",
    },
    "DOCUMENTATION_HANDOFF_WRITER": {
        "mission": "preserve current authority, state and resume handoff",
        "evidence_required": "read-back verified handoff artifact",
    },
}
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
IMPLEMENTER_ASSIGNMENT_POLICY = "TASK_FIT_NECESSITY"
GATE_VALIDATOR_OWNERSHIP = {
    "SAFE_TOOL": {
        "trigger": "BEFORE_TOOL_MEDIATED_EXECUTION",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "ONLY_IF_PROTECTED_AUTHORITY_OR_EXTERNAL_AUTH_REQUIRED",
        "receipt_custodian": "NAVIGATOR",
    },
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
        "human_authority_condition": "PROTECTED_SCOPE_OR_AUTHORITY_CHANGE",
        "receipt_custodian": "GUARDIAN",
    },
    "COST": {
        "trigger": "BEFORE_EXTERNAL_OR_METERED_CALL",
        "primary": "AUTO",
        "semantic": "AI_SEMANTIC",
        "human_authority_condition": "REAL_INCREMENTAL_SPEND_OR_FORBIDDEN_COST_PATH",
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
        return False, "TAKY role-based collaborative execution contract missing"
    if contract.get("name") != CONTRACT_NAME:
        return False, "orchestration contract name mismatch"
    if contract.get("version") != CONTRACT_VERSION:
        return False, "orchestration contract version mismatch"
    if contract.get("parent_system_ref") != SYSTEM_IDENTITY_REF:
        return False, "execution model must remain subordinate to TAKY"
    if contract.get("execution_model") != EXECUTION_MODEL:
        return False, "role-based collaborative execution structure mismatch"
    if contract.get("metaphor_model") != METAPHOR_MODEL:
        return False, "Shepherding metaphor compatibility binding missing"
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
        return False, "canonical control roles mismatch"
    if contract.get("economy_policy") != ECONOMY_POLICY:
        return False, "canonical SAVEY AI economy policy mismatch"
    if contract.get("economy_contract") != ECONOMY_CONTRACT:
        return False, "SAVEY corrective-router economy contract mismatch"

    role_registry = contract.get("role_registry")
    if role_registry != ROLE_REGISTRY:
        return False, "role_registry mismatch"
    actor_bindings = contract.get("default_actor_bindings")
    if actor_bindings != DEFAULT_ACTOR_BINDINGS:
        return False, "default_actor_bindings mismatch"
    if actor_bindings.get("implementer") is not None:
        return False, "implementer actor must remain task-fit, not fixed"
    for role_name, role_id in role_registry.items():
        actor_id = actor_bindings.get(role_name)
        if actor_id is not None and role_id == actor_id:
            return False, f"role must not equal actor binding: {role_name}"

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
    if implementation_status.get("role_actor_binding") != "IMPLEMENTED":
        return False, "role_registry/default_actor_bindings separation not implemented"
    for field in (
        "control_role_schema",
        "semantic_owner_binding",
        "worker_role_contracts",
        "shared_savey_economy_policy",
        "owner_map_registry",
        "startup_readback_receipt",
        "delivery_confirmation_split",
    ):
        if implementation_status.get(field) not in {"OPEN", "IMPLEMENTED"}:
            return False, f"invalid implementation status: {field}"

    loop = contract.get("guidance_loop")
    if loop != GUIDANCE_LOOP:
        return False, "guidance loop mismatch"

    call_policy = contract.get("call_policy")
    if not isinstance(call_policy, Mapping):
        return False, "call policy missing"
    if call_policy.get("claude_codex_remote") != "NECESSITY_CHECK_WITHIN_COST":
        return False, "Necessity must remain inside COST/Driver"

    gate_policy = contract.get("gate_policy")
    if not isinstance(gate_policy, Mapping):
        return False, "gate policy missing"
    if gate_policy.get("default") != "REDIRECT_BEFORE_ESCALATE":
        return False, "gate policy must redirect before escalation"
    if gate_policy.get("user_not_debugger") is not True:
        return False, "USER != DEBUGGER policy missing"
    if gate_policy.get("block_is_not_goal") is not True:
        return False, "gate must guide, not treat blocking as the goal"
    return True, "TAKY hierarchy and role-based collaborative execution contract verified"


def worker_role_profiles(action: Mapping[str, Any]) -> list[dict[str, Any]]:
    requested = action.get("worker_roles", [])
    if requested is None:
        requested = []
    if not isinstance(requested, list):
        raise ValueError("worker_roles must be a list")
    owner_ref = action.get("semantic_owner_ref")
    owner_scope = action.get("semantic_owner_scope")
    profiles = []
    seen = set()
    for role_id in requested:
        if not isinstance(role_id, str) or role_id not in WORKER_ROLE_REGISTRY:
            raise ValueError(f"unknown worker role: {role_id}")
        if role_id in seen:
            continue
        seen.add(role_id)
        base = WORKER_ROLE_REGISTRY[role_id]
        profiles.append({
            "role": role_id,
            "mission": base["mission"],
            "semantic_owner_ref": owner_ref,
            "semantic_owner_scope": owner_scope,
            "authority": "ROLE_SCOPED_NOT_SEMANTIC_OWNER",
            "evidence_required": base["evidence_required"],
        })
    return profiles


def role_assignment(
    action: Mapping[str, Any],
    *,
    verification_tier: str,
) -> dict[str, Any]:
    assigned = action.get("assigned_implementer")
    implementer_actor = assigned.strip() if isinstance(assigned, str) and assigned.strip() else None
    actor_bindings = dict(DEFAULT_ACTOR_BINDINGS)
    actor_bindings["implementer"] = implementer_actor
    worker_role_error = None
    try:
        selected_worker_roles = worker_role_profiles(action)
    except ValueError as exc:
        selected_worker_roles = []
        worker_role_error = str(exc)
    return {
        "system": SYSTEM_NAME,
        "system_identity_ref": SYSTEM_IDENTITY_REF,
        "execution_model": EXECUTION_MODEL,
        "metaphor_model": METAPHOR_MODEL,
        "canonical_systemwide_ref": CANONICAL_SYSTEMWIDE_REF,
        "available_control_roles": list(CONTROL_ROLES),
        "economy_policy": ECONOMY_POLICY,
        "role_registry": dict(ROLE_REGISTRY),
        "default_actor_bindings": dict(DEFAULT_ACTOR_BINDINGS),
        "actor_bindings": actor_bindings,
        "worker_roles": selected_worker_roles,
        "worker_role_error": worker_role_error,
        "orchestrator_role": ROLE_REGISTRY["orchestrator"],
        "orchestrator_actor": actor_bindings["orchestrator"],
        "implementer_role": ROLE_REGISTRY["implementer"],
        "implementer_actor": implementer_actor,
        "implementer_assignment_policy": IMPLEMENTER_ASSIGNMENT_POLICY,
        "verifier_role": ROLE_REGISTRY["verifier"],
        "verifier_actor": actor_bindings["verifier"],
        "independent_reviewer_role": ROLE_REGISTRY["independent_reviewer"],
        "independent_reviewer_actor": actor_bindings["independent_reviewer"],
        "final_authority_role": ROLE_REGISTRY["final_authority"],
        "final_authority_actor": actor_bindings["final_authority"],
        # Legacy short keys are actor projections only.
        # Canonical role identity is exposed exclusively through *_role / role_registry.
        "orchestrator": actor_bindings["orchestrator"],
        "implementer": implementer_actor,
        "verifier": actor_bindings["verifier"],
        "independent_reviewer": actor_bindings["independent_reviewer"],
        "final_authority": actor_bindings["final_authority"],
        "verification_tier": verification_tier,
        "independent_review_policy": (
            "REQUIRED_BY_TIER_OR_NECESSITY"
            if verification_tier == "STRONG"
            else "ON_NECESSITY"
        ),
        "external_ai_calls": "NECESSITY_CHECK_WITHIN_COST",
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
            "owner": DEFAULT_ACTOR_BINDINGS["orchestrator"],
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
            "owner": DEFAULT_ACTOR_BINDINGS["orchestrator"],
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
        next_action = (
            "classify failure and choose a materially different permitted route internally; "
            "do not involve USER unless real authority, spend, or irreversible scope changes"
        )
    elif gate == "COST":
        next_action = (
            "preserve acceptance quality, then correct/minimize and run: reuse, shrink context, "
            "batch, lower model/effort, or reroute only when sufficient; never suppress "
            "capability-required work merely to save cost"
        )
    elif gate == "DONE":
        next_action = "return to missing evidence/verification/rework before completion claim"
    elif gate == "KEY":
        next_action = "restore trusted Key/registered action without changing USER intent"
    else:
        next_action = "correct the failed precondition and rerun from the nearest safe point"

    return {
        "mode": "REDIRECT",
        "owner": DEFAULT_ACTOR_BINDINGS["orchestrator"],
        "system": SYSTEM_NAME,
        "system_identity_ref": SYSTEM_IDENTITY_REF,
        "execution_model": EXECUTION_MODEL,
        "principle": PURPOSE,
        "terminal": False,
        "detected": {"gate": gate, "state": state, "reason": reason},
        "next_action": next_action,
        "user_role": "FINAL_AUTHORITY_NOT_DEBUGGER",
    }
