#!/usr/bin/env python3
import unittest
from mining_provider_executor import build_execution_request
from mining_live_execution import normalize_runtime_result,execute_batch

class T(unittest.TestCase):
 def test_success_builds_receipt(self):
  req=build_execution_request({"frontier_id":"f","query":"q"},"WEB")
  r=normalize_runtime_result(req,{"state":"SUCCESS","response":{"results":[{"url":"https://example.gov/a","source_class":"OFFICIAL"}]}})
  self.assertEqual(r["state"],"SUCCESS"); self.assertEqual(len(r["receipt"]["results"]),1)

 def test_empty_is_preserved_not_failure(self):
  req=build_execution_request({"frontier_id":"f","query":"q"},"WEB")
  r=normalize_runtime_result(req,{"state":"EMPTY","response":{"results":[]}})
  self.assertEqual(r["state"],"EMPTY"); self.assertEqual(r["receipt"]["results"],[])

 def test_missing_runtime_result_fails_without_stopping_batch(self):
  req=build_execution_request({"frontier_id":"f","query":"q"},"GITHUB")
  b=execute_batch([req],{})
  self.assertEqual(b["failed_request_ids"],[req["request_id"]]); self.assertTrue(b["continue_allowed"])

 def test_partial_failure_keeps_success_receipt(self):
  a=build_execution_request({"frontier_id":"f","query":"q"},"PUBLIC_DATA")
  b=build_execution_request({"frontier_id":"f","query":"q"},"WEB")
  out=execute_batch([a,b],{
    a["request_id"]:{"state":"FAILED","error":"timeout"},
    b["request_id"]:{"state":"SUCCESS","response":{"results":[{"url":"https://example.gov/r","source_class":"OFFICIAL"}]}}
  })
  self.assertIn(a["request_id"],out["failed_request_ids"])
  self.assertIn(b["request_id"],out["successful_request_ids"])
  self.assertEqual(len(out["receipts"]),1)

if __name__=="__main__": unittest.main()
