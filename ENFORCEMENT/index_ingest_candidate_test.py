#!/usr/bin/env python3
import unittest
from index_ingest_candidate import build_candidate,build_candidates

class IndexIngestCandidateTest(unittest.TestCase):
 def test_candidate_never_assigns_current_or_family(self):
  c=build_candidate({"source_url":"https://example.org/a","source_title":"A","source_class":"OFFICIAL","claim":"x"})
  self.assertIsNone(c["classification_candidate"]["source_family"])
  self.assertIsNone(c["state"]["current_relation"])
  self.assertEqual(c["state"]["index_state"],"CANDIDATE")
  self.assertTrue(c["guards"]["candidate_is_not_canonical"])

 def test_batch_preserves_count(self):
  b=build_candidates([{"source_url":"https://a.example"},{"source_url":"https://b.example"}])
  self.assertEqual(b["count"],2)

if __name__=="__main__":
 unittest.main()
