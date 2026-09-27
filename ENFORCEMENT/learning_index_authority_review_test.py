#!/usr/bin/env python3
"""Existing V26 authority labels must not vanish nor auto-become OFFICIAL."""
import json,tempfile,unittest
from pathlib import Path
from learning_evidence_gap_broker import route_gap

GAP={
 "gap_id":"LE-KICE-ASSESSMENT-REF","owner":"LEARNING_ENGINE_CORE",
 "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
 "scope":{"member_id":"A","subject":"국어","concept_skill_target":"assessment"},
 "index_check_required":True,"resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
 "mining_request_authorized":False,
 "acceptable_source_families":["KICE_ELEMENTARY_ASSESSMENT_2026"],
 "acceptable_authority_classes":["OFFICIAL"],"required_provenance":["OFFICIAL_STANDARD_REF"],
 "query_terms":["초등학교","학생평가"]
}
# Exact source id and descriptive label taken from the selected V26 metadata
# when this test was authored. This fixture does not copy the 679-row index.
KICE={
 "source_id":"1nUpgPyHDd0fWfwrw0jcSgd7fa__TczXq",
 "title":"2022_개정_교육과정에_따른_초등학교_학생평가_톺아보기(2026).pdf",
 "path":"DATA",
 "source_family":"KICE_ELEMENTARY_ASSESSMENT_2026",
 "authority_level":"AUTHORITY_LAYER",
 "source_review_state":"CONTENT_REVIEWED",
 "utilization_class":"REFERENCE_ONLY"
}
def execute(rows,gap=GAP,min_results=1):
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/"index.json"
  path.write_text(json.dumps({"source_entries":rows},ensure_ascii=False))
  return route_gap(gap,index_path=path,min_results=min_results)

class AuthorityReview(unittest.TestCase):
 def test_existing_descriptive_authority_is_review_not_mining_nor_official(self):
  out=execute([KICE])
  self.assertEqual(out["decision"],"INDEX_AUTHORITY_REVIEW_REQUIRED",out)
  self.assertFalse(out["index_sufficient"])
  self.assertIsNone(out["mining_request"])
  request=out["authority_review_request"]
  self.assertEqual(request["source_candidates"][0]["source_id"],KICE["source_id"])
  self.assertEqual(request["source_candidates"][0]["source_authority_literal"],"AUTHORITY_LAYER")
  self.assertEqual(request["source_candidates"][0]["review_status"],
                   "PENDING_INDEPENDENT_SOURCE_VERIFICATION")
  self.assertTrue(request["guards"]["candidate_is_not_official_proof"])
  self.assertTrue(request["guards"]["raw_authority_label_preserved"])
  self.assertEqual(out["retrieval"]["eligible_results"],[])
 def test_exact_verified_class_works_without_semantic_alias_guess(self):
  out=execute([{**KICE,"authority_level":"OFFICIAL"}])
  self.assertEqual(out["decision"],"INDEX_REQUERY")
  self.assertTrue(out["index_sufficient"])
  self.assertIsNone(out["mining_request"])
 def test_community_and_wrong_family_do_not_become_official_review(self):
  self.assertEqual(execute([{**KICE,"authority_level":"COMMUNITY_OR_PRACTICE_LAYER"}])["decision"],"MINING_REQUEST")
  self.assertEqual(execute([{**KICE,"source_family":"UNRELATED_FAMILY"}])["decision"],"MINING_REQUEST")
  self.assertEqual(execute([{**KICE,"path":"","authority_level":"AUTHORITY_LAYER"}])["decision"],"MINING_REQUEST")
 def test_mixed_sources_require_review_only_when_count_can_fill_gap(self):
  plain={**KICE,"source_id":"SOURCE2","authority_level":"OFFICIAL"}
  out=execute([KICE,plain],min_results=2)
  self.assertEqual(out["decision"],"INDEX_AUTHORITY_REVIEW_REQUIRED")
  self.assertEqual(len(out["retrieval"]["eligible_results"]),1)
  self.assertEqual(len(out["authority_review_request"]["source_candidates"]),1)
  self.assertEqual(execute([KICE],min_results=2)["decision"],"MINING_REQUEST")
 def test_learner_performance_gap_never_reaches_authority_review_or_mining(self):
  gap={**GAP,"resolution_path":"SPECIALIST_EVIDENCE_ACQUISITION",
       "gap_type":"LEARNER_EVIDENCE_SPARSE"}
  out=execute([KICE],gap=gap)
  self.assertEqual(out["decision"],"SPECIALIST_EVIDENCE_REQUEST")
  self.assertIsNone(out["mining_request"])

if __name__=="__main__": unittest.main(verbosity=2)
