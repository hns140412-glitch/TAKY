import hashlib
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from continuity_resume import canonical_bytes, generate, sha256, verify_checkpoint, within


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.repo = self.root / "repo"
        self.state.mkdir()
        self.repo.mkdir()
        (self.repo / "OWNER.md").write_text("owner\n", encoding="utf-8")
        self.config = {
            "state_root": str(self.state),
            "owners": {"DATA": {"repo": str(self.repo), "canonical_path": "OWNER.md"}},
            "tasks": [{"namespace": "DATA", "task_id": "ONE"}],
        }

    def checkpoint(self, tamper=False):
        path = self.state / "CURRENT" / "DATA" / "ONE.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"checkpoint_version": "1.0", "namespace": "DATA", "task_id": "ONE",
                  "atomic_unit": "unit-1", "status": "RUNNING", "done": ["closed"],
                  "open": ["still-open"], "next": "next-unit", "corrections": ["keep"],
                  "source_refs": ["source-id"], "updated_at": "2026-09-28T12:00:00+09:00"}
        record["checkpoint_hash"] = sha256(canonical_bytes(record))
        if tamper:
            record["open"].append("unverified change")
        path.write_text(json.dumps(record), encoding="utf-8")

    def test_missing_is_blocked_not_success(self):
        e = verify_checkpoint(self.state, "DATA", "ONE")
        self.assertEqual(e["status"], "BLOCKED")
        self.assertIn("CURRENT_CHECKPOINT_MISSING", e["issues"])

    def test_valid_integrity_and_default_minimal_export(self):
        self.checkpoint()
        e = verify_checkpoint(self.state, "DATA", "ONE")
        self.assertEqual(e["status"], "LOCAL_INTEGRITY_VERIFIED")
        with mock.patch("continuity_resume.git_snapshot", return_value={"issues": [], "live_freshness": "NOT_CHECKED"}):
            payload = generate(self.config, self.root / "report")
        self.assertEqual(payload["overall"], "REVIEW_REQUIRED")
        self.assertIsNone(payload["entries"][0]["snapshot"])
        self.assertNotIn("still-open", (self.root / "report" / "CHATGPT_RESUME_NOTE.md").read_text())
        self.assertEqual(payload["entries"][0]["handoff"]["status"], "NOT_CONFIGURED")

    def test_opt_in_context_and_missing_owner_block(self):
        self.checkpoint()
        self.config["owners"] = {}
        payload = generate(self.config, self.root / "report", include_context=True)
        self.assertEqual(payload["overall"], "BLOCKED")
        self.assertEqual(payload["entries"][0]["snapshot"]["open"], ["still-open"])
        self.assertIn("OWNER_NOT_CONFIGURED", payload["entries"][0]["issues"])

    def test_tamper_fails_hash(self):
        self.checkpoint(tamper=True)
        e = verify_checkpoint(self.state, "DATA", "ONE")
        self.assertIn("CURRENT_CHECKPOINT_INTEGRITY_MISMATCH", e["issues"])
        self.assertIsNone(e["snapshot"])

    def test_no_traversal(self):
        with self.assertRaises(ValueError):
            within(self.state, "../escape")
        with self.assertRaises(ValueError):
            within(self.state, str(self.root / "escape"))

    def test_missing_handoff_explicitly_unknown(self):
        self.checkpoint()
        self.config["tasks"][0]["handoff_relative_path"] = "HANDOFF/missing.md"
        payload = generate(self.config, self.root / "report")
        self.assertIn("HANDOFF_SOURCE_UNAVAILABLE", payload["entries"][0]["issues"])

    def test_duplicate_tasks_rejected(self):
        self.checkpoint()
        self.config["tasks"].append(dict(self.config["tasks"][0]))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TASK"):
            generate(self.config, self.root / "report")

    def test_no_report_inside_state(self):
        self.checkpoint()
        with self.assertRaisesRegex(ValueError, "REPORT_MUST_BE_OUTSIDE"):
            generate(self.config, self.state / "report")


if __name__ == "__main__":
    unittest.main()
