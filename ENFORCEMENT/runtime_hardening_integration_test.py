#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path

from runtime_orchestrator import run


ROOT = Path(__file__).resolve().parents[1]
BASE_FIXTURE = ROOT / "ENFORCEMENT" / "fixtures" / "runtime_orchestrator_pass.json"


def base_record():
    return json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))


def codes(result, prefix):
    return [x for x in result.get("detected", []) if str(x).startswith(prefix)]


class RuntimeHardeningIntegrationTest(unittest.TestCase):
    def test_context_firewall_blocks_bulk_parent_context(self):
        record = base_record()
        record["worker_context"] = {
            "isolated": True,
            "allowed_context_refs": ["CURRENT:task"],
            "return_fields": ["finding"],
            "full_chat_history": ["do not forward"],
        }
        result = run(record, ROOT, None)
        self.assertTrue(
            codes(result, "CONTEXT_FIREWALL_FORBIDDEN_BULK_CONTEXT"),
            result.get("detected"),
        )

    def test_context_firewall_accepts_bounded_context(self):
        record = base_record()
        record["worker_context"] = {
            "isolated": True,
            "allowed_context_refs": ["CURRENT:task"],
            "return_fields": ["finding", "evidence_ref"],
        }
        result = run(record, ROOT, None)
        self.assertEqual(codes(result, "CONTEXT_FIREWALL_"), [])

    def test_synthesis_barrier_blocks_missing_child(self):
        record = base_record()
        record["synthesis_barrier"] = {
            "required": True,
            "expected_children": ["research-a", "research-b"],
            "child_results": [
                {
                    "child_id": "research-a",
                    "status": "COMPLETED",
                    "structured_result": {"finding": "a"},
                }
            ],
        }
        result = run(record, ROOT, None)
        self.assertIn(
            "SYNTHESIS_CHILD_RESULTS_INCOMPLETE:research-b",
            result.get("detected", []),
        )

    def test_synthesis_barrier_accepts_all_structured_children(self):
        record = base_record()
        record["synthesis_barrier"] = {
            "required": True,
            "expected_children": ["research-a", "research-b"],
            "child_results": [
                {
                    "child_id": "research-a",
                    "status": "COMPLETED",
                    "structured_result": {"finding": "a"},
                },
                {
                    "child_id": "research-b",
                    "status": "COMPLETED",
                    "structured_result": {"finding": "b"},
                },
            ],
        }
        result = run(record, ROOT, None)
        self.assertEqual(codes(result, "SYNTHESIS_"), [])
        barrier = result.get("synthesis_barrier") or {}
        self.assertTrue(barrier.get("synthesis_ready"))

    def test_untrusted_source_blocks_privileged_action_without_clearance(self):
        record = base_record()
        record["action_class"] = "IMPLEMENTATION_WRITE"
        record["source_trust_class"] = "PUBLIC_WEB"
        result = run(record, ROOT, None)
        self.assertIn(
            "UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE",
            result.get("detected", []),
        )

    def test_validator_clearance_removes_quarantine_block(self):
        record = base_record()
        record["action_class"] = "IMPLEMENTATION_WRITE"
        record["source_trust_class"] = "PUBLIC_WEB"
        record["quarantine_clearance"] = {
            "authority": "VALIDATOR",
            "evidence_ref": "INDEX:verified-source-1",
            "verified": True,
        }
        result = run(record, ROOT, None)
        self.assertNotIn(
            "UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE",
            result.get("detected", []),
        )
        quarantine = result.get("source_quarantine") or {}
        self.assertTrue(quarantine.get("cleared"))


if __name__ == "__main__":
    unittest.main()
