#!/usr/bin/env python3
import unittest
from index_ingest_validator import classify_candidate

INDEX=[
 {"source_id":"A","canonical_title":"Official Guide","locator":"https://example.org/guide","content_hash":"abc"},
 {"source_id":"B","canonical_title":"Study","locator":"https://x.org/study-v1","content_hash":"old"},
]
class IndexIngestValidatorTest(unittest.TestCase):
 def test_exact_hash(self):
  c={"candidate_id":"C","identity":{"source_id":"C","canonical_title":"X","locator":"https://z","content_hash":"abc"}}
  r=classify_candidate(c,INDEX)
  self.assertEqual(r["status"],"EXACT_DUPLICATE")
  self.assertEqual(r["exact_duplicate_of"],["A"])
  self.assertFalse(r["promotion_allowed"])

 def test_near_same_locator_title(self):
  c={"candidate_id":"C","identity":{"source_id":"C","canonical_title":"Official Guide","locator":"https://example.org/guide","content_hash":None}}
  r=classify_candidate(c,INDEX)
  self.assertEqual(r["status"],"NEAR_DUPLICATE")
  self.assertIsNotNone(r["hold_reason"])

 def test_new_source(self):
  c={"candidate_id":"C","identity":{"source_id":"C","canonical_title":"New","locator":"https://new.org/a"}}
  r=classify_candidate(c,INDEX)
  self.assertEqual(r["status"],"NEW_SOURCE_CANDIDATE")

if __name__=="__main__":
 unittest.main()
