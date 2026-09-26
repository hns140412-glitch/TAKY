#!/usr/bin/env python3
import unittest

from executor_transport import build_envelope, validate_receipt


def envelope():
    result = build_envelope(
        {
            "task_id": "outcome-state-test",
            "repository": "hns140412-glitch/TAKY",
            "executor_automation": {"target_repository_local": False},
        }
    )
    assert result["pass"]
    return result["dispatch_envelope"]


def receipt(env, status, **extra):
    value = {
        "task_id": env["task_id"],
        "task_contract_sha256": env["task_contract_sha256"],
        "provider": env["provider"],
        "executor_run_id": "run-1",
        "status": status,
    }
    value.update(extra)
    return value


class ExecutionOutcomeStateTest(unittest.TestCase):
    def test_accepted_is_not_started(self):
        env = envelope()
        result = validate_receipt(env, receipt(env, "ACCEPTED"))
        self.assertTrue(result["pass"])
        self.assertEqual(result["execution_outcome"], "NOT_STARTED")

    def test_started_is_running(self):
        env = envelope()
        result = validate_receipt(env, receipt(env, "STARTED"))
        self.assertTrue(result["pass"])
        self.assertEqual(result["execution_outcome"], "RUNNING")

    def test_completed_without_post_condition_is_unknown(self):
        env = envelope()
        result = validate_receipt(env, receipt(env, "COMPLETED"))
        self.assertTrue(result["pass"])
        self.assertEqual(result["execution_outcome"], "OUTCOME_UNKNOWN")
        self.assertTrue(result["post_condition_verification_required"])
        self.assertFalse(result["blind_retry_permitted"])

    def test_verified_success_is_succeeded(self):
        env = envelope()
        result = validate_receipt(
            env,
            receipt(
                env,
                "COMPLETED",
                outcome_status="SUCCEEDED",
                post_condition_verified=True,
            ),
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["execution_outcome"], "SUCCEEDED")
        self.assertTrue(result["outcome_confirmed"])

    def test_verified_failure_is_failed_confirmed(self):
        env = envelope()
        result = validate_receipt(
            env,
            receipt(
                env,
                "COMPLETED",
                outcome_status="FAILED_CONFIRMED",
                post_condition_verified=True,
            ),
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["execution_outcome"], "FAILED_CONFIRMED")
        self.assertTrue(result["outcome_confirmed"])

    def test_unverified_success_claim_remains_unknown(self):
        env = envelope()
        result = validate_receipt(
            env,
            receipt(env, "COMPLETED", outcome_status="SUCCEEDED"),
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["execution_outcome"], "OUTCOME_UNKNOWN")
        self.assertFalse(result["outcome_confirmed"])

    def test_invalid_outcome_enum_fails_validation(self):
        env = envelope()
        result = validate_receipt(
            env,
            receipt(
                env,
                "COMPLETED",
                outcome_status="FAILED",
                post_condition_verified=True,
            ),
        )
        self.assertFalse(result["pass"])
        self.assertIn("EXECUTION_OUTCOME_STATUS_INVALID", result["detected"])


if __name__ == "__main__":
    unittest.main()
