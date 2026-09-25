#!/usr/bin/env python3
import unittest
from learning_index_bridge import retrieve_learning_evidence

ROWS=[
 {"source_id":"S1","canonical_title":"Official curriculum standard","short_summary":"fraction comparison grade 5","authority_class":"OFFICIAL","source_family":"CURRICULUM"},
 {"source_id":"S2","canonical_title":"Community worksheet","short_summary":"fraction comparison practice","authority_class":"COMMUNITY","source_family":"PRACTICE"},
]

class LearningIndexBridgeTest(unittest.TestCase):
 def test_retrieves_candidates_without_authorizing_use(self):
  out=retrieve_learning_evidence({"request_id":"R1","learning_context":"fraction comparison","query":"fraction comparison","minimum_results":1},ROWS)
  self.assertTrue(out["evidence_sufficient_for_review"])
  self.assertTrue(out["guards"]["retrieval_is_not_pedagogical_authorization"])
  self.assertTrue(out["guards"]["learning_engine_retains_use_decision"])

 def test_authority_filter_can_create_gap(self):
  out=retrieve_learning_evidence({"query":"fraction comparison","minimum_results":2,"minimum_authority":"OFFICIAL","desired_evidence_type":"remediation"},ROWS)
  self.assertFalse(out["evidence_sufficient_for_review"])
  self.assertEqual(out["evidence_gap"]["type"],"LEARNING_EVIDENCE_GAP")
  self.assertEqual(out["evidence_gap"]["existing_evidence_count"],1)

 def test_empty_index_emits_mining_ready_gap(self):
  out=retrieve_learning_evidence({"query":"decimal causal prerequisite","minimum_results":1,"learning_context":"learner error analysis"},[])
  self.assertFalse(out["evidence_sufficient_for_review"])
  self.assertEqual(out["evidence_gap"]["query"],"decimal causal prerequisite")
  self.assertTrue(out["guards"]["gap_may_trigger_mining_only_after_index_check"])

if __name__=="__main__":
 unittest.main()
