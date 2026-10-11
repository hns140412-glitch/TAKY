import json
import pytest

from TAKY2.bridges import BridgeViolation
from TAKY2.verify_from_review_receipt import verify_bound_review
from TAKY2.enforcement import done_gate


def runtime_fixture():
    verdict = {
        "target_receipt_id": "target",
        "target_result_digest": "result-target",
        "authority_digest": "auth1",
        "verifier_role": "VERIFIER",
        "verifier_actor": "CODEX",
        "passed": True,
        "evidence_ref": "verify:target:codex",
        "evidence_type": "runtime_test",
        "claim_supported": "bounded target execution verification",
        "key_match": True,
        "required_verifications": ["technical", "intent"],
        "passed_verifications": ["technical", "intent"],
        "critical_gaps": [],
    }
    return {
        "preflight_receipts": {
            "target": {
                "allowed": True,
                "action_id": "read:q002",
                "execution_key": "exec-target",
                "execution_scope": "q002-read",
                "authority_digest": "auth1",
                "verification_tier": "STANDARD",
                "semantic_owner_ref": "TAKY2_ORCHESTRATION_KERNEL",
                "semantic_owner_scope": "TAKY2/Q002",
                "plan_digest": "plan1",
                "action_digest": "action1",
                "call_digest": "call1",
                "orchestration": {
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "independent_reviewer_role": "INDEPENDENT_REVIEWER",
                    "independent_reviewer_actor": "CLAUDE",
                },
            },
            "review": {
                "allowed": True,
                "action_id": "review:external-model",
                "execution_key": "exec-review",
            },
        },
        "execution_calls": {
            "target": {
                "executor_id": "TAKY_LOCAL_TEST",
                "result_digest": "result-target",
                "status": "RETURNED",
                "result": {"returncode": 0, "stdout": "ok", "stderr": ""},
            },
            "review": {
                "executor_id": "TAKY_MODEL_REVIEW_CODEX",
                "provider": "openai",
                "model": "codex",
                "status": "RETURNED",
                "result": {
                    "returncode": 0,
                    "stdout": json.dumps(verdict),
                    "stderr": "",
                },
            },
        },
        "active_attempts": {
            "exec-target": {
                "receipt_id": "target",
                "status": "PENDING",
                "attempt": {"target": "Q002", "method_or_tool": "git"},
                "execution_scope": "q002-read",
            },
            "exec-review": {
                "receipt_id": "review",
                "status": "PENDING",
                "attempt": {"target": "repo", "method_or_tool": "codex-app-devnull"},
                "execution_scope": "external-model-review",
            },
        },
        "execution_outcomes": {},
        "evidence_registry": {},
        "completion_registry": {},
        "independent_review_registry": {},
        "route_ledgers": {},
    }


def test_bound_codex_review_creates_success_evidence_and_completion():
    updated = verify_bound_review(runtime_fixture(), "target", "review")
    assert updated["execution_outcomes"]["target"] == "SUCCESS"
    assert "verify:target:codex" in updated["evidence_registry"]
    assert "target" in updated["completion_registry"]
    assert updated["preflight_receipts"]["review"]["consumed"] is True
    assert updated["preflight_receipts"]["review"]["consumed_as_verification_evidence_for"] == "target"
    assert "exec-review" not in updated["active_attempts"]


def test_bound_review_rejects_target_result_mismatch():
    runtime = runtime_fixture()
    payload = json.loads(runtime["execution_calls"]["review"]["result"]["stdout"])
    payload["target_result_digest"] = "wrong"
    runtime["execution_calls"]["review"]["result"]["stdout"] = json.dumps(payload)
    with pytest.raises(BridgeViolation, match="TARGET_RESULT_DIGEST_MISMATCH"):
        verify_bound_review(runtime, "target", "review")


def test_verified_receipt_reaches_delivered_unconfirmed_until_user_confirmation():
    updated = verify_bound_review(runtime_fixture(), "target", "review")
    trusted = dict(updated)
    trusted["_authority_digest"] = "auth1"
    completion = updated["completion_registry"]["target"]
    result = done_gate(
        trusted,
        {
            "preflight_receipt": "target",
            "evidence_refs": completion["evidence_refs"],
        },
    )
    assert result.allowed is False
    assert result.state == "DELIVERED_UNCONFIRMED"
    assert "confirmation" in result.reason.lower()
