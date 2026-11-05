#!/usr/bin/env python3
"""Deterministic tests: no model calls, state writes, or network."""
import unittest

from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
ensure_trusted_taky2()
from TAKY2.enforcement import stable_hash
from TAKY_TARGET_REVIEW_PACKET import attach

TARGET = "pf:fixture:1234567890abcdef"

class TargetReviewPacketTests(unittest.TestCase):
    def base(self):
        result = {"returncode": 0, "stdout": "the actual earlier output", "stderr": ""}
        return {"preflight_receipts": {TARGET: {"authority_digest": "a", "allowed": True}},
                "execution_calls": {TARGET: {"status": "RETURNED",
                                             "result": result,
                                             "result_digest": stable_hash(result)}}}

    def test_exact_target_attached_and_bound(self):
        packet, binding = attach("TASK: verify target\n", self.base(), TARGET)
        self.assertIn("the actual earlier output", packet)
        self.assertEqual(binding["target_result_digest"],
                         self.base()["execution_calls"][TARGET]["result_digest"])
        self.assertEqual(binding["target_receipt_id"], TARGET)

    def test_changed_target_is_not_misrepresented(self):
        scope = self.base()
        scope["execution_calls"][TARGET]["result"]["stdout"] = "changed"
        with self.assertRaisesRegex(ValueError, "NOT_INTEGRITY_BOUND"):
            attach("TASK review", scope, TARGET)

    def test_missing_or_oversize_target_holds(self):
        with self.assertRaisesRegex(ValueError, "NOT_FOUND"):
            attach("TASK review", self.base(), "pf:missing:00000000")
        scope = self.base()
        scope["execution_calls"][TARGET]["result"]["stdout"] = "large" * 4000
        scope["execution_calls"][TARGET]["result_digest"] = stable_hash(
            scope["execution_calls"][TARGET]["result"])
        with self.assertRaisesRegex(Exception, "too large"):
            attach("TASK review", scope, TARGET)

    def test_insertion_cannot_repeat(self):
        packet, _ = attach("TASK review", self.base(), TARGET)
        with self.assertRaisesRegex(ValueError, "ALREADY_HAS_RESULT"):
            attach(packet, self.base(), TARGET)

if __name__ == "__main__":
    unittest.main()
