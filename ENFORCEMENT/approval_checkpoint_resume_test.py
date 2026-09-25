#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from execution_checkpoint import guard, persist


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


if __name__ == "__main__":
    unittest.main()
