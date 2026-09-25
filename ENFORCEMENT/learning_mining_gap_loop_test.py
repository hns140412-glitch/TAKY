#!/usr/bin/env python3
import unittest
from learning_orchestrator import orchestrate_learning
from learning_mining_gap_loop import plan_from_learning_gap,requery_learning

class LearningMiningGapLoopTest(unittest.TestCase):
 def test_gap_creates_mining_plan(self):
  learning=orchestrate_learning({
   "evidence_request":{"query":"decimal causal prerequisite","minimum_results":1},
   "index_rows":[],
   "context":{"skill_id":"DECIMAL","learning_context":"error analysis"},
   "observations":[{"correct":False}],
  })
  loop=plan_from_learning_gap(learning)
  self.assertTrue(loop["mining_required"])
  self.assertEqual(loop["mining_task"]["task_family"],"LEARNING_ENGINE")
  self.assertTrue(loop["mining_plan"]["plan"]["external_search_required"])

 def test_no_gap_skips_mining(self):
  learning={"mining_request_candidate":None}
  loop=plan_from_learning_gap(learning)
  self.assertFalse(loop["mining_required"])

 def test_requery_after_index_update_closes_gap(self):
  original={
   "evidence_request":{"query":"fraction remediation","minimum_results":1},
   "context":{"skill_id":"FRACTION"},
   "observations":[{"correct":False},{"correct":False}],
  }
  rows=[{"source_id":"S1","canonical_title":"Official fraction remediation","short_summary":"fraction remediation","keywords":["fraction","remediation"],"authorization_class":"READY_WITH_GUARDS","authority_class":"OFFICIAL"}]
  out=requery_learning(original,rows)["learning_result"]
  self.assertIsNone(out["mining_request_candidate"])
  self.assertEqual(out["runtime"]["strategy_selection"]["strategy"],"TARGETED_REMEDIATION")

if __name__=="__main__":
 unittest.main()
