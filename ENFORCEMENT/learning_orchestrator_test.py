#!/usr/bin/env python3
import unittest
from learning_orchestrator import orchestrate_learning

ROWS=[
 {"source_id":"S1","canonical_title":"Official fraction remediation","short_summary":"fraction remediation","keywords":["fraction","remediation"],"authorization_class":"READY_WITH_GUARDS","authority_class":"OFFICIAL"},
]

class LearningOrchestratorTest(unittest.TestCase):
 def test_index_to_runtime_path(self):
  r=orchestrate_learning({
   "evidence_request":{"query":"fraction remediation","minimum_results":1},
   "index_rows":ROWS,
   "context":{"learner_id":"C1","skill_id":"FRACTION"},
   "observations":[{"correct":False},{"correct":False}],
  })
  self.assertTrue(r["retrieval"]["evidence_sufficient_for_review"])
  self.assertEqual(r["runtime"]["strategy_selection"]["strategy"],"TARGETED_REMEDIATION")
  self.assertIsNone(r["runtime"]["next_learning_action"]["planner_date"])
  self.assertIsNone(r["mining_request_candidate"])

 def test_gap_only_becomes_mining_candidate(self):
  r=orchestrate_learning({
   "evidence_request":{"query":"decimal causal prerequisite","minimum_results":1},
   "index_rows":[],
   "context":{"skill_id":"DECIMAL","learning_context":"error analysis"},
   "observations":[{"correct":False}],
  })
  self.assertEqual(r["mining_request_candidate"]["type"],"LEARNING_EVIDENCE_GAP")
  self.assertTrue(r["guards"]["index_checked_before_mining"])

if __name__=="__main__":
 unittest.main()
