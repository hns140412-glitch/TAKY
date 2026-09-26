#!/usr/bin/env python3
import unittest

from execution_state_engine import approval_context, transition


def approval_for(record):
    current = str(record["current_state"]).upper()
    requested = str(record["requested_state"]).upper()
    context, failures = approval_context(record, current, requested)
    assert not failures, failures
    return {
        "approval_id": "approval-transition-001",
        "approver_ref": "USER",
        "decision": "APPROVE",
        **context,
    }


class ExecutionStateApprovalBindingTest(unittest.TestCase):
    def test_merge_approval_is_bound_to_exact_target(self):
        record = {
            "task_id": "TASK-1",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
        }
        record["human_approval_evidence"] = approval_for(record)
        result = transition(record)
        self.assertTrue(result["pass"], result)
        self.assertEqual(
            result["approval_verified"]["target_ref"],
            "commit:abc123",
        )

    def test_stale_merge_approval_cannot_authorize_new_target(self):
        record = {
            "task_id": "TASK-1",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
        }
        evidence = approval_for(record)
        record["transition_target_ref"] = "commit:def456"
        record["human_approval_evidence"] = evidence
        result = transition(record)
        self.assertFalse(result["pass"])
        self.assertIn(
            "APPROVAL_EVIDENCE_TARGET_REF_MISMATCH",
            result["detected"],
        )
        self.assertIn(
            "APPROVAL_EVIDENCE_CONTEXT_HASH_MISMATCH",
            result["detected"],
        )

    def test_deploy_approval_is_bound_to_deploy_target(self):
        record = {
            "task_id": "TASK-2",
            "current_state": "MERGED",
            "requested_state": "DEPLOYED",
            "transition_target_ref": "production:artifact-sha256:123",
        }
        record["human_approval_evidence"] = approval_for(record)
        result = transition(record)
        self.assertTrue(result["pass"], result)
        self.assertEqual(
            result["approval_verified"]["to_state"],
            "DEPLOYED",
        )

    def test_unstructured_approval_evidence_is_rejected(self):
        record = {
            "task_id": "TASK-3",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
            "human_approval_evidence": "yes",
        }
        result = transition(record)
        self.assertFalse(result["pass"])
        self.assertIn("HUMAN_APPROVAL_EVIDENCE_INVALID", result["detected"])

    def test_missing_approval_returns_required_context(self):
        record = {
            "task_id": "TASK-4",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "pr:133/head:abc123",
        }
        result = transition(record)
        self.assertFalse(result["pass"])
        self.assertIn("HUMAN_APPROVAL_MISSING:merge", result["detected"])
        context = result["required_approval_context"]
        self.assertEqual(context["task_id"], "TASK-4")
        self.assertEqual(context["target_ref"], "pr:133/head:abc123")
        self.assertTrue(context["approval_context_hash"].startswith("sha256:"))

    def test_missing_target_ref_fails_closed(self):
        record = {
            "task_id": "TASK-5",
            "current_state": "MERGED",
            "requested_state": "DEPLOYED",
        }
        result = transition(record)
        self.assertFalse(result["pass"])
        self.assertIn(
            "APPROVAL_CONTEXT_TARGET_REF_MISSING",
            result["detected"],
        )

    def test_explicit_no_approval_requirement_preserves_transition(self):
        record = {
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "merge_approval_required": False,
        }
        result = transition(record)
        self.assertTrue(result["pass"], result)
        self.assertIsNone(result["approval_verified"])


if __name__ == "__main__":
    unittest.main()
