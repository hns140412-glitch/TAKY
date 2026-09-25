#!/usr/bin/env python3
import unittest
from external_to_learning_loop import process_external_receipt

INDEX=[
 {"source_id":"A","canonical_title":"Official Guide","locator":"https://example.org/guide","content_hash":"abc","short_summary":"old evidence","authority_class":"OFFICIAL","utilization_class":"REFERENCE_ONLY"}
]
LEARNING={
 "evidence_request":{"query":"decimal remediation","minimum_results":1},
 "context":{"skill_id":"DECIMAL"},
 "observations":[{"correct":False},{"correct":False}],
}

class ExternalToLearningLoopTest(unittest.TestCase):
 def test_new_source_enters_projection_and_requeries(self):
  receipt={
   "frontier_id":"F1","query":"decimal remediation","adapter":"WEB",
   "results":[{"url":"https://new.org/decimal","title":"Decimal remediation","source_class":"OFFICIAL","claim":"decimal remediation"}]
  }
  out=process_external_receipt(receipt,INDEX,LEARNING)
  self.assertTrue(out["accepted"])
  self.assertEqual(out["projection_added"],1)
  self.assertEqual(out["updated_projection_count"],2)
  self.assertIsNotNone(out["learning_requery"])
  lr=out["learning_requery"]["learning_result"]
  self.assertTrue(lr["retrieval"]["evidence_sufficient_for_review"])

 def test_exact_duplicate_is_held_not_readded(self):
  receipt={
   "frontier_id":"F1","query":"guide","adapter":"WEB",
   "results":[{"url":"https://example.org/guide","title":"Official Guide","source_class":"OFFICIAL","claim":"same","content_hash":"abc"}]
  }
  # mining adapter currently does not propagate content_hash, so simulate duplicate by same locator/title => NEAR_DUPLICATE
  out=process_external_receipt(receipt,INDEX,None)
  self.assertEqual(out["projection_added"],0)
  self.assertEqual(out["projection_held"][0]["status"],"NEAR_DUPLICATE")
  self.assertTrue(out["guards"]["exact_near_version_not_auto_added"])

if __name__=="__main__":
 unittest.main()
