#!/usr/bin/env python3
import unittest
from pathlib import Path

import runtime_orchestrator as ro


def state_record(action, trust, clearance=None):
    record = {
        "task_id": "quarantine-test",
        "action_class": action,
        "execution_owner": "CODEX",
        "source_trust_class": trust,
        "working_model": {
            "primary_outcome": "bounded execution",
            "priority_order": ["safe"],
            "execution_implications": ["respect quarantine"],
            "rule_to_execution": ["untrusted reader != privileged actor"],
            "next_action": "continue",
            "stop_conditions": ["quarantine"],
            "protected_state": [],
        },
    }
    if clearance is not None:
        record["quarantine_clearance"] = clearance
    return record


class UntrustedReaderQuarantineTest(unittest.TestCase):
    def test_constants_cover_privileged_actions(self):
        self.assertIn("GOVERNANCE_WRITE", ro.PRIVILEGED_ACTIONS)
        self.assertIn("IMPLEMENTATION_WRITE", ro.PRIVILEGED_ACTIONS)
        self.assertIn("IMPLEMENTATION_EXECUTE", ro.PRIVILEGED_ACTIONS)

    def test_untrusted_external_class_is_quarantined(self):
        self.assertIn("UNTRUSTED_EXTERNAL", ro.UNTRUSTED_SOURCE_CLASSES)

    def test_runtime_state_preserves_source_trust_class(self):
        state, failures = ro.derive_runtime_state(
            state_record("IMPLEMENTATION_WRITE", "UNTRUSTED_EXTERNAL")
        )
        self.assertEqual(failures, [])
        self.assertEqual(state["source_trust_class"], "UNTRUSTED_EXTERNAL")

    def test_orchestrator_has_validator_clearance_contract(self):
        source = Path(ro.__file__).read_text(encoding="utf-8")
        self.assertIn("UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE", source)
        self.assertIn('== "VALIDATOR"', source)
        self.assertIn('clearance.get("verified") is True', source)
        self.assertIn('"source_quarantine": quarantine_result', source)


if __name__ == "__main__":
    unittest.main()
