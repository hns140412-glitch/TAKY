#!/usr/bin/env python3
import unittest
from learning_growth_memory import observe,aggregate

class LearningGrowthMemoryTest(unittest.TestCase):
 def test_single_success_not_promoted(self):
  run={"strategy_selection":{"strategy":"SPACED_REVIEW"},"learner_state":{"skill_id":"VOCAB","learner_id":"C1"}}
  o=observe(run,{"success":True,"observation":{}})
  self.assertFalse(o["promotion_allowed"])
  a=aggregate([o])
  self.assertFalse(a["summaries"][0]["eligible_for_review"])

 def test_three_clean_successes_review_eligible_not_promoted(self):
  rows=[{"strategy":"GUIDED_PRACTICE","skill_id":"MATH","success":True} for _ in range(3)]
  a=aggregate(rows)
  s=a["summaries"][0]
  self.assertTrue(s["eligible_for_review"])
  self.assertFalse(s["promotion_allowed"])

 def test_failure_blocks_review_eligibility(self):
  rows=[
   {"strategy":"GUIDED_PRACTICE","skill_id":"MATH","success":True},
   {"strategy":"GUIDED_PRACTICE","skill_id":"MATH","success":True},
   {"strategy":"GUIDED_PRACTICE","skill_id":"MATH","success":False},
  ]
  a=aggregate(rows)
  self.assertFalse(a["summaries"][0]["eligible_for_review"])

if __name__=="__main__":
 unittest.main()
