#!/usr/bin/env python3
"""No-model regression checks for bounded TAKY code-edit application."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from TAKY_SCOPED_EDIT_APPLY import EditRejected, run, sha, extract_proposal

class ScopedEditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="TAKY_EDIT_TEST_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "a.py"
        self.src.write_text("ANSWER = 1\n", encoding="utf-8")
        self.untouched = self.root / "unrelated.py"
        self.untouched.write_text("KEEP = True\n", encoding="utf-8")
        self.task = {"schema": "TAKY_EXECUTION_REQUEST_V1", "mode": "BOUNDED_EDIT_PROPOSAL",
                     "id": "a" * 32, "repo": str(self.root),
                     "no_push": True, "no_deploy": True,
                     "allowed_files": [{"path": "a.py", "sha256": sha(self.src.read_bytes())}]}
        self.proposal = {"task_id": self.task["id"],
                         "edits": [{"path": "a.py", "replacements": [
                             {"old": "ANSWER = 1", "new": "ANSWER = 2"}]}]}

    def test_extract_plain_model_json(self):
        result = extract_proposal(self.task, json.dumps(self.proposal))
        self.assertEqual(result["task_id"], self.task["id"])

    def test_extract_claude_envelope(self):
        envelope = {"type": "result", "is_error": False, "result": json.dumps(self.proposal)}
        self.assertEqual(extract_proposal(self.task, json.dumps(envelope)), self.proposal)

    def test_extract_rejects_unstructured_output(self):
        with self.assertRaisesRegex(EditRejected, "STRICT_JSON"):
            extract_proposal(self.task, "looks fine - please change ANSWER")

    def test_preview_makes_no_changes(self):
        result = run(self.task, self.proposal)
        self.assertEqual(result["status"], "DRY_RUN_VALID")
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_authorized_application(self):
        with patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            result = run(self.task, self.proposal, execute=True)
        self.assertEqual(result["status"], "APPLIED_UNVERIFIED")
        self.assertEqual(self.src.read_text(), "ANSWER = 2\n")
        self.assertEqual(self.untouched.read_text(), "KEEP = True\n")

    def test_unapproved_application_refused(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(EditRejected, "AUTHORIZATION_REQUIRED"):
                run(self.task, self.proposal, execute=True)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_changed_preimage_refused(self):
        self.src.write_text("ANSWER = 5\n", encoding="utf-8")
        with self.assertRaisesRegex(EditRejected, "SOURCE_CHANGED"):
            run(self.task, self.proposal)
        self.assertEqual(self.src.read_text(), "ANSWER = 5\n")

    def test_path_escape_and_unlisted_file_refused(self):
        self.proposal["edits"][0]["path"] = "../unrelated.py"
        with self.assertRaisesRegex(EditRejected, "UNAPPROVED"):
            run(self.task, self.proposal)
        self.proposal["edits"][0]["path"] = "unrelated.py"
        with self.assertRaisesRegex(EditRejected, "UNAPPROVED"):
            run(self.task, self.proposal)

    def test_duplicate_replacement_refused(self):
        self.src.write_text("ANSWER = 1\nANSWER = 1\n", encoding="utf-8")
        self.task["allowed_files"][0]["sha256"] = sha(self.src.read_bytes())
        with self.assertRaisesRegex(EditRejected, "NON_UNIQUE"):
            run(self.task, self.proposal)

    def test_invalid_python_refused(self):
        self.proposal["edits"][0]["replacements"][0]["new"] = "def broken(:"
        with self.assertRaises(SyntaxError):
            run(self.task, self.proposal)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_atomic_validation_two_files(self):
        second = self.root / "b.py"
        second.write_text("OK = 1\n", encoding="utf-8")
        self.task["allowed_files"].append({"path": "b.py", "sha256": sha(second.read_bytes())})
        self.proposal["edits"].append({"path": "b.py", "replacements": [
            {"old": "MISSING", "new": "WRONG"}]})
        with patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            with self.assertRaises(EditRejected):
                run(self.task, self.proposal, execute=True)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")
        self.assertEqual(second.read_text(), "OK = 1\n")

if __name__ == "__main__":
    unittest.main()
