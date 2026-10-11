#!/usr/bin/env python3
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from result_preview_gate import _canonical_hash, validate_preview, validate_release


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class ResultPreviewGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.result_file = self.root / "result.bin"
        self.result_file.write_bytes(b"revision-a")
        self.preview_file = self.root / "preview.png"
        self.preview_file.write_bytes(b"preview-evidence")

    def record(self):
        return {
            "preview_version": "1.0",
            "task_id": "TASK-1",
            "preview_required": True,
            "result_path": "result.bin",
            "result_revision_hash": sha(self.result_file.read_bytes()),
            "preview_surface": "rendered-result",
            "preview_evidence": [{
                "evidence_path": "preview.png",
                "evidence_sha256": sha(self.preview_file.read_bytes()),
            }],
            "acceptance_result": "PASS",
            "acceptance_method": "CROSS_VALIDATION",
            "reviewer_ref": "validator:test",
        }

    def release_request(self, receipt):
        return {
            "task_id": "TASK-1",
            "result_revision_hash": receipt["result_revision_hash"],
            "preview_receipt_hash": receipt["preview_receipt_hash"],
            "release_target": "production:site",
            "release_payload_hash": sha(b"deploy-payload"),
        }

    def test_valid_preview_passes(self):
        result = validate_preview(self.record(), self.root)
        self.assertTrue(result["pass"], result)
        self.assertTrue(result["release_eligible"])

    def test_preview_requires_concrete_result_path(self):
        record = self.record()
        del record["result_path"]
        result = validate_preview(record, self.root)
        self.assertIn("RESULT_PREVIEW_RESULT_PATH_REQUIRED", result["detected"])

    def test_changed_result_invalidates_preview(self):
        record = self.record()
        self.result_file.write_bytes(b"revision-b")
        result = validate_preview(record, self.root)
        self.assertIn("RESULT_PREVIEW_REVISION_FILE_MISMATCH", result["detected"])

    def test_changed_evidence_invalidates_preview(self):
        record = self.record()
        self.preview_file.write_bytes(b"changed")
        result = validate_preview(record, self.root)
        self.assertTrue(any(x.startswith("RESULT_PREVIEW_EVIDENCE_HASH_MISMATCH") for x in result["detected"]))

    def test_failed_acceptance_blocks(self):
        record = self.record()
        record["acceptance_result"] = "FAIL"
        result = validate_preview(record, self.root)
        self.assertIn("RESULT_PREVIEW_ACCEPTANCE_NOT_PASS", result["detected"])

    def test_not_applicable_can_be_recorded_but_not_released(self):
        record = {
            "preview_version": "1.0",
            "task_id": "TASK-2",
            "preview_required": False,
            "not_applicable_reason": "internal non-release bookkeeping",
            "acceptance_result": "NOT_APPLICABLE",
        }
        result = validate_preview(record, self.root)
        self.assertTrue(result["pass"], result)
        self.assertFalse(result["release_eligible"])

    def test_release_same_revision_passes(self):
        receipt = validate_preview(self.record(), self.root)
        result = validate_release(receipt, self.release_request(receipt), self.root)
        self.assertTrue(result["pass"], result)
        self.assertTrue(result["release_binding_hash"].startswith("sha256:"))

    def test_release_revision_change_is_blocked(self):
        receipt = validate_preview(self.record(), self.root)
        request = self.release_request(receipt)
        request["result_revision_hash"] = sha(b"other-revision")
        result = validate_release(receipt, request, self.root)
        self.assertIn("RESULT_RELEASE_REVISION_MISMATCH", result["detected"])

    def test_release_cannot_use_other_preview_receipt(self):
        receipt = validate_preview(self.record(), self.root)
        request = self.release_request(receipt)
        request["preview_receipt_hash"] = sha(b"other-preview")
        result = validate_release(receipt, request, self.root)
        self.assertIn("RESULT_RELEASE_PREVIEW_RECEIPT_HASH_MISMATCH", result["detected"])

    def test_fabricated_receipt_without_hash_is_rejected(self):
        receipt = {
            "pass": True,
            "preview_required": True,
            "acceptance_result": "PASS",
            "release_eligible": True,
            "task_id": "TASK-1",
            "result_path": "result.bin",
            "result_revision_hash": sha(self.result_file.read_bytes()),
        }
        request = {
            "task_id": "TASK-1",
            "result_revision_hash": receipt["result_revision_hash"],
            "preview_receipt_hash": None,
            "release_target": "production:site",
            "release_payload_hash": sha(b"deploy-payload"),
        }
        result = validate_release(receipt, request, self.root)
        self.assertFalse(result["pass"])
        self.assertIn("RESULT_RELEASE_PREVIEW_RECEIPT_HASH_INVALID", result["detected"])

    def test_tampered_receipt_is_rejected(self):
        receipt = validate_preview(self.record(), self.root)
        self.assertTrue(receipt["pass"])
        tampered = copy.deepcopy(receipt)
        tampered["reviewer_ref"] = "forged:reviewer"
        result = validate_release(tampered, self.release_request(receipt), self.root)
        self.assertIn("RESULT_RELEASE_PREVIEW_RECEIPT_INTEGRITY_MISMATCH", result["detected"])

    def test_self_hashed_fabricated_receipt_without_preview_evidence_is_rejected(self):
        receipt = {
            "pass": True,
            "preview_version": "1.0",
            "task_id": "TASK-1",
            "preview_required": True,
            "result_path": "result.bin",
            "result_revision_hash": sha(self.result_file.read_bytes()),
            "preview_surface": "rendered-result",
            "preview_evidence": [],
            "acceptance_result": "PASS",
            "acceptance_method": "CROSS_VALIDATION",
            "reviewer_ref": "forged:reviewer",
            "release_eligible": True,
        }
        core = {
            "preview_version": receipt["preview_version"],
            "task_id": receipt["task_id"],
            "preview_required": receipt["preview_required"],
            "result_path": receipt["result_path"],
            "result_revision_hash": receipt["result_revision_hash"],
            "preview_surface": receipt["preview_surface"],
            "preview_evidence": receipt["preview_evidence"],
            "acceptance_result": receipt["acceptance_result"],
            "acceptance_method": receipt["acceptance_method"],
            "reviewer_ref": receipt["reviewer_ref"],
        }
        receipt["preview_receipt_hash"] = _canonical_hash(core)
        result = validate_release(receipt, self.release_request(receipt), self.root)
        self.assertFalse(result["pass"])
        self.assertTrue(
            any(
                x.startswith("RESULT_RELEASE_PREVIEW_REVALIDATION:")
                for x in result["detected"]
            )
        )

    def test_result_mutation_after_preview_blocks_release(self):
        receipt = validate_preview(self.record(), self.root)
        request = self.release_request(receipt)
        self.result_file.write_bytes(b"revision-b")
        result = validate_release(receipt, request, self.root)
        self.assertIn("RESULT_RELEASE_RESULT_REVISION_CHANGED", result["detected"])


if __name__ == "__main__":
    unittest.main()
