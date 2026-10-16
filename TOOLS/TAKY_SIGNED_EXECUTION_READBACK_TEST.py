#!/usr/bin/env python3
import unittest
from TAKY_SIGNED_EXECUTION_READBACK import correlate

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
        sample["execution_calls"][RID] = {
            "model": "codex", "provider": "openai", "status": status,
            "result": {"returncode": returncode, "stdout": "Do not expose confidential output",
                       "stderr": ""}, "result_digest": "fixed-digest",
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
