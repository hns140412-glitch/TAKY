#!/usr/bin/env python3
import unittest

from codex_task_contract_builder import build as build_task_contract
from executor_transport import build_envelope, sha256_json, validate_receipt, validate_retry


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


def mutation_envelope(payload=None, effect_class="NON_IDEMPOTENT_MUTATION", retry_budget=2):
    payload = payload or {"resource": "demo", "value": 1}
    policy = {
        "effect_class": effect_class,
        "request_fingerprint": sha256_json(payload),
        "reconcile_before_retry": effect_class == "NON_IDEMPOTENT_MUTATION",
        "retry_budget": retry_budget,
        "compensation_ref": None,
    }
    result = build_envelope(
        {
            "task_id": "side-effect-test",
            "repository": "hns140412-glitch/TAKY",
            "executor_automation": {"target_repository_local": False},
            "effect_policy": policy,
        }
    )
    assert result["pass"], result
    return result["dispatch_envelope"]


def receipt(env, status, **extra):
    value = {
        "task_id": env["task_id"],
        "task_contract_sha256": env["task_contract_sha256"],
        "provider": env["provider"],
        "executor_run_id": "run-1",
        "status": status,
    }
    if (env.get("effect_policy") or {}).get("effect_class") != "READ_ONLY":
        value["operation_key"] = env["operation_key"]
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

    def test_builder_generates_mutation_request_fingerprint(self):
        base = {
            "task_id": "builder-effect-test",
            "project": "TAKY",
            "repository": "hns140412-glitch/TAKY",
            "base_branch": "main",
            "verified_base_head": "a" * 40,
            "allowed_change_scope": ["ENFORCEMENT/"],
            "acceptance_tests": ["side effect retry contract"],
            "working_model": {
                "primary_outcome": "Safely retry ambiguous side effects.",
                "protected_state": [],
            },
            "effect_class": "NON_IDEMPOTENT_MUTATION",
            "side_effect_request": {"target": "record-1", "value": 1},
            "retry_budget": 2,
        }
        first = build_task_contract(base)
        self.assertTrue(first["pass"], first)
        policy = first["task_contract"]["effect_policy"]
        self.assertEqual(policy["effect_class"], "NON_IDEMPOTENT_MUTATION")
        self.assertEqual(len(policy["request_fingerprint"]), 64)
        self.assertTrue(policy["reconcile_before_retry"])

        changed = dict(base)
        changed["side_effect_request"] = {"target": "record-1", "value": 2}
        second = build_task_contract(changed)
        self.assertTrue(second["pass"], second)
        self.assertNotEqual(
            policy["request_fingerprint"],
            second["task_contract"]["effect_policy"]["request_fingerprint"],
        )

    def test_mutation_operation_key_is_stable_for_same_contract(self):
        first = mutation_envelope()
        second = mutation_envelope()
        self.assertEqual(first["operation_key"], second["operation_key"])

    def test_mutation_receipt_rejects_wrong_operation_key(self):
        env = mutation_envelope()
        result = validate_receipt(
            env,
            receipt(env, "COMPLETED", operation_key="wrong-key"),
        )
        self.assertFalse(result["pass"])
        self.assertIn("DISPATCH_RECEIPT_OPERATION_KEY_MISMATCH", result["detected"])

    def test_unknown_mutation_requires_reconciliation_before_retry(self):
        env = mutation_envelope()
        previous = receipt(env, "COMPLETED")
        retry = {
            "operation_key": env["operation_key"],
            "request_fingerprint": env["effect_policy"]["request_fingerprint"],
            "retry_attempt": 1,
        }
        result = validate_retry(env, previous, retry)
        self.assertFalse(result["pass"])
        self.assertIn("RETRY_RECONCILIATION_REQUIRED", result["detected"])

    def test_reconciled_not_applied_allows_retry(self):
        env = mutation_envelope()
        previous = receipt(
            env,
            "COMPLETED",
            provider_operation_id="provider-op-123",
        )
        retry = {
            "operation_key": env["operation_key"],
            "request_fingerprint": env["effect_policy"]["request_fingerprint"],
            "retry_attempt": 1,
            "reconciliation": {
                "performed": True,
                "effect_state": "NOT_APPLIED",
                "request_fingerprint": env["effect_policy"]["request_fingerprint"],
            },
        }
        result = validate_retry(env, previous, retry)
        self.assertTrue(result["pass"], result)
        self.assertTrue(result["retry_permitted"])
        self.assertEqual(result["provider_operation_id"], "provider-op-123")

    def test_reconciled_applied_blocks_duplicate_effect(self):
        env = mutation_envelope()
        previous = receipt(env, "COMPLETED")
        retry = {
            "operation_key": env["operation_key"],
            "request_fingerprint": env["effect_policy"]["request_fingerprint"],
            "retry_attempt": 1,
            "reconciliation": {
                "performed": True,
                "effect_state": "APPLIED_CONFIRMED",
                "request_fingerprint": env["effect_policy"]["request_fingerprint"],
            },
        }
        result = validate_retry(env, previous, retry)
        self.assertFalse(result["pass"])
        self.assertIn("RETRY_BLOCKED_EFFECT_ALREADY_APPLIED", result["detected"])

    def test_changed_payload_fingerprint_cannot_reuse_operation(self):
        env = mutation_envelope()
        previous = receipt(env, "COMPLETED")
        retry = {
            "operation_key": env["operation_key"],
            "request_fingerprint": sha256_json({"resource": "demo", "value": 2}),
            "retry_attempt": 1,
            "reconciliation": {
                "performed": True,
                "effect_state": "NOT_APPLIED",
                "request_fingerprint": env["effect_policy"]["request_fingerprint"],
            },
        }
        result = validate_retry(env, previous, retry)
        self.assertFalse(result["pass"])
        self.assertIn("RETRY_REQUEST_FINGERPRINT_MISMATCH", result["detected"])


if __name__ == "__main__":
    unittest.main()
