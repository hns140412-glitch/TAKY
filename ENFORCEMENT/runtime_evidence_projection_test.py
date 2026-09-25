#!/usr/bin/env python3
import unittest

from runtime_evidence_projection import project


class RuntimeEvidenceProjectionTest(unittest.TestCase):
    def test_success_is_compact(self):
        result = project({
            "pass": True,
            "authorized_to_continue": True,
            "route": {"role": "ORCHESTRATOR"},
            "claim_ceiling": "CONTROLLED_REPOSITORY_RUNTIME",
            "runtime_state": {"large": "payload"},
            "detected": [],
        })
        self.assertEqual(result["projection_mode"], "SUCCESS_COMPACT")
        self.assertNotIn("runtime_state", result)
        self.assertNotIn("detected", result)
        self.assertTrue(result["full_result_preserved"])

    def test_failure_keeps_diagnostics(self):
        result = project({
            "pass": False,
            "authorized_to_continue": False,
            "detected": ["CHECK_FAILED"],
            "runtime_state": {"task_id": "x"},
            "route": None,
            "claim_ceiling": "CONTROLLED_REPOSITORY_RUNTIME",
        })
        self.assertEqual(result["projection_mode"], "FAILURE_DIAGNOSTIC")
        self.assertEqual(result["detected"], ["CHECK_FAILED"])
        self.assertIn("runtime_state", result)
        self.assertTrue(result["full_result_preserved"])


if __name__ == "__main__":
    unittest.main()
