#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from execution_checkpoint import consume_approval, guard, persist, validate_approval_evidence


def checkpoint_record():
    return {
        "checkpoint_version": "1.0",
        "task_id": "approval-resume-test",
        "namespace": "RUNTIME",
        "atomic_unit": "approval-boundary",
        "status": "BLOCKED",
        "done": ["validation"],
        "open": ["human approval"],
        "next": "resume implementation",
        "corrections": [],
        "source_refs": ["CURRENT:test"],
        "updated_at": "2026-09-26T00:00:00+00:00",
        "approval_binding": {
            "action_class": "HUMAN_APPROVAL",
            "execution_owner": "USER",
        },
    }


def approval_evidence(checkpoint_hash):
    return {
        "approval_id": "approval-001",
        "approver_ref": "USER",
        "decision": "APPROVE",
        "namespace": "RUNTIME",
        "task_id": "approval-resume-test",
        "checkpoint_hash": checkpoint_hash,
        "atomic_unit": "approval-boundary",
    }


class ApprovalCheckpointResumeTest(unittest.TestCase):
    def test_exact_checkpoint_hash_resumes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            saved = persist(checkpoint_record(), root)
            self.assertTrue(saved["pass"], saved["detected"])
            result = guard(
                root,
                namespace="RUNTIME",
                task_id="approval-resume-test",
                expected_atomic_unit="approval-boundary",
                expected_checkpoint_hash=saved["checkpoint_hash"],
            )
            self.assertTrue(result["pass"], result["detected"])

    def test_wrong_checkpoint_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            saved = persist(checkpoint_record(), root)
            self.assertTrue(saved["pass"], saved["detected"])
            result = guard(
                root,
                namespace="RUNTIME",
                task_id="approval-resume-test",
                expected_atomic_unit="approval-boundary",
                expected_checkpoint_hash="sha256:not-the-approved-state",
            )
            self.assertFalse(result["pass"])
            self.assertIn("CURRENT_CHECKPOINT_HASH_MISMATCH", result["detected"])

    def test_mutated_checkpoint_cannot_match_approved_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            saved = persist(checkpoint_record(), root)
            self.assertTrue(saved["pass"], saved["detected"])

            current = root / "CURRENT" / "RUNTIME" / "approval-resume-test.json"
            payload = json.loads(current.read_text(encoding="utf-8"))
            payload["next"] = "different action"
            current.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = guard(
                root,
                namespace="RUNTIME",
                task_id="approval-resume-test",
                expected_atomic_unit="approval-boundary",
                expected_checkpoint_hash=saved["checkpoint_hash"],
            )
            self.assertFalse(result["pass"])
            self.assertIn(
                "CURRENT_CHECKPOINT_INTEGRITY_MISMATCH",
                result["detected"],
            )

    def test_bound_approval_is_consumed_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            saved = persist(checkpoint_record(), root)
            self.assertTrue(saved["pass"], saved["detected"])

            first = consume_approval(
                root,
                namespace="RUNTIME",
                task_id="approval-resume-test",
                expected_atomic_unit="approval-boundary",
                expected_checkpoint_hash=saved["checkpoint_hash"],
                evidence=approval_evidence(saved["checkpoint_hash"]),
            )
            self.assertTrue(first["pass"], first)
            self.assertTrue(first["approval_consumed"])
            self.assertTrue(Path(first["claim_path"]).exists())

            current = root / "CURRENT" / "RUNTIME" / "approval-resume-test.json"
            completed = json.loads(current.read_text(encoding="utf-8"))
            self.assertEqual(completed["status"], "COMPLETE")
            self.assertEqual(
                completed["approval_consumption"]["approval_id"],
                "approval-001",
            )

            replay = consume_approval(
                root,
                namespace="RUNTIME",
                task_id="approval-resume-test",
                expected_atomic_unit="approval-boundary",
                expected_checkpoint_hash=saved["checkpoint_hash"],
                evidence=approval_evidence(saved["checkpoint_hash"]),
            )
            self.assertFalse(replay["pass"])
            self.assertIn("CURRENT_CHECKPOINT_HASH_MISMATCH", replay["detected"])

    def test_approval_evidence_must_match_checkpoint(self):
        saved_hash = "sha256:approved-state"
        evidence = approval_evidence("sha256:different-state")
        normalized, failures = validate_approval_evidence(
            evidence,
            namespace="RUNTIME",
            task_id="approval-resume-test",
            checkpoint_hash_value=saved_hash,
            atomic_unit="approval-boundary",
        )
        self.assertIsNotNone(normalized)
        self.assertIn(
            "APPROVAL_EVIDENCE_CHECKPOINT_HASH_MISMATCH",
            failures,
        )

    def test_rejected_decision_cannot_resume(self):
        evidence = approval_evidence("sha256:approved-state")
        evidence["decision"] = "REJECT"
        _, failures = validate_approval_evidence(
            evidence,
            namespace="RUNTIME",
            task_id="approval-resume-test",
            checkpoint_hash_value="sha256:approved-state",
            atomic_unit="approval-boundary",
        )
        self.assertIn("APPROVAL_DECISION_NOT_APPROVED", failures)

    def test_approval_evidence_must_match_task_and_unit(self):
        evidence = approval_evidence("sha256:approved-state")
        evidence["task_id"] = "other-task"
        evidence["atomic_unit"] = "other-boundary"
        _, failures = validate_approval_evidence(
            evidence,
            namespace="RUNTIME",
            task_id="approval-resume-test",
            checkpoint_hash_value="sha256:approved-state",
            atomic_unit="approval-boundary",
        )
        self.assertIn("APPROVAL_EVIDENCE_TASK_ID_MISMATCH", failures)
        self.assertIn("APPROVAL_EVIDENCE_ATOMIC_UNIT_MISMATCH", failures)

    def test_orchestrator_contains_approval_checkpoint_binding(self):
        source = (
            Path(__file__).with_name("runtime_orchestrator.py")
            .read_text(encoding="utf-8")
        )
        self.assertIn("APPROVAL_CHECKPOINT_REQUIRED", source)
        self.assertIn("HUMAN_APPROVAL_EVIDENCE_MISSING_FOR_RESUME", source)
        self.assertIn("expected_checkpoint_hash=checkpoint_hash", source)
        self.assertIn('"approval_checkpoint": approval_checkpoint_result', source)
        self.assertIn('"approval_resume_guard": approval_resume_result', source)
        self.assertIn('"approval_consumption": approval_consumption_result', source)
        self.assertIn("consume_approval(", source)


if __name__ == "__main__":
    unittest.main()
