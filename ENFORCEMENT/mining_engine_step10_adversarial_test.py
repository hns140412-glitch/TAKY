#!/usr/bin/env python3
import unittest

from mining_engine_step10_adversarial import run_adversarial


def c(file_id, assessed, review, through, cont, schema="UTIL", role="UTILIZATION"):
    return {
        "file_id": file_id,
        "schema": schema,
        "semantic_role": role,
        "state_fingerprint": {
            "assessed_count": assessed,
            "review_required_count": review,
            "reviewed_through": through,
            "continue_from": cont,
        },
    }


MEMORY = {
    "strategies": [
        {
            "strategy_id": "PROMOTED-LE",
            "task_family": "LEARNING_ENGINE",
            "goal_pattern": "learner mastery scheduling",
            "status": "PROMOTED",
        },
        {
            "strategy_id": "CANDIDATE-LE",
            "task_family": "LEARNING_ENGINE",
            "goal_pattern": "learner mastery scheduling",
            "status": "CANDIDATE",
        },
    ],
    "failures": [
        {
            "failure_id": "FAIL-1",
            "task_family": "LEARNING_ENGINE",
            "route_signature": "search:stale",
            "state": "RESOLVED",
            "new_evidence_required": True,
            "replacement_routes": ["search:official"],
        }
    ],
}


def payload():
    return {
        "current_attacks": [
            {
                "attack_id": "ADV-CURRENT-SEMANTIC-CONFLICT",
                "candidates": [
                    c("a", 10, 2, "CAP-10", "CAP-11", schema="UTIL"),
                    c("b", 11, 1, "CAP-11", "CAP-12", schema="OTHER"),
                ],
                "expected": {
                    "status": "HOLD",
                    "reason": "SEMANTIC_IDENTITY_CONFLICT",
                    "selected_file_id": None,
                },
            },
            {
                "attack_id": "ADV-CURRENT-FINGERPRINT-CONFLICT",
                "candidates": [
                    c("a", 10, 2, "CAP-A", "CAP-11"),
                    c("b", 10, 2, "CAP-B", "CAP-11"),
                ],
                "expected": {
                    "status": "HOLD",
                    "reason": "STATE_FINGERPRINT_CONFLICT",
                    "selected_file_id": None,
                },
            },
            {
                "attack_id": "ADV-CURRENT-BAD-POINTER",
                "candidates": [c("a", 10, 2, "CAP-10", "CAP-11")],
                "explicit_current_pointer": "missing",
                "expected": {
                    "status": "HOLD",
                    "reason": "EXPLICIT_POINTER_NOT_FOUND",
                    "selected_file_id": None,
                },
            },
        ],
        "anticipation_attacks": [
            {
                "attack_id": "ADV-ANTICIPATION-FRONTIER-INFLATION",
                "run": {
                    "KNOWN": ["goal"],
                    "WEAK": ["none"],
                    "UNKNOWN": ["one"],
                    "CONFLICT": ["none"],
                    "FOUNDATION_REQUIREMENTS": ["one"],
                    "ADVANCED_REQUIREMENTS": ["one"],
                    "ALTERNATIVE_PATHS": ["one"],
                    "SEARCH_FRONTIER": [
                        {"id": "needed"},
                        {"id": "noise-1"},
                        {"id": "noise-2"},
                        {"id": "noise-3"},
                    ],
                    "READY_FOR_USER": ["ready"],
                    "research_depth_decision": "D4",
                },
                "gold": {
                    "expected_frontier_ids": ["needed"],
                    "expected_depth": "D1",
                    "ready_for_user": True,
                    "pass_threshold": 0.80,
                    "min_precision": 0.75,
                },
                "should_pass": False,
            },
            {
                "attack_id": "ADV-ANTICIPATION-SHALLOW-CORRECT",
                "run": {
                    "KNOWN": ["sufficient"],
                    "WEAK": ["none"],
                    "UNKNOWN": ["none"],
                    "CONFLICT": ["none"],
                    "FOUNDATION_REQUIREMENTS": ["existing"],
                    "ADVANCED_REQUIREMENTS": ["none"],
                    "ALTERNATIVE_PATHS": ["none"],
                    "SEARCH_FRONTIER": [],
                    "READY_FOR_USER": ["ready"],
                    "research_depth_decision": "D0",
                },
                "gold": {
                    "expected_frontier_ids": [],
                    "expected_depth": "D0",
                    "ready_for_user": True,
                    "pass_threshold": 0.80,
                    "min_precision": 0.75,
                },
                "should_pass": True,
            },
        ],
        "memory": MEMORY,
        "memory_attacks": [
            {
                "attack_id": "ADV-MEMORY-CANDIDATE-NOT-AUTO-PROMOTED",
                "task": {
                    "task_family": "ARCHITECTURE_WORK",
                    "goal": "learner mastery scheduling",
                },
                "expected": {
                    "next_action": "PLAN_WITHOUT_MEMORY_PRIOR",
                    "authority_guard.memory_can_override_current": False,
                    "authority_guard.memory_can_override_source_authority": False,
                },
            },
            {
                "attack_id": "ADV-MEMORY-FAILED-ROUTE-BLOCK",
                "task": {
                    "task_family": "LEARNING_ENGINE",
                    "goal": "learner mastery scheduling",
                    "route_signature": "search:stale",
                },
                "expected": {
                    "next_action": "USE_REPLACEMENT_ROUTE",
                    "authority_guard.memory_can_override_current": False,
                    "authority_guard.memory_can_override_source_authority": False,
                },
            },
            {
                "attack_id": "ADV-MEMORY-CROSS-FAMILY-NO-LEAK",
                "task": {
                    "task_family": "PRODUCT_UI",
                    "goal": "screen hierarchy",
                    "route_signature": "search:stale",
                },
                "expected": {
                    "next_action": "PLAN_WITHOUT_MEMORY_PRIOR",
                    "authority_guard.memory_can_override_current": False,
                    "authority_guard.memory_can_override_source_authority": False,
                },
            },
        ],
    }


class Step10AdversarialTest(unittest.TestCase):
    def test_adversarial_suite_passes(self):
        result = run_adversarial(payload())
        self.assertTrue(result["pass"])
        self.assertEqual(result["failed"], [])
        self.assertEqual(result["total"], 8)

    def test_broken_guard_holds(self):
        p = payload()
        p["current_attacks"][0]["expected"]["reason"] = "SINGLE_CANDIDATE"
        result = run_adversarial(p)
        self.assertFalse(result["pass"])
        self.assertIn("ADV-CURRENT-SEMANTIC-CONFLICT", result["failed"])


if __name__ == "__main__":
    unittest.main()
