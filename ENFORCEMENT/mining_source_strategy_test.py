#!/usr/bin/env python3
import unittest
from mining_source_strategy import infer_need,plan_sources,diversity_check
class T(unittest.TestCase):
 def test_rule_prefers_authority(self):
  p=plan_sources([{"id":"x","kind":"CONFLICT","question":"official regulation","status":"CONFLICT"}])[0]
  self.assertEqual(p["evidence_need"],"RULE"); self.assertEqual(p["preferred_source_classes"][:2],["PRIMARY","OFFICIAL"]); self.assertEqual(p["independent_sources_target"],2)
 def test_implementation_not_forced_to_official_only(self):
  self.assertEqual(infer_need({"kind":"ADVANCED","question":"runtime implementation"}),"IMPLEMENTATION")
 def test_community_experience_role(self):
  p=plan_sources([{"id":"x","question":"community experience review","status":"OPEN"}])[0]
  self.assertEqual(p["community_role"],"DIRECT_EXPERIENCE")
 def test_diversity(self):
  d=diversity_check([{"frontier_id":"x","source_identity":"a","source_class":"OFFICIAL"},{"frontier_id":"x","source_identity":"b","source_class":"COMMUNITY"}],"x")
  self.assertEqual(d["independent_source_count"],2); self.assertTrue(d["has_authoritative_source"])
if __name__=="__main__":unittest.main()
