#!/usr/bin/env python3
import unittest
from mining_index_bridge import query_frontier

ROWS=[
 {"source_id":"A","canonical_title":"Official fraction standard","short_summary":"grade 5 fraction standard","keywords":["fraction","standard"],"authority_class":"OFFICIAL"},
 {"source_id":"B","canonical_title":"Writing rubric","short_summary":"structured writing rubric","keywords":["writing","rubric"],"authority_class":"OFFICIAL"},
]
FRONTIER=[
 {"id":"F1","question":"fraction standard"},
 {"id":"F2","question":"decimal intervention causal evidence"},
]

class MiningIndexBridgeTests(unittest.TestCase):
 def test_index_first_closes_known_and_forwards_gap(self):
  out=query_frontier(FRONTIER,ROWS,min_results=1,top_k=3)
  self.assertEqual(out["counts"]["resolved_from_index"],1)
  self.assertEqual(out["counts"]["external_required"],1)
  self.assertEqual(out["external_mining_frontier"][0]["id"],"F2")
  self.assertTrue(out["guards"]["index_does_not_decide_domain_use"])

 def test_index_hit_is_candidate_not_proof(self):
  out=query_frontier([{"id":"F1","question":"fraction standard"}],ROWS)
  self.assertEqual(out["counts"]["resolved_from_index"],1)
  self.assertEqual(out["counts"]["verification_required"],1)
  self.assertFalse(out["trace"][0]["evidence_sufficient"])
  self.assertEqual(out["verification_frontier"][0]["id"],"F1")

 def test_stale_reference_only_hit_does_not_resolve_research_gap(self):
  weak=[{"source_id":"OLD","canonical_title":"official fraction standard",
         "short_summary":"fraction standard","authority_class":"REFERENCE_ONLY",
         "stale_state":"STALE","review_state":"REFERENCE_ONLY"}]
  out=query_frontier([{"id":"F1","question":"fraction standard"}],weak)
  self.assertEqual(out["counts"]["resolved_from_index"],0)
  self.assertEqual(out["external_mining_frontier"][0]["id"],"F1")
  self.assertEqual(out["trace"][0]["retrieval_hit_count"],1)

 def test_empty_index_forwards_all(self):
  out=query_frontier(FRONTIER,[])
  self.assertEqual(out["counts"]["external_required"],2)

if __name__=="__main__":
 unittest.main()
