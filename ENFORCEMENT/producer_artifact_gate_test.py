#!/usr/bin/env python3
"""Negative and recovery fixtures for the controlled producer gate."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from producer_artifact_gate import preflight, postflight

class ProducerArtifactGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "source.txt").write_text("Source truth")
        (self.root / "authority.txt").write_text("Approved reference")
        self.contract = dict(kind="spreadsheet", task_id="X", user_intent="Make actual workbook",
            output_path="output.xlsx", source_ref="source.txt", authority_ref="authority.txt",
            protected_state="Original unchanged", acceptance_plan="Check actual semantic/visual result",
            visual_witness_plan="Render every print page", producer="AI")
    def evidence(self):
        output = self.root / "output.xlsx"
        output.write_bytes(b"test workbook representation")
        checks = {}
        for key in ("source_trace", "semantic_check", "regression_check", "delivery_check", "visual_check"):
            p = self.root / (key + ".txt")
            p.write_bytes(b"\\x89PNG\\r\\n\\x1a\\n" + b"sample render") if key == "visual_check" else p.write_text(key + " witness")
            checks[key] = dict(passed=True, evidence_path=p.name, evidence_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        import producer_artifact_gate as gate
        return dict(contract_sha256=gate._digest(self.contract), output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), **checks)

    def test_missing_pre_blocks(self):
        del self.contract["acceptance_plan"]
        self.assertIn("PRE_ACCEPTANCE_PLAN_MISSING", preflight(self.contract, self.root)["detected"])
    def test_pre_after_output_blocks(self):
        (self.root / "output.xlsx").write_bytes(b"already written")
        self.assertIn("PRE_OUTPUT_ALREADY_EXISTS", preflight(self.contract, self.root)["detected"])
    def test_no_visual_evidence_blocks_static_success(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["visual_check"]["passed"] = False
        self.assertIn("POST_VISUAL_CHECK_UNVERIFIED", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_source_semantic_migration_blocks(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["semantic_check"]["passed"] = False
        self.assertIn("POST_SEMANTIC_CHECK_UNVERIFIED", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_user_debugger_blocks(self):
        self.contract["user_as_debugger"] = True
        self.assertIn("USER_AS_QA", preflight(self.contract, self.root)["detected"])
    def test_low_risk_bounded_pass(self):
        self.contract["kind"] = "structured_data"
        receipt = preflight(self.contract, self.root)
        self.assertTrue(receipt["pass"])
        evidence = self.evidence()
        del evidence["visual_check"]
        self.assertTrue(postflight(self.contract, receipt, evidence, self.root)["pass"])
    def test_recovery_and_targeted_recheck(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["visual_check"]["passed"] = False
        self.assertFalse(postflight(self.contract, receipt, evidence, self.root)["pass"])
        evidence["visual_check"]["passed"] = True
        self.assertTrue(postflight(self.contract, receipt, evidence, self.root)["pass"])
    def test_receipt_contract_change_blocks(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        self.contract["user_intent"] = "Changed after preflight"
        self.assertIn("POST_PRE_RECEIPT_INVALID", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_hash_and_missing_witness_block(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["output_sha256"] = "0" * 64
        (self.root / "visual_check.txt").unlink()
        errors = postflight(self.contract, receipt, evidence, self.root)["detected"]
        self.assertIn("POST_OUTPUT_HASH_MISMATCH", errors)
        self.assertIn("POST_VISUAL_CHECK_EVIDENCE_MISSING", errors)
    def test_no_unapproved_complete_claim(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["claim"] = "COMPLETE"
        self.assertIn("HUMAN_APPROVAL_MISSING", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_source_mutation_after_pre_blocks(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        (self.root / "source.txt").write_text("Modified source")
        self.assertIn("POST_SOURCE_REF_CHANGED", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_authority_mutation_after_pre_blocks(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        (self.root / "authority.txt").write_text("Modified approval")
        self.assertIn("POST_AUTHORITY_REF_CHANGED", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_shared_evidence_file_does_not_launder_multiple_checks(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["visual_check"]["evidence_path"] = evidence["semantic_check"]["evidence_path"]
        self.assertIn("POST_VISUAL_CHECK_EVIDENCE_NOT_DISTINCT", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_forged_baseline_free_receipt_blocks(self):
        receipt = preflight(self.contract, self.root)
        del receipt["baseline_hashes"]
        evidence = self.evidence()
        self.assertIn("POST_BASELINE_RECEIPT_MISSING", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_visual_text_cannot_claim_render(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        p = self.root / "visual_check.txt"
        p.write_text("looks good")
        evidence["visual_check"]["evidence_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertIn("POST_VISUAL_CHECK_NOT_RENDER", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_evidence_hash_mismatch_blocks(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        (self.root / "semantic_check.txt").write_text("changed after review")
        self.assertIn("POST_SEMANTIC_CHECK_EVIDENCE_HASH_MISMATCH", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_approval_string_cannot_self_certify_completion(self):
        receipt = preflight(self.contract, self.root)
        evidence = self.evidence()
        evidence["claim"] = "COMPLETE"
        evidence["human_approval_ref"] = "self-reported"
        self.assertIn("INDEPENDENT_RESULT_VALIDATION_NOT_IMPLEMENTED", postflight(self.contract, receipt, evidence, self.root)["detected"])
    def test_path_escape_blocks(self):
        self.contract["output_path"] = "../escape.xlsx"
        self.assertIn("PATH_ESCAPES_ROOT", preflight(self.contract, self.root)["detected"])

if __name__ == "__main__":
    unittest.main()
