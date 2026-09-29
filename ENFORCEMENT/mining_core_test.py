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

 def test_same_official_dataset_two_surfaces_not_two_independent_sources(self):
  from mining_core import assess_frontier
  item=[{"id":"M1","question":"published metadata"}]
  doc={"frontier_id":"M1","source_identity":"data.go.kr:15134735",
       "source_id":"HTML-15134735","source_url":"https://www.data.go.kr/data/15134735/openapi.do",
       "source_class":"OFFICIAL","claim":"REST / JSON+XML","direct_support":True,
       "fresh_enough":True,"independent_support_count":2}
  meta={**doc,"source_id":"CATALOG-15134735",
        "source_url":"https://www.data.go.kr/catalog/15134735/openapi.json"}
  out=assess_frontier(item,[doc,meta])[0]
  self.assertEqual(out["evidence_count"],2)
  self.assertEqual(out["independent_source_identity_count"],1)
  self.assertEqual(out["best_evidence_score"],.925)

 def test_canonical_group_collapses_distinct_document_urls(self):
  from mining_core import assess_frontier
  rows=[{"frontier_id":"F","canonical_source_id":"PUB:DATASET-1",
         "source_identity":"HTML:D1","source_class":"OFFICIAL",
         "source_url":"https://example.gov/item/1","claim":"published specification",
         "direct_support":True,"fresh_enough":True,"independent_support_count":2},
        {"frontier_id":"F","canonical_source_id":"PUB:DATASET-1",
         "source_identity":"JSON:D1","source_class":"OFFICIAL",
         "source_url":"https://example.gov/catalog/1","claim":"published specification",
         "direct_support":True,"fresh_enough":True,"independent_support_count":2}]
  x=assess_frontier([{"id":"F","question":"published specification"}],rows)[0]
  self.assertEqual(x["independent_source_identity_count"],1)
  self.assertEqual(x["best_evidence_score"],.925)

 def test_distinct_canonical_origins_allow_independent_support_when_claimed(self):
  from mining_core import assess_frontier
  one={"frontier_id":"F","source_identity":"publisher:A","source_class":"PRIMARY",
       "claim":"X","direct_support":True,"fresh_enough":True,
       "independent_support_count":2}
  two={**one,"source_identity":"publisher:B"}
  out=assess_frontier([{"id":"F","question":"X"}],[one,two])[0]
  self.assertEqual(out["independent_source_identity_count"],2)
  self.assertEqual(out["best_evidence_score"],1.0)

 def test_public_catalog_metadata_cannot_close_credentialed_runtime_goal(self):
  task={"task_family":"PUBLIC_DATA","goal":"assess 건축HUB registry API usability",
        "required_frontier_ids":["PUBLISHED_SPEC","AUTHENTICATED_RESPONSE"]}
  front=[{"id":"PUBLISHED_SPEC","kind":"CRITICAL","question":"published REST JSON XML metadata"},
         {"id":"AUTHENTICATED_RESPONSE","kind":"CRITICAL",
          "question":"actual authorized API returns a building register record"}]
  published={"frontier_id":"PUBLISHED_SPEC","source_identity":"data.go.kr:15134735",
             "source_id":"DATA-GO-KR-15134735",
             "source_url":"https://www.data.go.kr/data/15134735/openapi.do",
             "source_class":"OFFICIAL","claim":"REST, JSON+XML metadata is published",
             "direct_support":True,"fresh_enough":True,
             "excerpt_ref":"Open API info: API type / data format",
             "independent_support_count":1}
  c=checkpoint(task,front,[published])
  self.assertEqual(c["frontier"][0]["status"],"CLOSED")
  self.assertEqual(c["frontier"][1]["status"],"OPEN")
  self.assertFalse(c["stop"])
  self.assertEqual(c["goal_sufficiency"]["unresolved_critical"],[])
  self.assertIn("AUTHENTICATED_RESPONSE",c["goal_sufficiency"]["unresolved_required"])
  self.assertEqual(c["next_queries"][0]["frontier_id"],"AUTHENTICATED_RESPONSE")

 def test_synthesis_preserves_checkpoint_trace(self):
  c=checkpoint({"task_family":"X","goal":"new goal"},[{"id":"f","kind":"FOUNDATION","question":"base"}],[{"evidence_id":"e1","frontier_id":"f","source_class":"OFFICIAL","direct_support":True,"claim":"base claim","independent_support_count":2}])
  s=synthesize_checkpoint(c)
  self.assertEqual(s["checkpoint_resume_key"],c["resume_key"])
  self.assertEqual(s["synthesis"]["sections"]["foundation"][0]["frontier_id"],"f")

if __name__=="__main__": unittest.main()
