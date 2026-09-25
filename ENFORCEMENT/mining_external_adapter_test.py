#!/usr/bin/env python3
import unittest
from mining_external_adapter import validate_receipt,ingest_receipt

class T(unittest.TestCase):
 def test_invalid_receipt_fails_closed(self):
  r=ingest_receipt({"query":"x","results":[]})
  self.assertFalse(r["accepted"]); self.assertIn("MISSING_FRONTIER_ID",r["errors"])

 def test_normalizes_provider_result(self):
  r=ingest_receipt({"frontier_id":"f1","query":"official rule","adapter":"WEB","results":[{"url":"https://example.gov/rule","title":"Rule","source_class":"OFFICIAL","claim":"A","direct_support":True}]})
  self.assertTrue(r["accepted"]); self.assertEqual(r["result_count"],1)
  e=r["evidence"][0]
  self.assertEqual(e["source_class"],"OFFICIAL"); self.assertEqual(e["source_domain"],"example.gov")
  self.assertTrue(e["direct_support"]); self.assertTrue(e["evidence_id"])

 def test_unknown_source_class_is_downgraded(self):
  r=ingest_receipt({"frontier_id":"f1","query":"x","results":[{"title":"x","source_class":"MAGIC"}]})
  self.assertEqual(r["evidence"][0]["source_class"],"UNKNOWN")

 def test_provider_independent_guard(self):
  r=ingest_receipt({"frontier_id":"f1","query":"x","adapter":"CUSTOM","results":[]})
  self.assertTrue(r["guards"]["provider_independent_contract"])

if __name__=="__main__": unittest.main()
