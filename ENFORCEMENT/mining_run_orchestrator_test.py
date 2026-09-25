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

    def test_index_first_resolves_and_reduces_external_frontier(self):
        rows=[{"source_id":"IDX-1","canonical_title":"Official fraction standard","short_summary":"fraction standard","keywords":["fraction","standard"],"authority_class":"OFFICIAL"}]
        r=orchestrate({"task":{"task_family":"LEARNING_ENGINE","goal":"check evidence","unknown":["fraction standard","decimal intervention"]},"memory":MEMORY,"index_rows":rows})
        self.assertEqual(r["plan"]["index_first"]["counts"]["resolved_from_index"],1)
        self.assertEqual(r["plan"]["index_first"]["counts"]["external_required"],1)
        self.assertEqual(len(r["plan"]["external_search_frontier"]),1)
        self.assertTrue(r["plan"]["external_search_required"])

    def test_index_first_can_eliminate_external_search(self):
        rows=[{"source_id":"IDX-1","canonical_title":"Fresh official evidence","short_summary":"fresh official evidence","keywords":["fresh","evidence"],"authority_class":"OFFICIAL"}]
        r=orchestrate({"task":{"task_family":"LEARNING_ENGINE","goal":"verify","unknown":["fresh evidence"]},"memory":MEMORY,"index_rows":rows})
        self.assertFalse(r["plan"]["external_search_required"])
        self.assertEqual(r["plan"]["external_search_frontier"],[])

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

    def test_outcome_growth_proposal_is_advisory(self):
        r=orchestrate({"task":{"task_family":"PRODUCT_UI","goal":"find reference","route_signature":"search:web"},"memory":MEMORY,"outcome":{"success":True,"accuracy":1,"usefulness":1,"completeness":1,"efficiency":1,"user_correction_rate":0}})
        g=r["growth_proposal"]
        self.assertEqual(g["proposal"]["status"],"CANDIDATE")
        self.assertFalse(g["proposal"]["promotion_allowed"])

if __name__=="__main__": unittest.main()
