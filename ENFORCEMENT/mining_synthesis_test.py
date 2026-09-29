#!/usr/bin/env python3
import unittest
from mining_synthesis import synthesize
from mining_core import checkpoint

class T(unittest.TestCase):
 def test_closed_items_are_bucketed(self):
  c={"frontier":[{"id":"f","kind":"FOUNDATION","question":"base","status":"CLOSED","best_evidence_score":.9},{"id":"a","kind":"ADVANCED","question":"deep","status":"CLOSED","best_evidence_score":.8}],"evidence":[{"evidence_id":"e1","frontier_id":"f","claim":"base claim","quality_score":.9},{"evidence_id":"e2","frontier_id":"a","claim":"deep claim","quality_score":.8}]}
  r=synthesize(c)
  self.assertEqual(r["sections"]["foundation"][0]["frontier_id"],"f")
  self.assertEqual(r["sections"]["advanced"][0]["frontier_id"],"a")
  self.assertTrue(r["ready_for_recommendation_review"])

 def test_unresolved_not_collapsed(self):
  c={"frontier":[{"id":"c","kind":"CRITICAL","question":"conflict","status":"CONFLICT"}],"evidence":[]}
  r=synthesize(c)
  self.assertFalse(r["ready_for_recommendation_review"])
  self.assertEqual(r["unresolved"][0]["status"],"CONFLICT")

 def test_partial_batch_cannot_be_presented_as_full_research(self):
  task={"goal":"confirm three required claims","task_family":"GENERAL_RESEARCH",
        "required_frontier_ids":["A","B","C"]}
  frontier=[{"id":"A","kind":"UNKNOWN","question":"A"},
            {"id":"B","kind":"UNKNOWN","question":"B"}]
  evidence=[{"evidence_id":"E-A","frontier_id":"A","source_id":"S-A",
             "source_url":"https://public.example/A","excerpt_ref":"para:1",
             "source_class":"PRIMARY","direct_support":True,"claim":"claim A"},
            {"evidence_id":"E-B","frontier_id":"B","source_id":"S-B",
             "source_url":"https://public.example/B","excerpt_ref":"para:2",
             "source_class":"PRIMARY","direct_support":True,"claim":"claim B"}]
  cp=checkpoint(task,frontier,evidence)
  self.assertTrue(all(x["status"]=="CLOSED" for x in cp["frontier"]))
  self.assertFalse(cp["goal_sufficiency"]["goal_sufficient"])
  report=synthesize(cp)
  self.assertFalse(report["ready_for_recommendation_review"])
  self.assertIn({"frontier_id":"C","status":"MISSING_REQUIRED","question":"C"},
                report["unresolved"])
  self.assertEqual(report["sections"]["other"][0]["source_anchors"][0]["source_id"],"S-A")
  self.assertTrue(report["source_grounding_review_required"])

 def test_alternative_becomes_candidate_not_recommendation(self):
  c={"frontier":[{"id":"alt","kind":"ALTERNATIVE","question":"option b","status":"CLOSED"}],"evidence":[{"evidence_id":"e1","frontier_id":"alt","claim":"works","quality_score":.9}]}
  r=synthesize(c)
  self.assertEqual(r["recommendation_candidates"][0]["status"],"CANDIDATE")
  self.assertFalse(r["recommendation_candidates"][0]["promotion_allowed"])

if __name__=="__main__": unittest.main()
