#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from active_rule_profile_freshness_validator import (
    PROFILE_ATTESTATION_VERSION,
    PROFILE_BINDING_ROLE,
    PROFILE_REVIEW_BASIS,
    PROFILE_REVIEWER_ROLE,
    REQUIRED_OWNER_PATHS,
    _canonical_object_hash,
    owner_fingerprint,
    projection_body_hash,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE_KEY = "PROJECTIONS/ACTIVE_RULE_PROFILE.md"


class ActiveRuleProfileFreshnessValidatorTest(unittest.TestCase):
    def fixture(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        for rel in REQUIRED_OWNER_PATHS:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if rel == "MASTER/RULE_REGISTRY.json":
                p.write_text(
                    json.dumps(
                        {
                            "registry_version": "test",
                            "purpose": "test registry",
                            "rules": [],
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            else:
                p.write_text(f"owner:{rel}", encoding="utf-8")

        (root / "PROJECTIONS").mkdir(exist_ok=True)
        paths = sorted(REQUIRED_OWNER_PATHS)
        fp, failures = owner_fingerprint(root, paths)
        self.assertEqual(failures, [])

        profile = root / PROFILE_KEY
        profile.write_text(
            "\n".join([
                "# TAKY ACTIVE RULE PROFILE",
                "",
                "[TAKY_ACTIVE_RULE_PROFILE]",
                "PROFILE_VERSION: test",
                "SOURCE_REPOSITORY: test/repo",
                "SOURCE_CANONICAL_HEAD: abc123",
                "SOURCE_STATE: WORKTREE_DERIVED",
                "SOURCE_OWNER_PATHS: " + ";".join(paths),
                f"SOURCE_OWNER_FINGERPRINT: {fp}",
                "GENERATED_AT: 2026-10-04T00:00:00+09:00",
                "STATUS: DERIVED_EXECUTION_PROJECTION / NON_SEMANTIC_OWNER",
                "",
                "## Always-on execution rules",
                "1. RESULT FIRST",
                "Canonical projected guidance.",
                "",
                "END_TAKY_ACTIVE_RULE_PROFILE",
            ]) + "\n",
            encoding="utf-8",
        )
        body_hash = projection_body_hash(profile.read_text(encoding="utf-8"))

        attestation_dir = root / "HISTORY" / "PROJECTION_ATTESTATIONS"
        attestation_dir.mkdir(parents=True, exist_ok=True)
        receipt = {
            "attestation_version": PROFILE_ATTESTATION_VERSION,
            "binding_role": PROFILE_BINDING_ROLE,
            "profile_path": PROFILE_KEY,
            "source_owner_fingerprint": fp,
            "projection_body_hash": body_hash,
            "source_canonical_head": "abc123",
            "review_basis": PROFILE_REVIEW_BASIS,
            "reviewer_role": PROFILE_REVIEWER_ROLE,
            "review_result": "PASS",
            "reviewed_at": "2026-10-04T00:00:01+09:00",
        }
        receipt["attestation_hash"] = _canonical_object_hash(receipt)
        receipt_path = attestation_dir / "active_rule_profile_test.json"
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt_sha = "sha256:" + hashlib.sha256(receipt_path.read_bytes()).hexdigest()

        registry_path = root / "MASTER" / "RULE_REGISTRY.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["projection_bindings"] = {
            PROFILE_KEY: {
                "source_owner_fingerprint": fp,
                "projection_body_hash": body_hash,
                "binding_role": PROFILE_BINDING_ROLE,
                "review_attestation_ref": receipt_path.relative_to(root).as_posix(),
                "review_attestation_sha256": receipt_sha,
            }
        }
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        fp_after, failures = owner_fingerprint(root, paths)
        self.assertEqual(failures, [])
        self.assertEqual(fp_after, fp)
        return td, root, profile

    def test_current_repository_profile_passes(self):
        result = validate(ROOT, ROOT / PROFILE_KEY)
        self.assertTrue(result["pass"], result)

    def test_matching_head_fingerprint_and_attestation_pass(self):
        td, root, profile = self.fixture()
        try:
            result = validate(root, profile, current_head="abc123")
            self.assertTrue(result["pass"], result)
        finally:
            td.cleanup()

    def test_owner_change_is_stale(self):
        td, root, profile = self.fixture()
        try:
            target = root / "TAKY.md"
            target.write_text("changed", encoding="utf-8")
            result = validate(root, profile, current_head="abc123")
            self.assertIn("ACTIVE_RULE_PROFILE_OWNER_FINGERPRINT_STALE", result["detected"])
            self.assertIn("ACTIVE_RULE_PROFILE_SOURCE_ATTESTATION_MISMATCH", result["detected"])
        finally:
            td.cleanup()

    def test_head_change_without_ancestor_proof_is_stale(self):
        td, root, profile = self.fixture()
        try:
            result = validate(root, profile, current_head="def456")
            self.assertIn("ACTIVE_RULE_PROFILE_BASE_HEAD_STALE", result["detected"])
        finally:
            td.cleanup()

    def test_missing_owner_file_fails(self):
        td, root, profile = self.fixture()
        try:
            rel = "TAKY.md"
            (root / rel).unlink()
            result = validate(root, profile, current_head="abc123")
            self.assertIn(f"ACTIVE_RULE_PROFILE_OWNER_MISSING:{rel}", result["detected"])
        finally:
            td.cleanup()

    def test_projection_cannot_remove_required_owner_and_rehash_remaining(self):
        td, root, profile = self.fixture()
        try:
            missing = "MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md"
            remaining = sorted(REQUIRED_OWNER_PATHS - {missing})
            fp, failures = owner_fingerprint(root, remaining)
            self.assertEqual(failures, [])
            text = profile.read_text(encoding="utf-8")
            lines = []
            for line in text.splitlines():
                if line.startswith("SOURCE_OWNER_PATHS:"):
                    line = "SOURCE_OWNER_PATHS: " + ";".join(remaining)
                elif line.startswith("SOURCE_OWNER_FINGERPRINT:"):
                    line = f"SOURCE_OWNER_FINGERPRINT: {fp}"
                lines.append(line)
            profile.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = validate(root, profile, current_head="abc123")
            self.assertIn(
                f"ACTIVE_RULE_PROFILE_REQUIRED_OWNER_MISSING:{missing}",
                result["detected"],
            )
        finally:
            td.cleanup()

    def test_duplicate_metadata_header_fails(self):
        td, root, profile = self.fixture()
        try:
            profile.write_text(
                profile.read_text(encoding="utf-8") + "PROFILE_VERSION: forged\n",
                encoding="utf-8",
            )
            result = validate(root, profile, current_head="abc123")
            self.assertIn(
                "ACTIVE_RULE_PROFILE_HEADER_DUPLICATE:PROFILE_VERSION",
                result["detected"],
            )
        finally:
            td.cleanup()

    def test_profile_body_change_requires_new_registry_attestation(self):
        td, root, profile = self.fixture()
        try:
            text = profile.read_text(encoding="utf-8")
            profile.write_text(
                text.replace("Canonical projected guidance.", "Stale or forged guidance."),
                encoding="utf-8",
            )
            result = validate(root, profile, current_head="abc123")
            self.assertIn(
                "ACTIVE_RULE_PROFILE_BODY_ATTESTATION_MISMATCH",
                result["detected"],
            )
        finally:
            td.cleanup()

    def test_inline_binding_refresh_cannot_replace_review_attestation(self):
        td, root, profile = self.fixture()
        try:
            (root / "TAKY.md").write_text("new reviewed-owner candidate", encoding="utf-8")
            paths = sorted(REQUIRED_OWNER_PATHS)
            new_fp, failures = owner_fingerprint(root, paths)
            self.assertEqual(failures, [])
            text = profile.read_text(encoding="utf-8")
            lines = []
            for line in text.splitlines():
                if line.startswith("SOURCE_OWNER_FINGERPRINT:"):
                    line = f"SOURCE_OWNER_FINGERPRINT: {new_fp}"
                lines.append(line)
            profile.write_text(
                ("\n".join(lines) + "\n").replace(
                    "Canonical projected guidance.",
                    "Updated projected guidance without review receipt.",
                ),
                encoding="utf-8",
            )
            new_body = projection_body_hash(profile.read_text(encoding="utf-8"))
            registry_path = root / "MASTER" / "RULE_REGISTRY.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            binding = registry["projection_bindings"][PROFILE_KEY]
            binding["source_owner_fingerprint"] = new_fp
            binding["projection_body_hash"] = new_body
            registry_path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = validate(root, profile, current_head="abc123")
            self.assertNotIn("ACTIVE_RULE_PROFILE_OWNER_FINGERPRINT_STALE", result["detected"])
            self.assertNotIn("ACTIVE_RULE_PROFILE_BODY_ATTESTATION_MISMATCH", result["detected"])
            self.assertIn(
                "ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_OWNER_MISMATCH",
                result["detected"],
            )
            self.assertIn(
                "ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_BODY_MISMATCH",
                result["detected"],
            )
        finally:
            td.cleanup()

    def test_metadata_fingerprint_refresh_alone_cannot_hide_owner_change(self):
        td, root, profile = self.fixture()
        try:
            (root / "TAKY.md").write_text("new canonical owner content", encoding="utf-8")
            paths = sorted(REQUIRED_OWNER_PATHS)
            new_fp, failures = owner_fingerprint(root, paths)
            self.assertEqual(failures, [])
            text = profile.read_text(encoding="utf-8")
            lines = [
                f"SOURCE_OWNER_FINGERPRINT: {new_fp}"
                if line.startswith("SOURCE_OWNER_FINGERPRINT:")
                else line
                for line in text.splitlines()
            ]
            profile.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = validate(root, profile, current_head="abc123")
            self.assertNotIn(
                "ACTIVE_RULE_PROFILE_OWNER_FINGERPRINT_STALE",
                result["detected"],
            )
            self.assertIn(
                "ACTIVE_RULE_PROFILE_SOURCE_ATTESTATION_MISMATCH",
                result["detected"],
            )
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
