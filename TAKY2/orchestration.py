from __future__ import annotations

from typing import Any, Mapping


CONTRACT_NAME = "BORDER_COLLIE_ORCHESTRATION"
PURPOSE = "GUIDE_TO_RESULT"
GUIDANCE_LOOP = ["DETECT", "CLASSIFY", "REDIRECT", "GUIDE", "VERIFY", "DELIVER"]
REQUIRED_ROLES = {
    "orchestrator": "CHATGPT_TAKY_BORDER_COLLIE",
    "implementer": "CODE_WRITER",
    "verifier": "CODEX",
    "independent_reviewer": "CLAUDE",
    "final_authority": "USER",
}


def validate_orchestration_contract(
    trusted: Mapping[str, Any],
) -> tuple[bool, str]:
    contract = trusted.get("orchestration_contract")
    if not isinstance(contract, Mapping):
        return False, "Border Collie orchestration contract missing"
    if contract.get("name") != CONTRACT_NAME:
        return False, "orchestration contract name mismatch"
    if contract.get("purpose") != PURPOSE:
        return False, "orchestration purpose must be GUIDE_TO_RESULT"

    roles = contract.get("roles")
    if not isinstance(roles, Mapping):
        return False, "orchestration roles missing"
    for role, expected in REQUIRED_ROLES.items():
        if roles.get(role) != expected:
            return False, f"orchestration role mismatch: {role}"

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
    return True, "Border Collie orchestration contract verified"


def role_assignment(
    action: Mapping[str, Any],
    *,
    verification_tier: str,
) -> dict[str, Any]:
    return {
        "orchestrator": "CHATGPT_TAKY_BORDER_COLLIE",
        "implementer": "CODE_WRITER",
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
            "owner": "CHATGPT_TAKY_BORDER_COLLIE",
            "principle": PURPOSE,
            "next_action": (
                "exhaust safe alternative routes, package cause/options/recommendation, "
                "then ask USER for the single authority decision only"
            ),
            "user_role": "FINAL_AUTHORITY_NOT_DEBUGGER",
        }

    if gate == "CONTEXT":
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

    hard_block_states = {
        "READ_ONLY",
        "ABANDONED",
        "KEY_NOT_LOCKED",
    }
    mode = "BLOCKED" if state in hard_block_states else "REDIRECT"
    return {
        "mode": mode,
        "owner": "CHATGPT_TAKY_BORDER_COLLIE",
        "principle": PURPOSE,
        "detected": {"gate": gate, "state": state, "reason": reason},
        "next_action": next_action,
        "user_role": "FINAL_AUTHORITY_NOT_DEBUGGER",
    }
