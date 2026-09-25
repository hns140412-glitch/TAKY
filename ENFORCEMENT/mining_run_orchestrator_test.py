#!/usr/bin/env python3
import unittest
from mining_run_orchestrator import orchestrate

MEMORY={"strategies":[{"strategy_id":"S1","task_family":"LEARNING_ENGINE","goal_pattern":"adaptive mastery scheduling","status":"PROMOTED"}],"failures":[{"failure_id":"F1","task_family":"LEARNING_ENGINE","route_signature":"search:stale","state":"RESOLVED","new_evidence_required":True,"replacement_routes":["search:official"]}]}

class OrchestratorTest(unittest.TestCase):
    def test_d0_no_frontier(self):
        r=orchestrate({"task":{"task_family":"PRODUCT_UI","goal":"use known approved state","max_research_depth":"D4","known_complete":True},"memory":MEMORY})
        self.assertEqual(r["plan"]["research_depth_decision"],"D0")
        self.assertEqual(r["plan"]["search_frontier"],[])
        self.assertTrue(r["plan"]["execution_allowed"])

    def test_auto_goal_decomposition_starts_research(self):
        r=orchestrate({"task":{"task_family":"GENERAL_RESEARCH","goal":"compare implementation approaches"},"memory":MEMORY})
        self.assertEqual(r["plan"]["research_depth_decision"],"D1")
        self.assertTrue(r["plan"]["search_frontier"])
        self.assertEqual(r["plan"]["search_frontier"][0]["origin"],"GENERIC_SCAFFOLD")

    def test_failed_route_uses_replacement(self):
        r=orchestrate({"task":{"task_family":"LEARNING_ENGINE","goal":"adaptive mastery scheduling","route_signature":"search:stale","unknown":["fresh evidence"]},"memory":MEMORY})
        self.assertEqual(r["plan"]["next_action"],"USE_REPLACEMENT_ROUTE")
        self.assertEqual(r["plan"]["selected_route"],"search:official")
        self.assertTrue(r["plan"]["execution_allowed"])

    def test_depth_and_frontier_bounded(self):
        r=orchestrate({"task":{"task_family":"ARCHITECTURE_WORK","goal":"verify current rules","unknown":["u1","u2"],"conflict":["c1"],"advanced_requirements":["a1"],"freshness_required":True,"max_research_depth":"D2"},"memory":MEMORY})
        self.assertEqual(r["plan"]["research_depth_decision"],"D2")
        self.assertLessEqual(len(r["plan"]["search_frontier"]),4)

    def test_success_only_proposes_candidate(self):
        r=orchestrate({"task":{"task_family":"LEARNING_ENGINE","goal":"adaptive mastery scheduling","route_signature":"search:official"},"memory":MEMORY,"execution_receipt":{"success":True,"route_signature":"search:official"}})
        p=r["memory_learning_proposal"]
        self.assertEqual(p["status"],"CANDIDATE")
        self.assertFalse(p["promotion_allowed"])
        self.assertFalse(r["authority_guard"]["memory_auto_promotion"])

    def test_failure_proposal_does_not_auto_resolve(self):
        r=orchestrate({"task":{"task_family":"PRODUCT_UI","goal":"find motion reference","route_signature":"search:x"},"memory":MEMORY,"execution_receipt":{"success":False,"failure_reason":"NO_EVIDENCE","route_signature":"search:x"}})
        p=r["memory_learning_proposal"]
        self.assertEqual(p["action"],"PROPOSE_FAILURE_OBSERVATION")
        self.assertEqual(p["status"],"OPEN")
        self.assertFalse(r["authority_guard"]["failure_auto_resolution"])

if __name__=="__main__": unittest.main()
