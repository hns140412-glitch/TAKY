#!/usr/bin/env python3
import unittest
from mining_core import checkpoint,resume,evidence_score,apply_external_receipts,synthesize_checkpoint

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
  self.assertEqual(r["cycle"],2); self.assertTrue(r["stop"]); self.assertEqual(r["stop_reason"],"GOAL_AND_EVIDENCE_SUFFICIENT")
 def test_conflict_stays_open(self):
  e=[{"evidence_id":"a","frontier_id":"law","source_class":"OFFICIAL","direct_support":True,"subject":"rule","predicate":"allowed","scope":"same","polarity":"ALLOW","independent_support_count":2},{"evidence_id":"b","frontier_id":"law","source_class":"OFFICIAL","direct_support":True,"subject":"rule","predicate":"allowed","scope":"same","polarity":"DENY","independent_support_count":2}]
  c=checkpoint({"task_family":"X","goal":"new goal"},[F[0]],e)
  self.assertFalse(c["stop"]); self.assertEqual(c["frontier"][0]["status"],"CONFLICT"); self.assertEqual(c["next_queries"][0]["purpose"],"RESOLVE_CONFLICT")
 def test_external_receipt_resumes_checkpoint(self):
  c=checkpoint({"task_family":"X","goal":"new goal"},[{"id":"law","question":"official rule"}],[])
  r=apply_external_receipts(c,[{"frontier_id":"law","query":"official rule","adapter":"WEB","results":[{"url":"https://example.gov/r","source_class":"OFFICIAL","direct_support":True,"subject":"rule","predicate":"text","scope":"current","value":"A","independent_support_count":2}]}])
  self.assertEqual(r["external_ingest"]["accepted_evidence"],1); self.assertTrue(r["stop"])

 def test_resume_preserves_unprocessed_required_goal_contract(self):
  task={"task_family":"GENERAL_RESEARCH","goal":"verify three required sources",
        "critical_requirements":["source A","source B","source C"],
        "unknown":["cross-check note"]}
  from mining_goal_decomposition import decompose
  critical=decompose(task)["critical_frontier_ids"]
  selected=[{"id":critical[0],"kind":"CRITICAL","question":"source A"},
            {"id":critical[1],"kind":"CRITICAL","question":"source B"}]
  c=checkpoint(task,selected,[])
  self.assertFalse(c["stop"])
  self.assertIn(critical[2],c["goal_sufficiency"]["missing_required"])
  for i,item in enumerate(selected):
   c=apply_external_receipts(c,[{"frontier_id":item["id"],"query":item["question"],
     "adapter":"WEB","results":[{"source_id":"S"+str(i),"url":"https://example.gov/"+str(i),
       "source_class":"PRIMARY","claim":"evidence "+item["question"],"direct_support":True,
       "fresh_enough":True,"excerpt_ref":"page:1#p:1","independent_support_count":2}]}])
  self.assertTrue(all(x["status"]=="CLOSED" for x in c["frontier"]))
  self.assertFalse(c["stop"],"Closed current batch cannot close an unprocessed critical goal")
  self.assertIn(critical[2],c["goal_sufficiency"]["missing_required"])
  self.assertIn("cross-check note",c["goal_sufficiency"]["missing_required"])
  self.assertEqual(c["task_contract"]["goal"],task["goal"])

 def test_synthesis_preserves_checkpoint_trace(self):
  c=checkpoint({"task_family":"X","goal":"new goal"},[{"id":"f","kind":"FOUNDATION","question":"base"}],[{"evidence_id":"e1","frontier_id":"f","source_class":"OFFICIAL","direct_support":True,"claim":"base claim","independent_support_count":2}])
  s=synthesize_checkpoint(c)
  self.assertEqual(s["checkpoint_resume_key"],c["resume_key"])
  self.assertEqual(s["synthesis"]["sections"]["foundation"][0]["frontier_id"],"f")

if __name__=="__main__": unittest.main()
