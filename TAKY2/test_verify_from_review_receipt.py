import json
import pytest

from TAKY2.bridges import BridgeViolation
from TAKY2.verify_from_review_receipt import verify_bound_review
from TAKY2.enforcement import done_gate, stable_hash


def runtime_fixture():
    target_result = {"returncode": 0, "stdout": "ok", "stderr": ""}
    target_digest = stable_hash(target_result)
    verdict = {
        "target_receipt_id": "target",
        "target_result_digest": target_digest,
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
        "authority_digest": "auth1",
        "preflight_receipts": {
            "target": {
                "allowed": True,
                "consumed": False,
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
                "call_allowed": True,
                "consumed": False,
                "action_id": "verify:codex-packet",
                "authority_digest": "auth1",
                "call_digest": "review-preflight-bound",
                "execution_key": "exec-review",
            },
        },
        "execution_calls": {
            "target": {
                "executor_id": "TAKY_LOCAL_TEST",
                "actual_calls": 1,
                "result_digest": target_digest,
                "status": "RETURNED",
                "result": target_result,
            },
            "review": {
                "executor_id": "TAKY_MODEL_REVIEW_CODEX",
                "provider": "openai",
                "model": "codex",
                "status": "RETURNED",
                "actual_calls": 1,
                "result": {
                    "returncode": 0,
                    "stdout": json.dumps(verdict),
                    "stderr": "",
                },
                "result_digest": stable_hash({
                    "returncode": 0, "stdout": json.dumps(verdict), "stderr": ""
                }),
                "target_review_evidence": {
                    "schema": "TAKY_TARGET_REVIEW_RECEIPT_V1",
                    "target_receipt_id": "target",
                    "target_result_digest": target_digest,
                    "packet_digest": "a" * 20,
                    "review_call_digest": "review-preflight-bound",
                    "review_result_digest": stable_hash({
                        "returncode": 0, "stdout": json.dumps(verdict),
                        "stderr": "",
                    }),
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
    runtime["execution_calls"]["review"]["result_digest"] = stable_hash(
        runtime["execution_calls"]["review"]["result"]
    )
    runtime["execution_calls"]["review"]["target_review_evidence"][
        "review_result_digest"] = runtime["execution_calls"]["review"]["result_digest"]
    with pytest.raises(BridgeViolation, match="TARGET_RESULT_DIGEST_MISMATCH"):
        verify_bound_review(runtime, "target", "review")



@pytest.mark.parametrize(("target", "expected"), [
    ("review.call_allowed", "REVIEW_PREFLIGHT_NOT_ACTIVE_AUTHORIZED"),
    ("review.consumed", "REVIEW_PREFLIGHT_NOT_ACTIVE_AUTHORIZED"),
    ("review.authority_digest", "REVIEW_TARGET_AUTHORITY_NOT_BOUND"),
    ("review.call_digest", "REVIEW_SIGNED_CALL_DIGEST_MISSING"),
    ("target_result_tampered", "TARGET_EXECUTION_DIGEST_NOT_VERIFIED"),
    ("review_result_tampered", "REVIEW_EXECUTION_DIGEST_NOT_VERIFIED"),
    ("review_calls_zero", "REVIEW_EXECUTION_DIGEST_NOT_VERIFIED"),
    ("review_actor_same_as_executor", "REVIEW_ACTOR_BINDING_MISMATCH"),
])
def test_false_verification_cannot_be_promoted(target, expected):
    state = runtime_fixture()
    if target == "review.call_allowed":
        state["preflight_receipts"]["review"]["call_allowed"] = False
    elif target == "review.consumed":
        state["preflight_receipts"]["review"]["consumed"] = True
    elif target == "review.authority_digest":
        state["preflight_receipts"]["review"]["authority_digest"] = "stale"
    elif target == "review.call_digest":
        state["preflight_receipts"]["review"]["call_digest"] = ""
    elif target == "target_result_tampered":
        state["execution_calls"]["target"]["result"]["stdout"] = "changed-after-execution"
    elif target == "review_result_tampered":
        state["execution_calls"]["review"]["result"]["stdout"] = '{"passed":true}'
    elif target == "review_calls_zero":
        state["execution_calls"]["review"]["actual_calls"] = 0
    else:
        state["execution_calls"]["target"]["executor_id"] = "TAKY_MODEL_REVIEW_CODEX"
    with pytest.raises(BridgeViolation, match=expected):
        verify_bound_review(state, "target", "review")
    assert state["completion_registry"] == {}
    assert state["execution_outcomes"] == {}


def test_missing_actual_target_stdin_proof_cannot_verify_target():
    state = runtime_fixture()
    del state["execution_calls"]["review"]["target_review_evidence"]
    with pytest.raises(BridgeViolation, match="REVIEW_TARGET_STDIN_PROVENANCE_MISSING"):
        verify_bound_review(state, "target", "review")
    state = runtime_fixture()
    state["execution_calls"]["review"]["target_review_evidence"]["target_result_digest"] = "fake"
    with pytest.raises(BridgeViolation, match="REVIEW_TARGET_STDIN_PROVENANCE_MISSING"):
        verify_bound_review(state, "target", "review")


def test_wrong_review_action_for_actor_holds():
    state = runtime_fixture()
    state["preflight_receipts"]["review"]["action_id"] = "review:external-model"
    with pytest.raises(BridgeViolation, match="REVIEW_ACTOR_ACTION_MISMATCH"):
        verify_bound_review(state, "target", "review")


def test_model_returned_non_object_cannot_verify_target():
    state = runtime_fixture()
    review_call = state["execution_calls"]["review"]
    review_call["result"]["stdout"] = '["passed", true]'
    review_call["result_digest"] = stable_hash(review_call["result"])
    review_call["target_review_evidence"]["review_result_digest"] = (
        review_call["result_digest"])
    with pytest.raises(BridgeViolation, match="REVIEW_VERDICT_MUST_BE_OBJECT"):
        verify_bound_review(state, "target", "review")



def test_negative_verdict_never_emits_completion():
    state = runtime_fixture()
    record = state["execution_calls"]["review"]
    response = json.loads(record["result"]["stdout"])
    response["passed"] = False
    record["result"]["stdout"] = json.dumps(response)
    record["result_digest"] = stable_hash(record["result"])
    record["target_review_evidence"]["review_result_digest"] = record["result_digest"]
    with pytest.raises(BridgeViolation, match="REVIEW_NOT_ACCEPTED_NO_COMPLETION"):
        verify_bound_review(state, "target", "review")
    assert state["completion_registry"] == {}
    assert state["execution_outcomes"] == {}


def test_obsolete_authority_and_replayed_target_cannot_verify():
    state = runtime_fixture()
    state["authority_digest"] = "new-authority"
    with pytest.raises(BridgeViolation, match="TARGET_REVIEW_STALE_AUTHORITY"):
        verify_bound_review(state, "target", "review")
    state = runtime_fixture()
    state["execution_outcomes"]["target"] = "SUCCESS"
    with pytest.raises(BridgeViolation, match="TARGET_ALREADY_VERIFIED_OR_NOT_AUTHORIZED"):
        verify_bound_review(state, "target", "review")

def test_review_receipt_cannot_be_reused_for_completion():
    first = verify_bound_review(runtime_fixture(), "target", "review")
    assert first["preflight_receipts"]["review"]["consumed"] is True
    with pytest.raises(BridgeViolation, match="TARGET_ALREADY_VERIFIED_OR_NOT_AUTHORIZED"):
        verify_bound_review(first, "target", "review")

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
