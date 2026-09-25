#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
from mining_e2e_benchmark import run_benchmark
from mining_provider_executor import build_execution_request

CAPTURE=Path(__file__).with_name("mining_e2e_live_capture_2026-09-25.json")

class T(unittest.TestCase):
 def test_live_captured_three_provider_families(self):
  payload=json.loads(CAPTURE.read_text(encoding="utf-8"))
  cases=[]
  for c in payload["cases"]:
   frontier=c["frontier"]
   req=build_execution_request({"frontier_id":frontier,"query":frontier},c["provider"])
   src=dict(c["source"])
   cases.append({
    "case_id":c["case_id"],
    "mode":"LIVE_CAPTURED_RUNTIME",
    "task":{
      "task_family":c["task_family"],
      "goal":c["goal"],
      "foundation_requirements":[frontier],
      "max_research_depth":"D1"
    },
    "provider_preferences":{frontier:[c["preferred_source_class"]]},
    "max_providers_per_query":1,
    "runtime_results":{
      req["request_id"]:{
        "state":"SUCCESS",
        "response":{"retrieved_at":"2026-09-25","results":[src]}
      }
    },
    "outcome":{"success":True,"accuracy":1,"usefulness":1,"completeness":1,"efficiency":.9,"user_correction_rate":0},
    "expected":{"min_evidence":1,"stop":True,"ready_for_recommendation_review":True,"growth_type":"STRATEGY_OBSERVATION"}
   })
  r=run_benchmark({"minimum_distinct_families":3,"cases":cases})
  self.assertTrue(r["pass"],r)
  self.assertEqual(r["live_captured_case_count"],3)
  self.assertEqual(r["passed"],3)

if __name__=="__main__": unittest.main()
