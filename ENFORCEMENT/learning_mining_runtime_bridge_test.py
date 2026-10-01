#!/usr/bin/env python3
import unittest
from learning_mining_runtime_bridge import plan,advance

ROUTE={
 "pass":True,"gap_id":"G1","index_sufficient":False,"decision":"MINING_REQUEST",
 "mining_request":{
  "gap_id":"G1","gap_type":"REFERENCE_EVIDENCE_REQUIRED",
  "scope":{"member_id":"A","subject":"science","concept_skill_target":"climate"},
  "query_terms":["science","climate","official"],
  "requested_capability":"EXTERNAL_REFERENCE_EVIDENCE",
  "acceptable_source_families":["OFFICIAL_STANDARDS"],
  "acceptable_authority_classes":["OFFICIAL"],
  "required_provenance":["OFFICIAL_SOURCE_REF"]
 }
}
class TestBridge(unittest.TestCase):
 def test_index_gated_request_becomes_mining_plan_without_network(self):
  r=plan(ROUTE,index_rows=[])
  self.assertTrue(r["pass"])
  self.assertTrue(r["mining_required"])
  self.assertEqual(r["mining"]["schema"],"TAKY_MINING_RUN_ORCHESTRATOR_V1")
  self.assertTrue(r["guards"]["index_gate_preserved"])
  self.assertFalse(r["guards"]["network_io_performed"])
  self.assertTrue(r["mining"]["plan"]["external_search_required"])

 def test_provider_results_are_required_for_advance(self):
  r=advance(ROUTE,{},index_rows=[])
  self.assertTrue(r["pass"])
  self.assertIn(r["advance"]["state"],{"WAIT_RUNTIME_RESULT","NO_PROVIDER_ACTION"})
  self.assertTrue(r["guards"]["provider_results_must_be_runtime_supplied"])

 def test_non_mining_route_is_noop(self):
  r=plan({"pass":True,"decision":"INDEX_REQUERY","index_sufficient":True})
  self.assertTrue(r["pass"])
  self.assertFalse(r["mining_required"])

if __name__=="__main__": unittest.main()
