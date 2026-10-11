#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from execution_state_engine import approval_context, transition


def approval_for(record):
    current = str(record["current_state"]).upper()
    requested = str(record["requested_state"]).upper()
    record.setdefault(
        "transition_action_payload",
        {
            "requested_state": requested,
            "target_ref": record.get("transition_target_ref"),
        },
    )
    context, failures = approval_context(record, current, requested)
    assert not failures, failures
    return {
        "approval_id": "approval-transition-001",
        "approver_ref": "USER",
        "decision": "APPROVE",
        **context,
    }


class ExecutionStateApprovalBindingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_root = Path(self.tmp.name)

    def do_transition(self, record):
        return transition(record, self.state_root)

    def test_merge_approval_is_bound_to_exact_target(self):
        record = {
            "task_id": "TASK-1",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
        }
        record["human_approval_evidence"] = approval_for(record)
        result = self.do_transition(record)
        self.assertTrue(result["pass"], result)
        self.assertEqual(
            result["approval_verified"]["target_ref"],
            "commit:abc123",
        )
        self.assertEqual(
            result["approval_verified"]["evidence_level"],
            "BOUND_RECORD_ONLY",
        )
        self.assertFalse(result["approval_verified"]["identity_authenticated"])

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
        result = self.do_transition(record)
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
        result = self.do_transition(record)
        self.assertTrue(result["pass"], result)
        self.assertEqual(
            result["approval_verified"]["to_state"],
            "DEPLOYED",
        )
        self.assertTrue(
            result["approval_verified"]["action_payload_hash"].startswith("sha256:")
        )

    def test_stale_approval_cannot_authorize_mutated_action_payload(self):
        record = {
            "task_id": "TASK-PAYLOAD",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
            "transition_action_payload": {
                "requested_state": "MERGED",
                "target_ref": "commit:abc123",
                "release_notes": "approved",
            },
        }
        evidence = approval_for(record)
        record["transition_action_payload"]["release_notes"] = "changed-after-approval"
        record["human_approval_evidence"] = evidence
        result = self.do_transition(record)
        self.assertFalse(result["pass"])
        self.assertIn(
            "APPROVAL_EVIDENCE_ACTION_PAYLOAD_HASH_MISMATCH",
            result["detected"],
        )
        self.assertIn(
            "APPROVAL_EVIDENCE_CONTEXT_HASH_MISMATCH",
            result["detected"],
        )

    def test_unstructured_approval_evidence_is_rejected(self):
        record = {
            "task_id": "TASK-3",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
            "human_approval_evidence": "yes",
        }
        result = self.do_transition(record)
        self.assertFalse(result["pass"])
        self.assertIn("HUMAN_APPROVAL_EVIDENCE_INVALID", result["detected"])

    def test_missing_approval_returns_required_context(self):
        record = {
            "task_id": "TASK-4",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "pr:133/head:abc123",
        }
        result = self.do_transition(record)
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
        result = self.do_transition(record)
        self.assertFalse(result["pass"])
        self.assertIn(
            "APPROVAL_CONTEXT_TARGET_REF_MISSING",
            result["detected"],
        )
        self.assertIn(
            "APPROVAL_CONTEXT_ACTION_PAYLOAD_MISSING",
            result["detected"],
        )

    def test_caller_cannot_disable_merge_approval_requirement(self):
        record = {
            "task_id": "TASK-6",
            "current_state": "HUMAN_APPROVAL",
            "requested_state": "MERGED",
            "transition_target_ref": "commit:abc123",
            "merge_approval_required": False,
        }
        result = self.do_transition(record)
        self.assertFalse(result["pass"], result)
        self.assertIn("HUMAN_APPROVAL_MISSING:merge", result["detected"])

    def test_same_high_impact_approval_cannot_be_replayed(self):
        record = {
            "task_id": "TASK-REPLAY",
            "current_state": "MERGED",
            "requested_state": "DEPLOYED",
            "transition_target_ref": "production:artifact-sha256:replay",
        }
        record["human_approval_evidence"] = approval_for(record)
        first = self.do_transition(record)
        self.assertTrue(first["pass"], first)
        second = self.do_transition(record)
        self.assertFalse(second["pass"], second)
        self.assertIn("TRANSITION_APPROVAL_ALREADY_CONSUMED", second["detected"])


    def test_executor_neutral_assignment_alias_is_accepted(self):
        result = self.do_transition({
            "task_id": "TASK-7",
            "current_state": "READY",
            "requested_state": "ASSIGNED_TO_EXECUTOR",
            "transition_target_ref": "local-only",
        })
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["current_state"], "ASSIGNED_TO_CODEX")


if __name__ == "__main__":
    unittest.main()
