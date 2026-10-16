#!/usr/bin/env python3
"""Offline QA tests. No model CLI, network, signed-runtime writes, or retry."""
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from TAKY_REVIEW_EVIDENCE_QA import _screen_reply, inspect_signed, verify_signed_source_manifest
from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2

ensure_trusted_taky2()
from TAKY2.enforcement import stable_hash

TASK = "b" * 32
RID = "pf:external-review-" + TASK + ":abcd1234"


def receipt(reply, *, exit_code=0, subtype="success", error=False, tamper=False):
    cli_response = {"subtype": subtype, "is_error": error, "result": reply}
    result = {"returncode": exit_code, "stdout": json.dumps(cli_response),
              "stderr": ""}
    digest = stable_hash(result)
    if tamper:
        digest = "incorrect-digest"
    return {
        "preflight_receipts": {
            RID: {"task_id": "external-review-" + TASK, "allowed": True,
                  "call_allowed": True}
        },
        "execution_calls": {
            RID: {"status": "RETURNED", "result": result, "model": "sonnet",
                  "provider": "anthropic", "result_digest": digest}
        }
    }


class ReceiptQATests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / "TOOLS").mkdir()
        (self.root / "TOOLS" / "module.py").write_text(
            "first = 1\nsecond = 2\nthird = 3\n", encoding="utf-8")
        self.repo = str(self.root)
        self.sources = ["TOOLS/module.py"]
        self.repo_patch = patch("TAKY_REVIEW_EVIDENCE_QA.APPROVED_REPOS", frozenset((self.repo,)))
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)

    def signed_fixture(self, *, included=3):
        item = receipt("See TOOLS/module.py:2")
        raw = (self.root / "TOOLS" / "module.py").read_bytes()
        manifest = [{"path": "TOOLS/module.py",
                     "sha256": hashlib.sha256(raw).hexdigest(),
                     "includedLines": included, "totalLines": 3}]
        binding = {"packet_digest": "a" * 20, "source_manifest": manifest}
        call = {"model": "sonnet", "effort": "medium", "context": "delta",
                "expected_calls": 1, "execution_mode": "PACKET_ONLY",
                "packet_digest": binding["packet_digest"],
                "source_manifest": manifest,
                "dry_run_plan": {
                    "expected_calls": 1,
                    "operations": ["one bounded independent review invocation"],
                    "batch_strategy": "single-review-batch",
                    "fallback": "HOLD", "paid_api": False}}
        item["preflight_receipts"][RID]["call_digest"] = stable_hash(call)
        return item, binding

    def test_enforcement_source_packet_to_qa_real_path(self):
        """Same ENFORCEMENT source must survive packet capture and review QA."""
        from TAKY_MODEL_REVIEW_PACKET import make_packet
        folder = self.root / "ENFORCEMENT"
        folder.mkdir()
        (folder / "gate.py").write_text("ALLOWED = False\nREASON = 'HOLD'\n", encoding="utf-8")
        packet, manifest = make_packet(self.root, "Review ENFORCEMENT/gate.py")
        self.assertIn("SOURCE_FILE ENFORCEMENT/gate.py", packet)
        self.assertEqual([m["path"] for m in manifest], ["ENFORCEMENT/gate.py"])
        result = _screen_reply(
            "Disallow at ENFORCEMENT/gate.py:1-2", self.repo,
            ["ENFORCEMENT/gate.py"],
            {"enforcement/gate.py": manifest[0]["includedLines"]},
        )
        self.assertEqual(result["state"], "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
        self.assertEqual(result["invalidCitations"], [])
        bad = _screen_reply(
            "ENFORCEMENT/gate.py:90", self.repo, ["ENFORCEMENT/gate.py"],
            {"enforcement/gate.py": manifest[0]["includedLines"]},
        )
        self.assertEqual(bad["state"], "REVIEW_HAS_SOURCE_CITATION_ERRORS")

    def test_authenticated_source_manifest_binds_signed_call(self):
        item, binding = self.signed_fixture()
        out = inspect_signed(TASK, self.repo, self.sources, item, binding)
        self.assertEqual(out["state"], "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
        self.assertEqual(out["sourceBindingState"],
                         "SIGNED_SOURCE_HASHES_MATCH_CURRENT_FILES")
        self.assertTrue(out["historicalSourceHashBound"])
        self.assertTrue(out["currentFileHashesMatchReview"])
        self.assertFalse(out["historicalSourceSnapshotVerified"])
        self.assertFalse(out["qualityVerified"])

    def test_forged_manifest_cannot_match_signed_receipt(self):
        item, binding = self.signed_fixture()
        binding["source_manifest"][0]["sha256"] = "0" * 64
        self.assertEqual(inspect_signed(TASK, self.repo, self.sources, item, binding)["state"],
                         "SIGNED_CALL_DIGEST_MISMATCH_HOLD")

    def test_file_change_after_review_is_not_treated_as_historic_source(self):
        item, binding = self.signed_fixture()
        (self.root / "TOOLS" / "module.py").write_text("changed = 1\n")
        self.assertEqual(inspect_signed(TASK, self.repo, self.sources, item, binding)["state"],
                         "SOURCE_CHANGED_SINCE_SIGNED_REVIEW_HOLD")

    def test_citation_past_original_packet_excerpt_is_invalid(self):
        item, binding = self.signed_fixture(included=1)
        out = inspect_signed(TASK, self.repo, self.sources, item, binding)
        self.assertEqual(out["state"], "REVIEW_HAS_SOURCE_CITATION_ERRORS")
        self.assertEqual(out["invalidCitations"][0]["reason"],
                         "CITATION_OUTSIDE_SUPPLIED_PACKET_EXCERPT")

    def test_nested_or_foreign_path_cannot_alias_supplied_source(self):
        cases = ("OTHER/TOOLS/module.py:2", "../TOOLS/module.py:2",
                 "C:\\foreign\\TOOLS/module.py:2", "prefixTOOLS/module.py:2")
        for sample in cases:
            with self.subTest(sample=sample):
                report = _screen_reply(sample, self.repo, self.sources)
                self.assertNotEqual(
                    report["state"], "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
                self.assertFalse(report["qualityVerified"])

    def test_wrong_line_detected_against_provided_file(self):
        report = inspect_signed(
            TASK, self.repo, self.sources,
            receipt("See TOOLS/module.py:1062-1065. Correction: lines 2-3."))
        self.assertEqual(report["state"], "REVIEW_HAS_SOURCE_CITATION_ERRORS")
        self.assertEqual(report["citationCount"], 1)
        self.assertEqual(report["invalidCitations"][0]["start"], 1062)
        self.assertFalse(report["qualityVerified"])
        self.assertFalse(report["historicalSourceSnapshotVerified"])
        self.assertNotIn("Correction:", str(report))

    def test_valid_citations_only_screened_not_semantically_verified(self):
        report = inspect_signed(TASK, self.repo, self.sources,
                                receipt("See TOOLS/module.py:2-3"))
        self.assertEqual(report["state"], "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
        self.assertEqual(report["invalidCitations"], [])
        self.assertFalse(report["qualityVerified"])

    def test_no_citation_holds(self):
        report = inspect_signed(TASK, self.repo, self.sources, receipt("Everything passed."))
        self.assertEqual(report["state"], "NO_CHECKABLE_CITATIONS_REVIEW_HOLD")

    def test_citation_to_unprovided_source_rejected(self):
        report = inspect_signed(TASK, self.repo, self.sources,
                                receipt("See TOOLS/other.py:1"))
        self.assertEqual(report["invalidCitations"][0]["reason"], "SOURCE_NOT_IN_REVIEW_PACKET")

    def test_digest_mismatch_fails_closed(self):
        report = inspect_signed(TASK, self.repo, self.sources, receipt("OK", tamper=True))
        self.assertEqual(report["state"], "SIGNED_RESULT_DIGEST_MISMATCH")

    def test_subtype_error_fails_closed(self):
        for subtype, error in (("error", True), ("success", True)):
            with self.subTest(subtype=subtype, error=error):
                report = inspect_signed(
                    TASK, self.repo, self.sources,
                    receipt("See TOOLS/module.py:1", subtype=subtype, error=error))
                self.assertEqual(report["state"], "CLAUDE_RESPONSE_NOT_SUCCESS")

    def test_nonzero_cli_never_accepted(self):
        report = inspect_signed(TASK, self.repo, self.sources,
                                receipt("See TOOLS/module.py:1", exit_code=1))
        self.assertEqual(report["state"], "SIGNED_EXECUTION_NOT_RETURNED")

    def test_no_signed_call_cannot_be_evaluated(self):
        runtime = {"preflight_receipts": {RID: {
            "task_id": "external-review-" + TASK, "allowed": True,
            "call_allowed": True}}, "execution_calls": {}}
        report = inspect_signed(TASK, self.repo, self.sources, runtime)
        self.assertEqual(report["state"], "SIGNED_EXECUTION_NOT_RETURNED")

    def test_unapproved_sources_and_scope_hold(self):
        report = _screen_reply("TOOLS/module.py:1", self.repo, ["../private.py"])
        self.assertEqual(report["state"], "UNAPPROVED_SOURCE_PATH")
        report = _screen_reply("TOOLS/module.py:1", self.repo,
                               ["TOOLS/module.py", "TOOLS/module.py"])
        self.assertEqual(report["state"], "UNAPPROVED_QA_SCOPE")

    def signed_codex_fixture(self):
        runtime, binding = self.signed_fixture()
        result = {"returncode": 0, "stdout": "See TOOLS/module.py:2-3", "stderr": ""}
        record = runtime["execution_calls"][RID]
        record.update({"provider": "openai", "model": "codex", "result": result,
                       "result_digest": stable_hash(result)})
        call = {"model": "codex", "effort": "medium", "context": "delta",
                "expected_calls": 1, "execution_mode": "CODEX_VERIFY_ONLY",
                "packet_digest": binding["packet_digest"],
                "source_manifest": binding["source_manifest"],
                "dry_run_plan": {
                    "expected_calls": 1,
                    "operations": ["one bounded independent review invocation"],
                    "batch_strategy": "single-review-batch",
                    "fallback": "HOLD", "paid_api": False}}
        runtime["preflight_receipts"][RID]["call_digest"] = stable_hash(call)
        return runtime, binding

    def test_codex_signed_review_uses_plain_last_message_and_signed_source(self):
        runtime, binding = self.signed_codex_fixture()
        out = inspect_signed(TASK, self.repo, self.sources, runtime, binding)
        self.assertEqual(out["state"], "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
        self.assertEqual(out["provider"], "Codex")
        self.assertEqual(out["sourceBindingState"], "SIGNED_SOURCE_HASHES_MATCH_CURRENT_FILES")
        self.assertFalse(out["qualityVerified"])

    def test_domain_and_learning_source_citations_are_screened(self):
        for folder, name in (("DOMAIN", "ARCHIGROW_RULE.md"),
                             ("LEARNING", "module.js")):
            with self.subTest(folder=folder):
                target = self.root / folder / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("one\ntwo\n", encoding="utf-8")
                source = f"{folder}/{name}"
                out = _screen_reply(f"See {source}:2", self.repo, [source],
                                    {source.casefold(): 2})
                self.assertEqual(out["state"],
                                 "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
                self.assertEqual(out["invalidCitations"], [])

    def attach_signed_skills(self, runtime, binding, *, model="sonnet"):
        skill_root = self.root / "signed-skills"
        rows = []
        for name in ("authority-check", "cross-model-review"):
            skill = skill_root / name / "SKILL.md"
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text("canonical " + name + "\n", encoding="utf-8")
            rows.append({"name": name, "sha256": hashlib.sha256(skill.read_bytes()).hexdigest()})
        binding["skill_manifest"] = rows
        call = {"model": model, "effort": "medium", "context": "delta",
                "expected_calls": 1,
                "execution_mode": "CODEX_VERIFY_ONLY" if model == "codex" else "PACKET_ONLY",
                "packet_digest": binding["packet_digest"],
                "source_manifest": binding["source_manifest"],
                "skill_manifest": rows,
                "dry_run_plan": {"expected_calls": 1,
                                 "operations": ["one bounded independent review invocation"],
                                 "batch_strategy": "single-review-batch",
                                 "fallback": "HOLD", "paid_api": False}}
        runtime["preflight_receipts"][RID]["call_digest"] = stable_hash(call)
        return skill_root

    def test_skills_are_bound_to_signed_review_and_current_hashes(self):
        runtime, binding = self.signed_fixture()
        root = self.attach_signed_skills(runtime, binding)
        with patch("TAKY_REVIEW_EVIDENCE_QA.SKILL_CANONICAL_ROOT", root):
            out = inspect_signed(TASK, self.repo, self.sources, runtime, binding)
        self.assertEqual(out["state"], "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
        self.assertTrue(out["skillManifestSigned"])
        self.assertTrue(out["skillHashesMatchCurrent"])
        self.assertFalse(out["qualityVerified"])

    def test_changed_skill_bytes_cannot_reuse_signed_receipt(self):
        runtime, binding = self.signed_fixture()
        root = self.attach_signed_skills(runtime, binding)
        (root / "authority-check" / "SKILL.md").write_text("MODIFIED", encoding="utf-8")
        with patch("TAKY_REVIEW_EVIDENCE_QA.SKILL_CANONICAL_ROOT", root):
            out = inspect_signed(TASK, self.repo, self.sources, runtime, binding)
        self.assertEqual(out["state"], "SKILL_CHANGED_SINCE_SIGNED_REVIEW_HOLD")

    def test_missing_signed_skill_manifest_is_not_accepted_as_legacy(self):
        runtime, binding = self.signed_fixture()
        self.attach_signed_skills(runtime, binding)
        binding.pop("skill_manifest")
        out = inspect_signed(TASK, self.repo, self.sources, runtime, binding)
        self.assertEqual(out["state"], "SIGNED_CALL_DIGEST_MISMATCH_HOLD")

    def test_codex_signed_skill_manifest_verifies_independently(self):
        runtime, binding = self.signed_codex_fixture()
        root = self.attach_signed_skills(runtime, binding, model="codex")
        with patch("TAKY_REVIEW_EVIDENCE_QA.SKILL_CANONICAL_ROOT", root):
            out = inspect_signed(TASK, self.repo, self.sources, runtime, binding)
        self.assertEqual(out["provider"], "Codex")
        self.assertTrue(out["skillManifestSigned"])
        self.assertEqual(out["invalidCitations"], [])

    def test_codex_manifest_tamper_is_rejected(self):
        runtime, binding = self.signed_codex_fixture()
        binding["source_manifest"][0]["sha256"] = "0" * 64
        self.assertEqual(inspect_signed(TASK, self.repo, self.sources, runtime, binding)["state"],
                         "SIGNED_CALL_DIGEST_MISMATCH_HOLD")

    def test_unsupported_executor_payload_stays_unverified(self):
        item = receipt("See TOOLS/module.py:1")
        item["execution_calls"][RID]["provider"] = "openai"
        self.assertEqual(inspect_signed(TASK, self.repo, self.sources, item)["state"],
                         "UNSUPPORTED_MODEL_PAYLOAD_FOR_THIS_SCREEN")


if __name__ == "__main__":
    unittest.main()
