#!/usr/bin/env python3
import unittest
from mining_depth_router import route_depth

class T(unittest.TestCase):
 def test_known_complete_is_d0(self):
  self.assertEqual(route_depth({"goal":"x","known_complete":True})["research_depth_decision"],"D0")

 def test_low_risk_new_goal_gets_light_pass(self):
  r=route_depth({"goal":"simple lookup"})
  self.assertEqual(r["research_depth_decision"],"D1")

 def test_high_impact_conflicted_high_stakes_goes_deep(self):
  r=route_depth({"goal":"critical decision","goal_impact":1,"evidence_risk":1,"uncertainty":1,"decision_risk":1,"urgency":1,"conflict":["c1","c2"]})
  self.assertEqual(r["research_depth_decision"],"D4")

 def test_high_cost_can_reduce_depth(self):
  a=route_depth({"goal":"x","goal_impact":.7,"evidence_risk":.6,"uncertainty":.6,"research_cost":0})
  b=route_depth({"goal":"x","goal_impact":.7,"evidence_risk":.6,"uncertainty":.6,"research_cost":1})
  order={"D0":0,"D1":1,"D2":2,"D3":3,"D4":4}
  self.assertLessEqual(order[b["research_depth_decision"]],order[a["research_depth_decision"]])

 def test_ceiling_respected(self):
  r=route_depth({"goal":"critical","goal_impact":1,"evidence_risk":1,"uncertainty":1,"decision_risk":1,"max_research_depth":"D2"})
  self.assertEqual(r["research_depth_decision"],"D2")

if __name__=="__main__":unittest.main()
