#!/usr/bin/env python3
import unittest

from mining_engine_step9_gate import run_gate


def candidate(file_id, assessed, review, modified, schema="UTIL", role="UTILIZATION"):
    return {
        "file_id": file_id,
        "schema": schema,
        "semantic_role": role,
        "state_fingerprint": {
            "assessed_count": assessed,
            "review_required_count": review,
            "reviewed_through": f"CAP-{assessed}",
            "continue_from": f"CAP-{assessed + 1}",
        },
        "modified_time": modified,
    }


MEMORY = {
    "strategies": [
        {
            "strategy_id": "S-PROMOTED",
            "task_family": "LEARNING_ENGINE",
            "goal_pattern": "adaptive learner mastery scheduling",
            "status": "PROMOTED",
        },
        {
            "strategy_id": "S-CANDIDATE",
            "task_family": "LEARNING_ENGINE",
            "goal_pattern": "adaptive learner mastery scheduling",
            "status": "CANDIDATE",
        },
    ],
    "failures": [
        {
            "failure_id": "F-STALE",
            "task_family": "LEARNING_ENGINE",
            "route_signature": "search:stale-endpoint",
            "state": "RESOLVED",
            "new_evidence_required": True,
            "replacement_routes": ["search:official-direct"],
        }
    ],
}


def passing_payload():
    old = candidate("old", 573, 93, "2026-09-24T10:00:00Z")
    new = candidate("new", 622, 44, "2026-09-25T01:00:00Z")
    dup1 = candidate("dup1", 622, 44, "2026-09-25T01:00:00Z")
    dup2 = candidate("dup2", 622, 44, "2026-09-25T02:00:00Z")
    return {
        "current_cases": [
            {
                "case_id": "CUR-PROGRESSION",
                "candidates": [old, new],
                "explicit_current_pointer": "old",
                "expected": {
                    "status": "SELECTED",
                    "reason": "STATE_PROGRESSION_DOMINANCE",
                    "selected_file_id": "new",
                },
            },
            {
                "case_id": "CUR-DUPLICATE",
                "candidates": [dup1, dup2],
                "expected": {
                    "status": "SELECTED",
                    "reason": "DUPLICATE_COLLAPSE_METADATA_TIEBREAK",
                    "selected_file_id": "dup2",
                },
            },
        ],
        "anticipation_suite": {
            "cases": [
                {
                    "case_id": "L5-NEGATIVE-D0",
                    "task_family": "PRODUCT_UI",
                    "run": {
                        "KNOWN": ["goal"],
                        "WEAK": ["none"],
                        "UNKNOWN": ["none"],
                        "CONFLICT": ["none"],
                        "FOUNDATION_REQUIREMENTS": ["existing evidence"],
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
                },
                {
                    "case_id": "L5-FRONTIER-D2",
                    "task_family": "ARCHITECTURE_WORK",
                    "run": {
                        "KNOWN": ["site"],
                        "WEAK": ["one assumption"],
                        "UNKNOWN": ["regulation freshness"],
                        "CONFLICT": ["source mismatch"],
                        "FOUNDATION_REQUIREMENTS": ["current rule"],
                        "ADVANCED_REQUIREMENTS": ["precedent"],
                        "ALTERNATIVE_PATHS": ["official source"],
                        "SEARCH_FRONTIER": [{"id": "official-current-rule"}],
                        "READY_FOR_USER": ["bounded research"],
                        "research_depth_decision": "D2",
                    },
                    "gold": {
                        "expected_frontier_ids": ["official-current-rule"],
                        "expected_depth": "D2",
                        "ready_for_user": True,
                        "pass_threshold": 0.80,
                        "min_precision": 0.75,
                    },
                },
            ]
        },
        "memory": MEMORY,
        "memory_cases": [
            {
                "case_id": "MEM-BLOCK-REPLACE",
                "task": {
                    "task_family": "LEARNING_ENGINE",
                    "goal": "adaptive learner mastery scheduling",
                    "route_signature": "search:stale-endpoint",
                },
                "expected": {"next_action": "USE_REPLACEMENT_ROUTE"},
            },
            {
                "case_id": "MEM-NEW-EVIDENCE",
                "task": {
                    "task_family": "LEARNING_ENGINE",
                    "goal": "adaptive learner mastery scheduling",
                    "route_signature": "search:stale-endpoint",
                    "has_new_evidence": True,
                },
                "expected": {"next_action": "USE_PROMOTED_STRATEGY"},
            },
        ],
    }


class MiningEngineStep9GateTest(unittest.TestCase):
    def test_passing_gate(self):
        result = run_gate(passing_payload())
        self.assertTrue(result["promotion_ready"])
        self.assertEqual(result["promotion_decision"], "PASS_TO_ADVERSARIAL_REVIEW")
        self.assertEqual(result["critical_failures"], [])

    def test_critical_current_regression_blocks(self):
        payload = passing_payload()
        payload["current_cases"][0]["expected"]["selected_file_id"] = "old"
        result = run_gate(payload)
        self.assertFalse(result["promotion_ready"])
        self.assertIn("CURRENT:CUR-PROGRESSION", result["critical_failures"])

    def test_anticipation_failure_blocks(self):
        payload = passing_payload()
        payload["anticipation_suite"]["cases"][1]["run"]["SEARCH_FRONTIER"] = [
            {"id": "wrong-frontier"}, {"id": "inflated-frontier"}
        ]
        result = run_gate(payload)
        self.assertFalse(result["promotion_ready"])
        self.assertIn("ANTICIPATION_SUITE", result["critical_failures"])

    def test_cross_validation_is_order_invariant(self):
        result = run_gate(passing_payload())
        self.assertTrue(all(x["pass"] for x in result["cross_validation"]["results"]))


if __name__ == "__main__":
    unittest.main()
