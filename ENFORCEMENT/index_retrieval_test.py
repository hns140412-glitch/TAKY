#!/usr/bin/env python3
import unittest
from index_retrieval import retrieve, structured_filter

ROWS=[
 {"source_id":"A","canonical_title":"Official Math Standard","source_family":"CURRICULUM","source_type":"PDF","authority_class":"OFFICIAL","short_summary":"fraction learning standard","keywords":["fraction","grade5"],"current_relation":"PROMOTED_CURRENT"},
 {"source_id":"B","canonical_title":"Fraction remediation study","source_family":"RESEARCH","source_type":"PDF","authority_class":"ACADEMIC","short_summary":"fraction remediation evidence","keywords":["fraction","intervention"]},
 {"source_id":"C","canonical_title":"Old Math Standard","source_family":"CURRICULUM","source_type":"PDF","authority_class":"OFFICIAL","short_summary":"older fraction standard","keywords":["fraction"],"current_relation":"SUPERSEDED"},
 {"source_id":"D","canonical_title":"Vocabulary map","source_family":"VOCAB","source_type":"IMAGE","authority_class":"REFERENCE","short_summary":"word map","keywords":["vocabulary"]},
]
REL=[
 {"from":"A","to":"C","type":"SUPERSEDES"},
 {"from":"A","to":"B","type":"RELATED_TO"},
]
DETAIL=[
 {"source_id":"A","page":3,"anchor":"6수01-06"},
 {"source_id":"B","page":7,"anchor":"results"},
]

class IndexRetrievalTests(unittest.TestCase):
 def test_structured_exact_filter(self):
  out=structured_filter(ROWS,{"source_family":"CURRICULUM","current_relation":"PROMOTED_CURRENT"})
  self.assertEqual([x["source_id"] for x in out],["A"])

 def test_lexical_and_semantic_rrf(self):
  out=retrieve(ROWS,"fraction",semantic_scores={"B":0.95,"A":0.80},top_k=2)
  self.assertEqual(len(out["primary"]),2)
  self.assertEqual({x["source_id"] for x in out["primary"]},{"A","B"})
  self.assertTrue(out["guards"]["search_projection_is_not_source_of_truth"])

 def test_relation_expansion_and_detail(self):
  out=retrieve(ROWS,"official math",relations=REL,detail_rows=DETAIL,top_k=1,relation_hops=1)
  self.assertEqual(out["primary"][0]["source_id"],"A")
  self.assertEqual({x["source_id"] for x in out["expanded"]},{"B","C"})
  self.assertEqual({x["source_id"] for x in out["details"]},{"A","B"})

 def test_structured_only_deterministic(self):
  out=retrieve(ROWS,"",filters={"authority_class":"OFFICIAL"},top_k=10)
  self.assertEqual([x["source_id"] for x in out["primary"]],["A","C"])

 def test_semantic_cannot_override_filter(self):
  out=retrieve(ROWS,"fraction",filters={"source_family":"CURRICULUM"},semantic_scores={"B":1.0,"A":0.2},top_k=5)
  self.assertNotIn("B",{x["source_id"] for x in out["primary"]})

if __name__=="__main__":
 unittest.main()
