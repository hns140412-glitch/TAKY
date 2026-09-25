#!/usr/bin/env python3
import unittest
from mining_growth_loop import outcome_quality,propose_growth,aggregate_strategy_observations

class T(unittest.TestCase):
 def test_good_outcome_becomes_candidate_only(self):
  r=propose_growth({"task_family":"X","goal":"g","selected_route":"r"},{"success":True,"accuracy":1,"usefulness":1,"completeness":1,"efficiency":.8,"user_correction_rate":0})
  self.assertEqual(r["proposal"]["type"],"STRATEGY_OBSERVATION")
  self.assertEqual(r["proposal"]["status"],"CANDIDATE")
  self.assertFalse(r["proposal"]["promotion_allowed"])

 def test_weak_outcome_becomes_failure_observation(self):
  r=propose_growth({"task_family":"X","goal":"g","selected_route":"r"},{"success":True,"accuracy":.4,"usefulness":.4,"completeness":.4,"efficiency":.4,"user_correction_rate":.5})
  self.assertEqual(r["proposal"]["type"],"FAILURE_OBSERVATION")
  self.assertFalse(r["proposal"]["auto_resolution_allowed"])

 def test_three_strong_same_family_observations_become_review_eligible(self):
  obs=[{"type":"STRATEGY_OBSERVATION","status":"CANDIDATE","task_family":"X","quality_score":.9} for _ in range(3)]
  r=aggregate_strategy_observations(obs)
  self.assertTrue(r["eligible_for_review"])

 def test_cross_family_observations_do_not_promote_together(self):
  obs=[
   {"type":"STRATEGY_OBSERVATION","status":"CANDIDATE","task_family":"X","quality_score":.9},
   {"type":"STRATEGY_OBSERVATION","status":"CANDIDATE","task_family":"Y","quality_score":.9},
   {"type":"STRATEGY_OBSERVATION","status":"CANDIDATE","task_family":"X","quality_score":.9},
  ]
  self.assertFalse(aggregate_strategy_observations(obs)["eligible_for_review"])

if __name__=="__main__":unittest.main()
