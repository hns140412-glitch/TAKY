#!/usr/bin/env python3
"""Offline efficiency ledger regression; synthetic data only, zero provider calls."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
from TAKY_USAGE_EFFICIENCY_AUDIT import (
    _signed_claude_usage, _history_index, audit_runtime,
)
ensure_trusted_taky2()
from TAKY2.enforcement import stable_hash

TASK = "a" * 32
RID = "pf:external-review-" + TASK + ":" + "b" * 16


def fixture(*, usage=None, provider="anthropic", state="RETURNED",
            cli_code=0, digest_ok=True, output_status="success"):
    if usage is None:
        usage = dict(input_tokens=1, output_tokens=3,
                     cache_creation_input_tokens=5, cache_read_input_tokens=7)
    envelope = {"subtype": output_status, "is_error": output_status != "success",
                "result": "UNTRUSTED_SECRET_PROMPT_NOT_FOR_PUBLIC_OUTPUT",
                "usage": usage, "total_cost_usd": 0.0043}
    result = {"stdout": json.dumps(envelope), "stderr": "", "returncode": cli_code}
    return {"preflight_receipts": {RID: {
                "task_id": "external-review-" + TASK, "allowed": True}},
            "execution_calls": {RID: {
                "status": state, "provider": provider, "model": "sonnet",
                "actual_calls": 1, "result": result,
                "result_digest": stable_hash(result) if digest_ok else "bad"}}}


class LedgerTests(unittest.TestCase):
    def test_true_signed_usage_is_not_savings_or_bill(self):
        out = audit_runtime(fixture(), {TASK: {
            "receiptId": RID, "outerStatus": "COMPLETE_UNVERIFIED",
            "qaState": "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED",
            "qualityVerifiedClaimed": True}})
        self.assertEqual(out["totals"]["signedExecutionClaims"], 1)
        self.assertEqual(out["totals"]["claudeTokenizedReviewCalls"], 1)
        self.assertEqual(out["usageEvidence"]["tokens:output_tokens"], 3)
        self.assertEqual(out["externalReviews"][0]["providerUsage"]["reportedTokenTotal"], 16)
        self.assertTrue(out["externalReviews"][0]["outerReceiptBound"])
        self.assertFalse(out["externalReviews"][0]["taskOutcomeVerified"])
        self.assertIsNone(out["verifiedReworkCount"])
        self.assertIsNone(out["verifiedConsumptionSavingsPercent"])
        self.assertIsNone(out["actualIncrementalBillingUsd"])
        self.assertNotIn("UNTRUSTED_SECRET_PROMPT", json.dumps(out))

    def test_corrupt_result_digest_never_counts_usage(self):
        out = audit_runtime(fixture(digest_ok=False))
        self.assertNotIn("claudeTokenizedReviewCalls", out["totals"])
        self.assertEqual(out["externalReviews"][0]["providerUsage"]["state"],
                         "RESULT_DIGEST_MISMATCH")

    def test_missing_usage_is_not_zero(self):
        out = audit_runtime(fixture(usage={"input_tokens": 0}))
        self.assertNotIn("claudeTokenizedReviewCalls", out["totals"])
        self.assertEqual(out["externalReviews"][0]["providerUsage"]["state"],
                         "CLAUDE_USAGE_FIELDS_MISSING_OR_INVALID")

    def test_failed_model_envelope_is_not_usage_evidence(self):
        for kw in ({"state": "OUTCOME_UNKNOWN"}, {"cli_code": 17},
                   {"output_status": "error"}):
            with self.subTest(kw=kw):
                out = audit_runtime(fixture(**kw))
                self.assertNotIn("claudeTokenizedReviewCalls", out["totals"])

    def test_non_anthropic_not_counted_as_claude(self):
        out = audit_runtime(fixture(provider="openai"))
        self.assertEqual(out["totals"]["provider:openai"], 1)
        self.assertNotIn("claudeTokenizedReviewCalls", out["totals"])

    def test_unbound_preflight_does_not_contribute(self):
        r = fixture()
        r["preflight_receipts"][RID]["allowed"] = False
        out = audit_runtime(r)
        self.assertEqual(out["totals"]["notBoundToAllowedPreflight"], 1)
        self.assertNotIn("signedExecutionClaims", out["totals"])

    def test_outer_receipt_mismatched_id_is_not_quality(self):
        out = audit_runtime(fixture(), {TASK: {
            "receiptId": "pf:external-review-" + TASK + ":" + "0" * 16,
            "qaState": "VERIFIED", "qualityVerifiedClaimed": True}})
        self.assertFalse(out["externalReviews"][0]["outerReceiptBound"])
        self.assertIsNone(out["externalReviews"][0]["contentQaState"])

    def test_local_history_reader_does_not_emit_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder / ("TAKY_ROUTED_" + TASK + ".json")
            path.write_text(json.dumps({
                "task_id": TASK, "executor": "Claude", "state": "COMPLETE_UNVERIFIED",
                "taky2_signed_receipt_id": RID, "content_qa_state": "QA_HOLD",
                "result": "TOP_PRIVATE_USER_PROMPT"}))
            out = audit_runtime(fixture(), _history_index(folder))
            self.assertEqual(out["externalReviews"][0]["contentQaState"], "QA_HOLD")
            self.assertNotIn("TOP_PRIVATE_USER_PROMPT", json.dumps(out))

    def test_invalid_or_absent_runtime_fail_closed(self):
        for bad in (None, {}, {"preflight_receipts": {}, "execution_calls": None}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    audit_runtime(bad)

    def test_provider_0_tokens_is_real_only_when_explicit(self):
        out = audit_runtime(fixture(usage=dict.fromkeys(
            ("input_tokens", "output_tokens", "cache_creation_input_tokens",
             "cache_read_input_tokens"), 0)))
        self.assertEqual(out["externalReviews"][0]["providerUsage"]["reportedTokenTotal"], 0)


if __name__ == "__main__":
    unittest.main()
