#!/usr/bin/env python3
import unittest
from TAKY_SIGNED_EXECUTION_READBACK import correlate, _digest

IDENT = "a" * 32
RID = "pf:external-review-" + IDENT + ":abcd1234"


def state(returncode=0, status="RETURNED", with_result=True):
    sample = {
        "preflight_receipts": {
            RID: {"task_id": "external-review-" + IDENT, "allowed": True, "call_allowed": True}
        },
        "execution_calls": {},
    }
    if with_result:
        result = {"returncode": returncode,
                  "stdout": "Do not expose confidential output", "stderr": ""}
        sample["execution_calls"][RID] = {
            "model": "codex", "provider": "openai", "status": status,
            "result": result, "result_digest": _digest(result),
        }
    return sample


class SignedReceiptCorrelationTests(unittest.TestCase):
    def test_one_returned_cli_is_not_accepted_as_verified_task(self):
        data = correlate(IDENT, state(), RID)
        self.assertEqual(data["state"], "CLI_RETURNED_UNVERIFIED")
        self.assertFalse(data["modelSuccessVerified"])
        self.assertFalse(data["creditSavingsMeasured"])
        self.assertEqual(data["cliExitCode"], 0)
        self.assertNotIn("confidential", str(data))

    def test_signed_call_manifest_and_result_digest_are_bound(self):
        inp = {"model": "codex", "packet_digest": "a" * 20}
        sample = state()
        sample["preflight_receipts"][RID]["call_digest"] = _digest(inp)
        yes = correlate(IDENT, sample, RID, inp)
        self.assertTrue(yes["signedCallManifestBound"])
        self.assertEqual(yes["state"], "CLI_RETURNED_UNVERIFIED")
        bad = correlate(IDENT, sample, RID, {"model": "fake"})
        self.assertEqual(bad["state"], "SIGNED_CALL_MANIFEST_MISMATCH_HOLD")
        corrupted = state()
        corrupted["execution_calls"][RID]["result"]["stdout"] = "tampered"
        result = correlate(IDENT, corrupted, RID)
        self.assertEqual(result["state"], "SIGNED_RETURN_DIGEST_MISMATCH_HOLD")
        self.assertFalse(result["modelSuccessVerified"])


    def test_sealed_verified_execution_is_distinct_from_user_done(self):
        signed = state()
        pf = signed["preflight_receipts"][RID]
        pf.update(plan_digest="p", action_digest="a", call_digest="c", authority_digest="auth")
        call = signed["execution_calls"][RID]
        call["executor_id"] = "CLAUDE_EXECUTOR"
        evidence_ref = "verified:target:receipt"
        signed["execution_outcomes"] = {RID: "SUCCESS"}
        signed["completion_registry"] = {RID: {
            "plan_digest": "p", "action_digest": "a", "call_digest": "c",
            "authority_digest": "auth", "key_match": True, "critical_gaps": [],
            "verified_by": "CODEX_REVIEWER",
            "required_verifications": ["technical", "intent"],
            "passed_verifications": ["technical", "intent"],
            "evidence_refs": [evidence_ref],
        }}
        signed["evidence_registry"] = {evidence_ref: {
            "verified": True, "acceptance_state": "ACCEPTED", "receipt_id": RID,
            "revision_or_hash": call["result_digest"],
            "authority_digest_or_key_version": "auth",
            "validator": "CODEX_REVIEWER",
        }}
        result = correlate(IDENT, signed, RID)
        self.assertEqual(result["state"], "CLI_RETURNED_UNVERIFIED")
        self.assertTrue(result["executionEvidenceVerified"])
        self.assertEqual(result["executionVerificationState"],
                         "SIGNED_EXECUTION_EVIDENCED_NOT_USER_DONE")
        self.assertFalse(result["modelSuccessVerified"])
        self.assertNotIn("CODEX_REVIEWER", str(result))
        signed["evidence_registry"][evidence_ref]["revision_or_hash"] = "forged"
        altered = correlate(IDENT, signed, RID)
        self.assertFalse(altered["executionEvidenceVerified"])
        signed["evidence_registry"][evidence_ref]["revision_or_hash"] = call["result_digest"]
        signed["completion_registry"][RID]["call_digest"] = "wrong"
        self.assertFalse(correlate(IDENT, signed, RID)["executionEvidenceVerified"])
        signed["completion_registry"][RID]["call_digest"] = "c"
        signed["execution_outcomes"][RID] = "UNKNOWN"
        self.assertFalse(correlate(IDENT, signed, RID)["executionEvidenceVerified"])


    def test_strong_independent_review_evidence_uses_review_digest_not_target_digest(self):
        signed = state()
        pf = signed["preflight_receipts"][RID]
        pf.update(plan_digest="p", action_digest="a", call_digest="c", authority_digest="auth")
        call = signed["execution_calls"][RID]
        call["executor_id"] = "CLAUDE_EXECUTOR"
        signed["execution_outcomes"] = {RID: "SUCCESS"}
        signed["completion_registry"] = {RID: {
            "plan_digest": "p", "action_digest": "a", "call_digest": "c",
            "authority_digest": "auth", "key_match": True, "critical_gaps": [],
            "verified_by": "CODEX_VERIFIER",
            "required_verifications": ["technical", "intent", "independent"],
            "passed_verifications": ["technical", "intent", "independent"],
            "independent_reviewer_role": "INDEPENDENT_REVIEWER",
            "independent_reviewer_actor": "CLAUDE",
            "independent_review_ref": "review:1",
            "evidence_refs": ["verify:1", "review:1"],
        }}
        common = {"verified": True, "acceptance_state": "ACCEPTED",
                  "receipt_id": RID, "authority_digest_or_key_version": "auth"}
        signed["evidence_registry"] = {
            "verify:1": {**common, "revision_or_hash": call["result_digest"],
                         "validator": "CODEX_VERIFIER"},
            "review:1": {**common, "revision_or_hash": "review-content-digest",
                         "result_digest": call["result_digest"],
                         "validator": "INDEPENDENT_REVIEW_BRIDGE"},
        }
        signed["independent_review_registry"] = {"review:1": {
            "receipt_id": RID, "acceptance_state": "ACCEPTED",
            "target_result_digest": call["result_digest"], "authority_digest": "auth",
            "review_digest": "review-content-digest",
            "bridge_id": "INDEPENDENT_REVIEW_BRIDGE",
            "reviewer_role": "INDEPENDENT_REVIEWER",
            "reviewer_actor": "CLAUDE", "reviewer_id": "CLAUDE_REVIEWER_DIFFERENT",
        }}
        valid = correlate(IDENT, signed, RID)
        self.assertTrue(valid["executionEvidenceVerified"])
        signed["independent_review_registry"]["review:1"]["review_digest"] = "tampered"
        self.assertFalse(correlate(IDENT, signed, RID)["executionEvidenceVerified"])
        signed["independent_review_registry"]["review:1"]["review_digest"] = "review-content-digest"
        signed["independent_review_registry"]["review:1"]["reviewer_id"] = "CLAUDE_EXECUTOR"
        self.assertFalse(correlate(IDENT, signed, RID)["executionEvidenceVerified"])

    def test_claimed_completion_without_signed_evidence_does_not_verify(self):
        signed = state()
        signed["execution_outcomes"] = {RID: "SUCCESS"}
        signed["completion_registry"] = {RID: {"verified_by": "MODEL_OUTPUT",
                                                  "key_match": True}}
        result = correlate(IDENT, signed, RID)
        self.assertFalse(result["executionEvidenceVerified"])
        self.assertEqual(result["executionVerificationState"], "NO_BOUND_COMPLETION_EVIDENCE")

    def test_preinvoke_release_not_treated_as_model_success(self):
        example = state(with_result=False)
        example["execution_outcomes"] = {RID: "PREINVOKE_RELEASED"}
        result = correlate(IDENT, example)
        self.assertEqual(result["state"], "PREINVOKE_RELEASED")
        self.assertFalse(result["modelSuccessVerified"])

    def test_binding_mismatch_fails_closed(self):
        result = correlate(IDENT, state(), "pf:external-review-abc:different")
        self.assertEqual(result["state"], "RECEIPT_ID_MISMATCH_HOLD")
        self.assertFalse(result["modelSuccessVerified"])

    def test_preflight_without_execution_is_not_returned(self):
        self.assertEqual(correlate(IDENT, state(with_result=False))["state"], "PREFLIGHT_ONLY")

    def test_ambiguous_multiple_execution_attempts_hold(self):
        s = state()
        alt = RID[:-4] + "7777"
        s["preflight_receipts"][alt] = {
            "task_id": "external-review-" + IDENT, "allowed": True, "call_allowed": True}
        self.assertEqual(correlate(IDENT, s)["state"], "MULTIPLE_PREFLIGHTS_HOLD_NO_RETRY")

    def test_unknown_status_stays_unknown(self):
        self.assertEqual(correlate(IDENT, state(status="OUTCOME_UNKNOWN"))["state"],
                         "EXECUTION_OUTCOME_UNKNOWN_NO_RETRY")

    def test_nonzero_exit_stays_unresolved(self):
        self.assertEqual(correlate(IDENT, state(returncode=124))["state"],
                         "EXECUTION_UNRESOLVED_NO_RETRY")

    def test_malformed_task_id_rejected(self):
        with self.assertRaises(ValueError):
            correlate("../../bad", {})

    def test_no_receipt_is_absence_of_evidence(self):
        self.assertEqual(correlate(IDENT, {})["state"], "SIGNED_PREFLIGHT_NOT_FOUND")
        self.assertEqual(correlate(IDENT, {"preflight_receipts": {}, "execution_calls": {}})["state"],
                         "SIGNED_PREFLIGHT_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
