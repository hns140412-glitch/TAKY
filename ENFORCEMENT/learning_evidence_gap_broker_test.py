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
   index=Path(td)/"index.json"; write_index(index,[{"source_id":"SRC-ENG-1","title":"영어 VOCABULARY 교육과정","source_family":"OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS","source_type":"OFFICIAL_CURRICULUM","authority_level":"OFFICIAL","keywords":["영어","VOCABULARY","교육과정"]}])
   r=route_gap(REFERENCE_GAP,index_path=index); self.assertEqual(r["decision"],"INDEX_REQUERY"); self.assertTrue(r["index_sufficient"])
 def test_wrong_family_does_not_satisfy_reference_gap(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[{"source_id":"SRC-BLOG-1","title":"영어 VOCABULARY 교육과정","source_family":"BLOG","authority_level":"SECONDARY","keywords":["영어","VOCABULARY","교육과정"]}])
   r=route_gap(REFERENCE_GAP,index_path=index); self.assertEqual(r["decision"],"MINING_REQUEST"); self.assertFalse(r["index_sufficient"]); self.assertEqual(r["mining_request"]["index_check"]["eligible_result_count"],0)
 def test_learner_gap_routes_specialist_not_mining(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[])
   r=route_gap(LEARNER_GAP,index_path=index); self.assertEqual(r["decision"],"SPECIALIST_EVIDENCE_REQUEST"); self.assertIsNone(r["mining_request"]); self.assertFalse(r["index_checked"])
 def test_learning_cannot_authorize_mining(self):
  with tempfile.TemporaryDirectory() as td:
   index=Path(td)/"index.json"; write_index(index,[]); bad=dict(REFERENCE_GAP); bad["mining_request_authorized"]=True
   r=route_gap(bad,index_path=index); self.assertFalse(r["pass"]); self.assertIn("LEARNING_MINING_AUTHORIZATION_FORBIDDEN",r["detected"])

if __name__=="__main__": unittest.main()