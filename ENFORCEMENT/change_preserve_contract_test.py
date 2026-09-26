#!/usr/bin/env python3
import unittest

from codex_task_contract_builder import build
from codex_task_contract_validator import validate


def base_record():
    return {
        "task_id": "p0-change-preserve",
        "project": "TAKY",
        "repository": "hns140412-glitch/TAKY",
        "base_branch": "taky/mining-indexing-learning-integration-2026-09-25",
        "verified_base_head": "verified-head-placeholder",
        "allowed_change_scope": ["ENFORCEMENT/runtime_orchestrator.py"],
        "acceptance_tests": ["change-preserve-contract"],
        "working_model": {
            "primary_outcome": "Preserve approved state while applying a bounded change.",
            "priority_order": ["preserve", "change", "verify"],
            "execution_implications": ["bounded mutation"],
            "rule_to_execution": ["KEEP YOUR KEY -> preserve scope"],
            "next_action": "build task contract",
            "stop_conditions": ["change/preserve conflict"],
            "protected_state": ["MASTER/MASTER_LOGIC.md"],
        },
    }


class ChangePreserveContractTest(unittest.TestCase):
    def test_builder_maps_protected_state_to_preserve_set(self):
        result = build(base_record())
        self.assertTrue(result["pass"], result["detected"])
        scope = result["task_contract"]["change_scope"]
        self.assertEqual(
            scope["allowed"],
            ["ENFORCEMENT/runtime_orchestrator.py"],
        )
        self.assertEqual(scope["preserve"], ["MASTER/MASTER_LOGIC.md"])

    def test_explicit_preserve_scope_overrides_working_model_fallback(self):
        record = base_record()
        record["preserve_change_scope"] = ["CURRENT/DATA"]
        result = build(record)
        self.assertTrue(result["pass"], result["detected"])
        self.assertEqual(
            result["task_contract"]["change_scope"]["preserve"],
            ["CURRENT/DATA"],
        )

    def test_exact_change_preserve_conflict_fails_closed(self):
        record = base_record()
        record["preserve_change_scope"] = [
            "ENFORCEMENT/runtime_orchestrator.py"
        ]
        result = build(record)
        self.assertFalse(result["pass"])
        self.assertTrue(
            any(x.startswith("CHANGE_PRESERVE_CONFLICT:")
                for x in result["detected"])
        )

    def test_nested_path_conflict_fails_closed(self):
        record = base_record()
        record["allowed_change_scope"] = ["MASTER"]
        record["preserve_change_scope"] = ["MASTER/MASTER_LOGIC.md"]
        result = build(record)
        self.assertFalse(result["pass"])
        self.assertTrue(
            any(x.startswith("CHANGE_PRESERVE_CONFLICT:")
                for x in result["detected"])
        )

    def test_disjoint_scope_passes(self):
        record = base_record()
        result = build(record)
        self.assertEqual(validate(result["task_contract"]), [])


if __name__ == "__main__":
    unittest.main()
