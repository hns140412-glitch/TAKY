#!/usr/bin/env python3
import json, unittest
from pathlib import Path
from index_document_adapter import load_index_document
from index_retrieval import retrieve
from learning_orchestrator import orchestrate_learning
from mining_run_orchestrator import orchestrate as orchestrate_mining

FIX=Path(__file__).parent/"fixtures"/"index_runtime_projection_v24_666.json"

class ActualIndexCorpusE2ETest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.doc=json.loads(FIX.read_text(encoding="utf-8"))
  cls.loaded=load_index_document(cls.doc)
  cls.rows=cls.loaded["rows"]

 def test_loads_actual_666_projection(self):
  self.assertEqual(self.loaded["source_count"],666)
  self.assertEqual(self.loaded["loaded_count"],666)
  self.assertEqual(len({x["source_id"] for x in self.rows}),666)

 def test_exact_family_and_learning_retrieval(self):
  out=retrieve(self.rows,"초등 학습도구어",filters={"source_family":"ELEMENTARY_TOOL_LANGUAGE"},top_k=5)
  self.assertTrue(out["primary"])
  self.assertEqual(out["primary"][0]["source_id"],"1etdoU35AIduFqjXUqPfidMiQAfqzLoVS")

 def test_learning_orchestrator_uses_actual_corpus(self):
  out=orchestrate_learning({
   "evidence_request":{"query":"한자 어휘","minimum_results":1},
   "index_rows":self.rows,
   "context":{"learner_id":"C1","skill_id":"HANJA","learning_context":"한자 어휘 복습"},
   "observations":[{"correct":False},{"correct":False}],
  })
  self.assertTrue(out["retrieval"]["evidence_sufficient_for_review"])
  self.assertEqual(out["runtime"]["strategy_selection"]["strategy"],"TARGETED_REMEDIATION")
  self.assertIsNone(out["mining_request_candidate"])

 def test_mining_index_first_uses_actual_corpus(self):
  out=orchestrate_mining({
   "task":{"task_family":"LEARNING_ENGINE","goal":"find assessment authority","unknown":["초등학교 학생평가"]},
   "memory":{},
   "index_rows":self.rows,
  })
  self.assertGreaterEqual(out["plan"]["index_first"]["counts"]["resolved_from_index"],1)
  self.assertFalse(out["plan"]["external_search_required"])

if __name__=="__main__":
 unittest.main()
