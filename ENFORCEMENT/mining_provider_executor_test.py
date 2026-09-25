#!/usr/bin/env python3
import unittest
from mining_provider_executor import build_execution_request,provider_response_to_receipt

class T(unittest.TestCase):
 def test_unsupported_provider_fails(self):
  self.assertFalse(build_execution_request({"frontier_id":"f","query":"q"},"X")["valid"])

 def test_build_request(self):
  r=build_execution_request({"frontier_id":"f","query":"official rule","purpose":"FILL_EVIDENCE_GAP"},"WEB")
  self.assertEqual(r["provider"],"WEB"); self.assertEqual(r["frontier_id"],"f"); self.assertTrue(r["request_id"])

 def test_github_defaults_implementation(self):
  req=build_execution_request({"frontier_id":"f","query":"runtime example"},"GITHUB")
  rec=provider_response_to_receipt(req,{"results":[{"html_url":"https://github.com/x/y","name":"repo"}]})
  self.assertEqual(rec["results"][0]["source_class"],"IMPLEMENTATION")

 def test_public_data_defaults_official(self):
  req=build_execution_request({"frontier_id":"f","query":"dataset"},"PUBLIC_DATA")
  rec=provider_response_to_receipt(req,{"results":[{"url":"https://data.example/x","title":"dataset"}]})
  self.assertEqual(rec["results"][0]["source_class"],"OFFICIAL")

 def test_web_gov_domain_classifies_official(self):
  req=build_execution_request({"frontier_id":"f","query":"law"},"WEB")
  rec=provider_response_to_receipt(req,{"results":[{"url":"https://law.example.gov/rule"}]})
  self.assertEqual(rec["results"][0]["source_class"],"OFFICIAL")

if __name__=="__main__": unittest.main()
