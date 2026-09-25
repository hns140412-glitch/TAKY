#!/usr/bin/env python3
import unittest
from mining_goal_sufficiency import evaluate
class T(unittest.TestCase):
 def test_strong_evidence_but_missing_goal_dimension_does_not_stop(self):
  task={"foundation_frontier_ids":["f"],"advanced_frontier_ids":["a"]}
  r=evaluate(task,[{"id":"f","status":"CLOSED","best_evidence_score":1.0},{"id":"a","status":"OPEN","best_evidence_score":.9}])
  self.assertFalse(r["goal_sufficient"]); self.assertEqual(r["coverage"],.5)
 def test_required_alternative(self):
  task={"foundation_frontier_ids":["f"],"alternative_frontier_ids":["alt"],"alternatives_required":True}
  r=evaluate(task,[{"id":"f","status":"CLOSED"},{"id":"alt","status":"OPEN"}]); self.assertFalse(r["goal_sufficient"])
 def test_critical_gap_blocks(self):
  r=evaluate({"critical_frontier_ids":["c"]},[{"id":"c","status":"CONFLICT"}]); self.assertEqual(r["unresolved_critical"],["c"]); self.assertFalse(r["goal_sufficient"])
 def test_all_required_closed(self):
  r=evaluate({"foundation_frontier_ids":["f"],"advanced_frontier_ids":["a"]},[{"id":"f","status":"CLOSED"},{"id":"a","status":"CLOSED"}]); self.assertTrue(r["goal_sufficient"])
if __name__=="__main__":unittest.main()
