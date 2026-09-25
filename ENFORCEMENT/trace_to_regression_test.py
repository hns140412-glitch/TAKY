#!/usr/bin/env python3
import unittest

from trace_to_regression import build_case


class TraceToRegressionTest(unittest.TestCase):
    def test_confirmed_failure_creates_candidate_case(self):
        result = build_case({
            "outcome_state": "FAILED_CONFIRMED",
            "task_family": "RUNTIME",
            "invariant": "validator_called",
            "expected": True,
            "observed": False,
            "source_ref": "TRACE:run-1",
        })
        self.assertTrue(result["pass"], result["detected"])
        case = result["regression_case"]
        self.assertEqual(case["status"], "CANDIDATE")
        self.assertFalse(case["auto_promote"])
        self.assertEqual(case["source_outcome_state"], "FAILED_CONFIRMED")

    def test_unknown_outcome_cannot_become_regression_case(self):
        result = build_case({
            "outcome_state": "OUTCOME_UNKNOWN",
            "task_family": "RUNTIME",
            "invariant": "validator_called",
            "expected": True,
            "observed": False,
            "source_ref": "TRACE:run-2",
        })
        self.assertFalse(result["pass"])
        self.assertIn(
            "REGRESSION_SOURCE_NOT_CONFIRMED_FAILURE",
            result["detected"],
        )

    def test_missing_provenance_fails_closed(self):
        result = build_case({
            "outcome_state": "REGRESSION_FAIL",
            "task_family": "RUNTIME",
            "invariant": "no_blind_retry",
            "expected": True,
            "observed": False,
        })
        self.assertFalse(result["pass"])
        self.assertIn("REGRESSION_SOURCE_MISSING:source_ref", result["detected"])


if __name__ == "__main__":
    unittest.main()
