#!/usr/bin/env python3
import unittest
from learning_consumer_adapters import to_ready_planner_request,hide_signal_to_observation,snap_result_to_outcome

class LearningConsumerAdaptersTest(unittest.TestCase):
 def test_ready_preserves_planner_date_authority(self):
  x=to_ready_planner_request({"runtime":{"next_learning_action":{"planner_allocation_allowed":True,"action":"REVIEW_UNIT","skill_id":"VOCAB","intensity":"LOW","estimated_units":1}}},{"child_id":"C1"})
  self.assertTrue(x["accepted_for_planner"])
  self.assertIsNone(x["planner_date"])
  self.assertTrue(x["guards"]["ready_planner_owns_date"])

 def test_hide_emits_observation_not_schedule(self):
  x=hide_signal_to_observation({"type":"RECALL_RESULT","child_id":"C1","payload":{"word":"apple","result":"CORRECT","hint_used":True,"nextReviewPriority":"HIGH"}})
  self.assertTrue(x["correct"])
  self.assertTrue(x["assisted"])
  self.assertEqual(x["next_review_priority"],"HIGH")
  self.assertTrue(x["guards"]["hide_does_not_schedule_long_term_review"])

 def test_snap_emits_contextual_outcome(self):
  x=snap_result_to_outcome({"type":"TASK_COMPLETED","child_id":"C1","payload":{"concept_skill_target":"writing","rubric_result":{"passed":True}}})
  self.assertTrue(x["completed"])
  self.assertTrue(x["evidence_of_improvement"])
  self.assertTrue(x["guards"]["production_completion_is_not_global_mastery"])

if __name__=="__main__":
 unittest.main()
