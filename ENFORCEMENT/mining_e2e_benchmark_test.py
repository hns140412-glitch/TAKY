#!/usr/bin/env python3
import unittest
from mining_e2e_benchmark import run_benchmark
from mining_provider_executor import build_execution_request

def runtime_for(frontier_id,query,provider="WEB",claim="ok",source_class="OFFICIAL"):
    req=build_execution_request({"frontier_id":frontier_id,"query":query},provider)
    return req["request_id"],{"state":"SUCCESS","response":{"results":[{"url":"https://example.gov/source","title":"source","source_class":source_class,"claim":claim,"direct_support":True,"independent_support_count":2}]}}    

class T(unittest.TestCase):
 def test_three_family_e2e_pipeline(self):
  cases=[]
  for cid,fam,goal in [("A","ARCHITECTURE_REGULATION","verify setback rule"),("B","DEVICE_PROCUREMENT","compare scanner workflow"),("C","MOTION_REFERENCE","find runtime interaction reference")]:
   frontier_id=f"{goal}: definition".replace(" ","_").lower()
   rid,rr=runtime_for(frontier_id,f"{goal}: definition","PUBLIC_DATA" if fam=="ARCHITECTURE_REGULATION" else "WEB")
   cases.append({
    "case_id":cid,
    "task":{"task_family":fam,"goal":goal,"foundation_requirements":[f"{goal}: definition"],"max_research_depth":"D1"},
    "runtime_results":{rid:rr},
    "max_providers_per_query":1,
    "outcome":{"success":True,"accuracy":1,"usefulness":1,"completeness":1,"efficiency":.9,"user_correction_rate":0},
    "expected":{"min_evidence":1,"growth_type":"STRATEGY_OBSERVATION"}
   })
  r=run_benchmark({"minimum_distinct_families":3,"cases":cases})
  self.assertTrue(r["pass"],r)
  self.assertEqual(r["passed"],3)

 def test_empty_suite_fails(self):
  self.assertFalse(run_benchmark({"cases":[]})["pass"])

if __name__=="__main__":unittest.main()
