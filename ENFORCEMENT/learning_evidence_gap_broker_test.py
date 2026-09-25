#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from learning_evidence_gap_broker import route_gap

GAP={
    "gap_id":"A:영어:VOCABULARY:LEARNER_EVIDENCE_SPARSE",
    "owner":"LEARNING_ENGINE_CORE",
    "gap_type":"LEARNER_EVIDENCE_SPARSE",
    "priority":"MEDIUM",
    "scope":{"member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY"},
    "index_check_required":True,
    "mining_request_authorized":False,
    "requested_capability":"LEARNING_EVIDENCE_SUPPORT",
    "query_terms":["영어","VOCABULARY"],
    "existing_source_refs":[]
}

def write_index(path, rows):
    path.write_text(json.dumps({"sources":rows},ensure_ascii=False),encoding="utf-8")

class GapBrokerTest(unittest.TestCase):
    def test_index_sufficient_blocks_mining(self):
        with tempfile.TemporaryDirectory() as td:
            index=Path(td)/"index.json"
            write_index(index,[{
                "source_id":"SRC-ENG-1",
                "title":"영어 VOCABULARY 공식 자료",
                "source_family":"OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS",
                "source_type":"OFFICIAL_CURRICULUM",
                "authority_level":"OFFICIAL",
                "keywords":["영어","VOCABULARY"]
            }])
            result=route_gap(GAP,index_path=index,min_results=1)
            self.assertTrue(result["pass"])
            self.assertEqual(result["decision"],"INDEX_REQUERY")
            self.assertIsNone(result["mining_request"])
            self.assertTrue(result["index_sufficient"])

    def test_index_insufficient_emits_mining_request(self):
        with tempfile.TemporaryDirectory() as td:
            index=Path(td)/"index.json"
            write_index(index,[{
                "source_id":"SRC-MATH-1",
                "title":"수학 분수 자료",
                "source_family":"MATH",
                "keywords":["수학","분수"]
            }])
            result=route_gap(GAP,index_path=index,min_results=1)
            self.assertTrue(result["pass"])
            self.assertEqual(result["decision"],"MINING_REQUEST")
            self.assertFalse(result["index_sufficient"])
            req=result["mining_request"]
            self.assertEqual(req["requester"],"LEARNING_ENGINE")
            self.assertTrue(req["index_check"]["performed"])
            self.assertIn("INDEXING_OWNS_PERSISTENT_CLASSIFICATION",req["constraints"])
            self.assertIn("LEARNING_OWNS_FINAL_EVIDENCE_USE_DECISION",req["constraints"])

    def test_learning_cannot_authorize_mining(self):
        with tempfile.TemporaryDirectory() as td:
            index=Path(td)/"index.json"
            write_index(index,[])
            bad=dict(GAP)
            bad["mining_request_authorized"]=True
            result=route_gap(bad,index_path=index)
            self.assertFalse(result["pass"])
            self.assertIn("LEARNING_MINING_AUTHORIZATION_FORBIDDEN",result["detected"])

if __name__=="__main__":
    unittest.main()
