#!/usr/bin/env python3
"""Cross-engine negative/positive round trip without promoting any source."""
import unittest
from external_to_learning_loop import process_external_receipt
from learning_orchestrator import orchestrate_learning
from learning_mining_gap_loop import plan_from_learning_gap,requery_learning
from learning_consumer_adapters import to_ready_planner_request

QUERY="science reasoning"
PAYLOAD={
    "evidence_request":{"query":QUERY,"minimum_results":1,"minimum_authority":"OFFICIAL"},
    "context":{"skill_id":"SCIENCE_REASONING"},
    "observations":[{"correct":False},{"correct":False}],
}
RECEIPT={
    "frontier_id":"F1","query":QUERY,"adapter":"WEB",
    "results":[{"url":"https://publisher.example/science","title":"Official science reasoning",
                "source_class":"OFFICIAL","claim":QUERY}],
}

class MiningIndexLearningRoundTrip(unittest.TestCase):
    def test_no_index_owner_receipt_no_usable_learning_action(self):
        before=orchestrate_learning({**PAYLOAD,"index_rows":[]})
        self.assertEqual(before["mining_request_candidate"]["query"],QUERY)
        plan=plan_from_learning_gap(before,index_rows=[])
        self.assertTrue(plan["mining_required"])
        self.assertIn(QUERY,plan["mining_task"]["goal"])
        discovered=process_external_receipt(RECEIPT,[],PAYLOAD)
        self.assertTrue(discovered["accepted"])
        self.assertEqual(discovered["projection_added"],1)
        after=discovered["learning_requery"]["learning_result"]
        self.assertFalse(after["retrieval"]["evidence_sufficient_for_review"])
        self.assertEqual(after["mining_request_candidate"]["query"],QUERY)
        self.assertFalse(to_ready_planner_request(after)["accepted_for_planner"])
        self.assertEqual(after["runtime"]["next_learning_action"]["action"],"NO_LEARNING_ACTION")
        self.assertFalse(discovered["validation"]["results"][0]["promotion_allowed"])
        self.assertTrue(discovered["guards"]["canonical_index_unchanged"])

    def test_independently_supplied_owner_row_can_be_reviewed_without_schedule_write(self):
        # Represents a separate, pre-verified owner receipt. The discovery
        # adapter itself never creates or upgrades this authoritative row.
        row={"source_id":"S-REVIEWED","canonical_title":"Official science reasoning",
             "short_summary":QUERY,"authority_class":"OFFICIAL",
             "index_state":"INDEXED","authorization_class":"READY_WITH_GUARDS",
             "locator":"https://publisher.example/science"}
        after=requery_learning(PAYLOAD,[row])["learning_result"]
        self.assertTrue(after["retrieval"]["evidence_sufficient_for_review"])
        self.assertEqual(after["runtime"]["strategy_selection"]["strategy"],"TARGETED_REMEDIATION")
        ready=to_ready_planner_request(after)
        self.assertTrue(ready["accepted_for_planner"])
        self.assertIsNone(ready["planner_date"])

if __name__=="__main__":
    unittest.main()
