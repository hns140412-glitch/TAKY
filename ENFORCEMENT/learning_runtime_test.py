#!/usr/bin/env python3
import unittest
from learning_runtime import run_learning_cycle,evaluate_outcome

EVID=[{"source_id":"S1","authorization_class":"READY_WITH_GUARDS"}]

class LearningRuntimeTest(unittest.TestCase):
 def test_repeated_error_selects_targeted_remediation(self):
  r=run_learning_cycle({"context":{"learner_id":"C1","skill_id":"FRACTION"},"evidence_candidates":EVID,"observations":[{"correct":False},{"correct":False}]})
  self.assertEqual(r["strategy_selection"]["strategy"],"TARGETED_REMEDIATION")
  self.assertEqual(r["next_learning_action"]["action"],"REMEDIATION_UNIT")
  self.assertIsNone(r["next_learning_action"]["planner_date"])

 def test_high_accuracy_selects_spaced_review(self):
  r=run_learning_cycle({"context":{"learner_id":"C1","skill_id":"VOCAB"},"evidence_candidates":EVID,"observations":[{"correct":True},{"correct":True},{"correct":True},{"correct":True},{"correct":False}]})
  self.assertEqual(r["strategy_selection"]["strategy"],"SPACED_REVIEW")

 def test_hold_evidence_blocks_learning_action(self):
  r=run_learning_cycle({"context":{"skill_id":"MATH"},"evidence_candidates":[{"source_id":"X","authorization_class":"HOLD"}],"observations":[{"correct":False}]})
  self.assertEqual(r["strategy_selection"]["strategy"],"HOLD_FOR_EVIDENCE")
  self.assertFalse(r["next_learning_action"]["planner_allocation_allowed"])
  self.assertEqual(r["evidence_gap"]["type"],"LEARNING_EVIDENCE_GAP")

 def test_outcome_only_proposes_memory_observation(self):
  run=run_learning_cycle({"context":{"skill_id":"VOCAB"},"evidence_candidates":EVID,"observations":[{"correct":True}]})
  o=evaluate_outcome(run,{"completed":True,"evidence_of_improvement":True})
  self.assertEqual(o["memory_proposal"]["status"],"CANDIDATE")
  self.assertFalse(o["memory_proposal"]["promotion_allowed"])

if __name__=="__main__":
 unittest.main()
