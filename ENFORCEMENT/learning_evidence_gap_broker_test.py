#!/usr/bin/env python3
import json,tempfile,unittest
from pathlib import Path
from learning_evidence_gap_broker import route_gap

REFERENCE_GAP={
 "gap_id":"A:영어:VOCABULARY:REFERENCE_EVIDENCE_REQUIRED:LE-F01",
 "owner":"LEARNING_ENGINE_CORE","gap_type":"REFERENCE_EVIDENCE_REQUIRED","priority":"MEDIUM",
 "scope":{"member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY"},
 "index_check_required":True,"resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
 "mining_request_authorized":False,"requested_capability":"EXTERNAL_REFERENCE_EVIDENCE",
 "acceptable_source_families":["OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS"],
 "acceptable_authority_classes":["OFFICIAL"],"required_provenance":["OFFICIAL_STANDARD_REF"],
 "query_terms":["영어","VOCABULARY","교육과정"],"existing_source_refs":[]
}
LEXICAL_GAP={
 "gap_id":"A:english:vocabulary:LEXICAL_SEMANTICS_REFERENCE_REQUIRED:LE-GROWTH-01",
 "owner":"LEARNING_ENGINE_CORE","gap_type":"LEXICAL_SEMANTICS_REFERENCE_REQUIRED","priority":"MEDIUM",
 "scope":{"member_id":"A","subject":"english","concept_skill_target":"vocabulary"},
 "index_check_required":True,"resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
 "mining_request_authorized":False,"requested_capability":"LEXICAL_SEMANTICS",
 "required_learning_evidence_role":"LEXICAL_SEMANTICS",
 "required_provenance_any_of":["LEXICAL_REFERENCE_SOURCE"],
 "query_terms":["english","vocabulary","LEXICAL_SEMANTICS"],"existing_source_refs":[]
}
LEARNER_GAP={
 "gap_id":"A:영어:VOCABULARY:LEARNER_EVIDENCE_SPARSE","owner":"LEARNING_ENGINE_CORE",
 "gap_type":"LEARNER_EVIDENCE_SPARSE","priority":"MEDIUM",
 "scope":{"member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY"},
 "index_check_required":False,"resolution_path":"SPECIALIST_EVIDENCE_ACQUISITION",
 "mining_request_authorized":False,"requested_capability":"LEARNER_PERFORMANCE_EVIDENCE"
}

def write_index(path,rows): path.write_text(json.dumps({"sources":rows},ensure_ascii=False),encoding="utf-8")

class GapBrokerTest(unittest.TestCase):
 def test_reference_index_sufficient_blocks_mining(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[{"source_id":"SRC-ENG-1","title":"영어 VOCABULARY 교육과정","source_family":"OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS","source_type":"OFFICIAL_CURRICULUM","authority_level":"OFFICIAL","keywords":["영어","VOCABULARY","교육과정"],"provenance":["OFFICIAL_STANDARD_REF"]}])
   r=route_gap(REFERENCE_GAP,index_path=index); self.assertEqual(r["decision"],"INDEX_REQUERY"); self.assertTrue(r["index_sufficient"])
 def test_wrong_family_does_not_satisfy_reference_gap(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[{"source_id":"SRC-BLOG-1","title":"영어 VOCABULARY 교육과정","source_family":"BLOG","authority_level":"SECONDARY","keywords":["영어","VOCABULARY","교육과정"]}])
   r=route_gap(REFERENCE_GAP,index_path=index); self.assertEqual(r["decision"],"MINING_REQUEST"); self.assertFalse(r["index_sufficient"]); self.assertEqual(r["mining_request"]["index_check"]["eligible_result_count"],0)
 def test_role_specific_gap_ignores_wrong_provenance_then_accepts_dictionary(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"
   write_index(index,[{
    "source_id":"EDU1","title":"english vocabulary curriculum",
    "source_family":"OFFICIAL_CURRICULUM","authority_level":"OFFICIAL",
    "keywords":["english","vocabulary"],"provenance":["OFFICIAL_EDUCATION_SOURCE"]
   }])
   r=route_gap(LEXICAL_GAP,index_path=index)
   self.assertEqual(r["decision"],"MINING_REQUEST")
   self.assertEqual(r["mining_request"]["required_learning_evidence_role"],"LEXICAL_SEMANTICS")
   write_index(index,[{
    "source_id":"DICT1","title":"english vocabulary lexical reference",
    "source_family":"LEXICAL_DICTIONARY","authority_level":"REFERENCE",
    "keywords":["english","vocabulary","LEXICAL_SEMANTICS"],
    "provenance":["LEXICAL_REFERENCE_SOURCE"]
   }])
   r=route_gap(LEXICAL_GAP,index_path=index)
   self.assertEqual(r["decision"],"INDEX_REQUERY")
   self.assertTrue(r["index_sufficient"])


 def test_role_contract_cannot_be_bypassed_by_mismatched_any_of_tag(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"
   gap=dict(LEXICAL_GAP)
   gap["required_provenance_any_of"]=["OFFICIAL_EDUCATION_SOURCE"]
   write_index(index,[{
    "source_id":"EDU-WITH-LEXICAL-TEXT",
    "title":"english vocabulary lexical semantics curriculum",
    "source_family":"OFFICIAL_CURRICULUM","authority_level":"OFFICIAL",
    "keywords":["english","vocabulary","LEXICAL_SEMANTICS"],
    "provenance":["OFFICIAL_EDUCATION_SOURCE"]
   }])
   r=route_gap(gap,index_path=index)
   self.assertEqual(r["decision"],"MINING_REQUEST")
   self.assertEqual(r["mining_request"]["index_check"]["eligible_result_count"],0)

 def test_unknown_learning_evidence_role_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[])
   gap=dict(LEXICAL_GAP); gap["required_learning_evidence_role"]="MAGIC_ROLE"
   r=route_gap(gap,index_path=index)
   self.assertFalse(r["pass"])
   self.assertIn("LEARNING_EVIDENCE_ROLE_INVALID",r["detected"])

 def test_learner_gap_routes_specialist_not_mining(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[])
   r=route_gap(LEARNER_GAP,index_path=index); self.assertEqual(r["decision"],"SPECIALIST_EVIDENCE_REQUEST"); self.assertIsNone(r["mining_request"]); self.assertFalse(r["index_checked"])
 def test_learning_cannot_authorize_mining(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[]); bad=dict(REFERENCE_GAP); bad["mining_request_authorized"]=True
   r=route_gap(bad,index_path=index); self.assertFalse(r["pass"]); self.assertIn("LEARNING_MINING_AUTHORIZATION_FORBIDDEN",r["detected"])

if __name__=="__main__": unittest.main()