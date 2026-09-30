#!/usr/bin/env python3
import unittest
from learning_index_bridge import retrieve_learning_evidence
from owner_test_fixture import make_row,verifier_for

ROWS=[
 make_row("S1","Official curriculum standard",short_summary="fraction comparison grade 5",source_family="CURRICULUM"),
 make_row("S2","Community worksheet",short_summary="fraction comparison practice",source_family="PRACTICE",authority_class="COMMUNITY",authorization_class="CONDITIONAL"),
]

class LearningIndexBridgeTest(unittest.TestCase):
 def test_retrieves_candidates_without_authorizing_use(self):
  out=retrieve_learning_evidence({"request_id":"R1","learning_context":"fraction comparison","query":"fraction comparison","minimum_results":1},ROWS,owner_verifier=verifier_for(*ROWS))
  self.assertTrue(out["evidence_sufficient_for_review"])
  self.assertTrue(out["guards"]["retrieval_is_not_pedagogical_authorization"])
  self.assertTrue(out["guards"]["learning_engine_retains_use_decision"])

 def test_authority_filter_can_create_gap(self):
  out=retrieve_learning_evidence({"query":"fraction comparison","minimum_results":2,"minimum_authority":"OFFICIAL","desired_evidence_type":"remediation"},ROWS,owner_verifier=verifier_for(*ROWS))
  self.assertFalse(out["evidence_sufficient_for_review"])
  self.assertEqual(out["evidence_gap"]["type"],"LEARNING_EVIDENCE_GAP")
  self.assertEqual(out["evidence_gap"]["existing_evidence_count"],1)

 def test_empty_index_emits_mining_ready_gap(self):
  out=retrieve_learning_evidence({"query":"decimal causal prerequisite","minimum_results":1,"learning_context":"learner error analysis"},[])
  self.assertFalse(out["evidence_sufficient_for_review"])
  self.assertEqual(out["evidence_gap"]["query"],"decimal causal prerequisite")
  self.assertTrue(out["guards"]["gap_may_trigger_mining_only_after_index_check"])

 def test_staged_candidate_cannot_satisfy_request_or_crowd_out_reviewed(self):
  rows=[
   {"source_id":"NEW","canonical_title":"fraction comparison fraction comparison",
    "short_summary":"fraction comparison","index_state":"CANDIDATE","utilization_class":"REFERENCE_ONLY"},
   make_row("OLD","fraction comparison"),
  ]
  staged=retrieve_learning_evidence({"query":"fraction comparison","minimum_results":1},[rows[0]])
  self.assertFalse(staged["evidence_sufficient_for_review"])
  self.assertEqual(staged["evidence_gap"]["staged_candidate_count"],1)
  mixed=retrieve_learning_evidence({"query":"fraction comparison","top_k":1,"minimum_results":1},rows,owner_verifier=verifier_for(rows[1]))
  self.assertTrue(mixed["evidence_sufficient_for_review"])
  self.assertEqual(mixed["evidence_candidates"][0]["source_id"],"OLD")

if __name__=="__main__":
 unittest.main()
