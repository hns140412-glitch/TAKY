#!/usr/bin/env python3
import unittest

from behavioral_eval import evaluate


class BehavioralEvalTest(unittest.TestCase):
    def test_required_true_passes(self):
        result = evaluate(
            {"validation": {"called": True}},
            [{"name": "validator-called", "kind": "REQUIRED_TRUE", "path": "validation.called"}],
        )
        self.assertTrue(result["pass"], result["detected"])

    def test_final_success_does_not_hide_behavior_failure(self):
        result = evaluate(
            {"final_output_pass": True, "validation": {"called": False}},
            [{"name": "validator-called", "kind": "REQUIRED_TRUE", "path": "validation.called"}],
        )
        self.assertFalse(result["pass"])
        self.assertIn("BEHAVIOR_ASSERTION_FAILED:validator-called", result["detected"])
        self.assertEqual(
            result["invariant"],
            "FINAL_OUTPUT_PASS != EXECUTION_PATH_PASS",
        )

    def test_equals_and_contains(self):
        result = evaluate(
            {
                "handoff": {"order": "HIDE_READY_SNAP_READY"},
                "guards": ["authority_rechecked", "no_blind_retry"],
            },
            [
                {
                    "name": "handoff-order",
                    "kind": "EQUALS",
                    "path": "handoff.order",
                    "expected": "HIDE_READY_SNAP_READY",
                },
                {
                    "name": "no-blind-retry",
                    "kind": "CONTAINS",
                    "path": "guards",
                    "expected": "no_blind_retry",
                },
            ],
        )
        self.assertTrue(result["pass"], result["detected"])

    def test_unsupported_assertion_fails_closed(self):
        result = evaluate(
            {"x": True},
            [{"name": "bad", "kind": "RUN_COMMAND", "path": "x"}],
        )
        self.assertFalse(result["pass"])
        self.assertIn("BEHAVIOR_ASSERTION_KIND_UNSUPPORTED:bad", result["detected"])


if __name__ == "__main__":
    unittest.main()
