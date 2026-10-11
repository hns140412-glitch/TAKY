"""Resume must bind checkpoint contents to the requested task and owner."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from execution_checkpoint import checkpoint_hash, guard


class CheckpointIdentityTest(unittest.TestCase):
    def check(self, task_id="TASK", namespace="OWNER", **expectations):
        record = {
            "checkpoint_version": "1.0", "task_id": task_id, "namespace": namespace,
            "atomic_unit": "unit", "status": "RUNNING", "done": [], "open": [],
            "next": "continue", "corrections": [], "source_refs": [],
            "updated_at": "2026-10-03T00:00:00Z",
        }
        record["checkpoint_hash"] = checkpoint_hash(record)
        with patch.object(Path, "exists", return_value=True), patch.object(
            Path, "read_text", return_value=json.dumps(record)
        ):
            return guard(Path.cwd(), "OWNER", "TASK", **expectations)

    def test_matching_identity_accepted(self):
        self.assertTrue(self.check()["pass"])

    def test_wrong_task_with_valid_hash_rejected(self):
        result = self.check(task_id="OTHER_TASK")
        self.assertFalse(result["pass"])
        self.assertIn("CURRENT_CHECKPOINT_TASK_ID_MISMATCH", result["detected"])

    def test_wrong_owner_with_valid_hash_rejected(self):
        result = self.check(namespace="OTHER_OWNER")
        self.assertFalse(result["pass"])
        self.assertIn("CURRENT_CHECKPOINT_NAMESPACE_MISMATCH", result["detected"])

    def test_slug_collision_does_not_authorize_another_identity(self):
        result = self.check(task_id=".TASK.")
        self.assertFalse(result["pass"])
        self.assertIn("CURRENT_CHECKPOINT_TASK_ID_MISMATCH", result["detected"])

    def test_stale_unit_still_rejected(self):
        result = self.check(expected_atomic_unit="new-unit")
        self.assertFalse(result["pass"])
        self.assertIn("CURRENT_CHECKPOINT_STALE_OR_WRONG_UNIT", result["detected"])

    def test_stale_hash_still_rejected(self):
        result = self.check(expected_checkpoint_hash="sha256:" + "0" * 64)
        self.assertFalse(result["pass"])
        self.assertIn("CURRENT_CHECKPOINT_HASH_MISMATCH", result["detected"])


if __name__ == "__main__":
    unittest.main()
