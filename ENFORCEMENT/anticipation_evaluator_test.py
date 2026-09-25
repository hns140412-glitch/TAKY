#!/usr/bin/env python3
import unittest

from anticipation_evaluator import evaluate_anticipation


def base_run(frontier, depth="D2", ready=True):
    return {
        "KNOWN": ["k"],
        "WEAK": ["w"],
        "UNKNOWN": ["u"],
        "CONFLICT": ["c"],
        "FOUNDATION_REQUIREMENTS": ["f"],
        "ADVANCED_REQUIREMENTS": ["a"],
        "ALTERNATIVE_PATHS": ["p"],
        "SEARCH_FRONTIER": [{"id": item} for item in frontier],
        "READY_FOR_USER": ["ready"] if ready else [],
        "research_depth_decision": depth,
    }


class AnticipationEvaluatorTest(unittest.TestCase):
    def test_exact_frontier_passes(self):
        result = evaluate_anticipation(
            base_run(["A", "B"]),
            {"expected_frontier_ids": ["A", "B"], "expected_depth": "D2", "ready_for_user": True},
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["frontier_precision"], 1.0)

    def test_frontier_inflation_is_penalized(self):
        result = evaluate_anticipation(
            base_run(["A", "B", "X", "Y", "Z"]),
            {"expected_frontier_ids": ["A", "B"], "expected_depth": "D2", "ready_for_user": True},
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["frontier_inflation"], 3)

    def test_wrong_depth_fails_even_with_good_frontier(self):
        result = evaluate_anticipation(
            base_run(["A"], depth="D4"),
            {"expected_frontier_ids": ["A"], "expected_depth": "D1", "ready_for_user": True},
        )
        self.assertFalse(result["pass"])
        self.assertFalse(result["research_depth_match"])

    def test_d0_can_have_empty_frontier(self):
        result = evaluate_anticipation(
            base_run([], depth="D0"),
            {"expected_frontier_ids": [], "expected_depth": "D0", "ready_for_user": True},
        )
        self.assertTrue(result["pass"])


if __name__ == "__main__":
    unittest.main()
