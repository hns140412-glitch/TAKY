#!/usr/bin/env python3
import unittest

from strategy_failure_memory import (
    apply_failure_memory,
    prepare_next_run,
    select_strategy,
)

PROMOTED = {
    "strategy_id": "S-GOOD",
    "task_family": "LEARNING_ENGINE",
    "goal_pattern": "adaptive learner mastery review scheduling",
    "status": "PROMOTED",
}
CANDIDATE = {
    "strategy_id": "S-NOT-READY",
    "task_family": "LEARNING_ENGINE",
    "goal_pattern": "adaptive learner mastery",
    "status": "CANDIDATE",
}
FAILURE = {
    "failure_id": "F-001",
    "task_family": "LEARNING_ENGINE",
    "route_signature": "search:stale-endpoint",
    "state": "RESOLVED",
    "new_evidence_required": True,
    "replacement_routes": [
        "search:official-direct",
        "search:alternate-index",
    ],
}


class StrategyFailureMemoryTest(unittest.TestCase):
    def test_promoted_strategy_reused(self):
        result = select_strategy(
            {
                "task_family": "LEARNING_ENGINE",
                "goal": "adaptive mastery scheduling",
            },
            [PROMOTED, CANDIDATE],
        )
        self.assertEqual(result["selected"]["strategy_id"], "S-GOOD")

    def test_candidate_strategy_not_reused(self):
        result = select_strategy(
            {
                "task_family": "LEARNING_ENGINE",
                "goal": "adaptive mastery",
            },
            [CANDIDATE],
        )
        self.assertIsNone(result["selected"])

    def test_known_failed_route_is_blocked(self):
        result = apply_failure_memory(
            {
                "task_family": "LEARNING_ENGINE",
                "route_signature": "search:stale-endpoint",
                "has_new_evidence": False,
                "materially_changed_method": False,
            },
            [FAILURE],
        )
        self.assertTrue(result["blocked"])
        self.assertIn(
            "search:official-direct",
            result["replacement_routes"],
        )

    def test_new_evidence_allows_retry(self):
        result = apply_failure_memory(
            {
                "task_family": "LEARNING_ENGINE",
                "route_signature": "search:stale-endpoint",
                "has_new_evidence": True,
            },
            [FAILURE],
        )
        self.assertFalse(result["blocked"])

    def test_different_family_not_blocked(self):
        result = apply_failure_memory(
            {
                "task_family": "ARCHITECTURE_WORK",
                "route_signature": "search:stale-endpoint",
            },
            [FAILURE],
        )
        self.assertFalse(result["blocked"])

    def test_prepare_next_run_prefers_replacement_when_blocked(self):
        result = prepare_next_run(
            {
                "task_family": "LEARNING_ENGINE",
                "goal": "adaptive mastery scheduling",
                "route_signature": "search:stale-endpoint",
            },
            {
                "strategies": [PROMOTED],
                "failures": [FAILURE],
            },
        )
        self.assertEqual(
            result["next_action"],
            "USE_REPLACEMENT_ROUTE",
        )
        self.assertFalse(
            result["authority_guard"]["memory_can_override_current"]
        )


if __name__ == "__main__":
    unittest.main()
