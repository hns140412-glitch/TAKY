#!/usr/bin/env python3
import unittest
from mining_core import checkpoint,resume,evidence_score

F=[{"id":"law","question":"official rule"},{"id":"impl","question":"implementation evidence"}]
class MiningCoreTest(unittest.TestCase):
 def test_primary_direct_scores_high(self):
  self.assertGreaterEqual(evidence_score({"source_class":"PRIMARY","direct_support":True,"independent_support_count":2}),.9)
 def test_gap_generates_query_and_checkpoint(self):
  c=checkpoint({"task_family":"X","goal":"new goal"},F,[])
  self.assertFalse(c["stop"]); self.assertEqual(len(c["next_queries"]),2); self.assertTrue(c["resume_key"])
 def test_resume_closes_without_restart(self):
  c=checkpoint({"task_family":"X","goal":"new goal"},F,[])
  e=[{"frontier_id":"law","source_class":"OFFICIAL","direct_support":True,"claim":"A","independent_support_count":2},{"frontier_id":"impl","source_class":"PRIMARY","direct_support":True,"claim":"B","independent_support_count":2}]
  r=resume(c,e)
  self.assertEqual(r["cycle"],2); self.assertTrue(r["stop"]); self.assertEqual(r["stop_reason"],"EVIDENCE_SUFFICIENT")
 def test_conflict_stays_open(self):
  e=[{"frontier_id":"law","source_class":"OFFICIAL","direct_support":True,"claim":"A","independent_support_count":2},{"frontier_id":"law","source_class":"OFFICIAL","direct_support":True,"claim":"B","independent_support_count":2}]
  c=checkpoint({"task_family":"X","goal":"new goal"},[F[0]],e)
  self.assertFalse(c["stop"]); self.assertEqual(c["frontier"][0]["status"],"CONFLICT"); self.assertEqual(c["next_queries"][0]["purpose"],"RESOLVE_CONFLICT")
if __name__=="__main__": unittest.main()
