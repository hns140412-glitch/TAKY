"""Canonical history must be established by the target, not a path prefix."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from evidence_ref_validator import validate_history_relevance, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


class HistoryBoundaryTest(unittest.TestCase):
    def file_manifest(self, path, target):
        return {"history_query_refs": [{
            "source_kind": "repo_file", "source_id": "history-boundary-test",
            "path": path, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }]}

    def test_traversal_with_correct_hash_is_not_history(self):
        for path in ("HISTORY/../TAKY.md", "HISTORY/..\\TAKY.md"):
            with self.subTest(path=path):
                failures = validate_manifest(self.file_manifest(path, ROOT / "TAKY.md"), ROOT)
                self.assertTrue(failures)

    def test_real_history_file_is_accepted(self):
        target = next((ROOT / "HISTORY").glob("*.md"))
        self.assertEqual(validate_manifest(
            self.file_manifest(target.relative_to(ROOT).as_posix(), target), ROOT), [])

    def test_resolved_link_outside_history_is_rejected(self):
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == ROOT / "HISTORY/linked.md":
                return ROOT / "TAKY.md"
            return original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve):
            ok, reason = validate_history_relevance(
                {"source_kind": "repo_file", "path": "HISTORY/linked.md"}, ROOT)
        self.assertFalse(ok)
        self.assertEqual(reason, "HISTORY_PATH_OUTSIDE_CANONICAL_HISTORY")

    def test_commit_traversal_rejected_before_git_lookup(self):
        with patch("evidence_ref_validator.git_ok", return_value=True) as git:
            ok, reason = validate_history_relevance({
                "source_kind": "repo_commit", "commit_sha": "a" * 40,
                "evidence_paths": ["HISTORY/../TAKY.md"],
            }, ROOT)
        self.assertFalse(ok)
        self.assertEqual(reason, "HISTORY_PATH_OUTSIDE_CANONICAL_HISTORY")
        git.assert_not_called()

    def test_commit_history_path_keeps_git_verification(self):
        with patch("evidence_ref_validator.git_ok", return_value=True) as git:
            self.assertTrue(validate_history_relevance({
                "source_kind": "repo_commit", "commit_sha": "a" * 40,
                "evidence_paths": ["HISTORY/record.md"],
            }, ROOT)[0])
        git.assert_called_once_with(ROOT, "cat-file", "-e", "a" * 40 + ":HISTORY/record.md")


if __name__ == "__main__":
    unittest.main()
