#!/usr/bin/env python3
import unittest
from badge_cli_master_plan_v3 import make_plan,validate,all_members
class T(unittest.TestCase):
 def test_master(self):
  p=make_plan();self.assertEqual([],validate(p));self.assertEqual(60,len(all_members(p)))
  self.assertEqual(6,len(p["tracks"]["KEEP_VERIFY"]["batches"]));self.assertEqual(7,len(p["tracks"]["REWORK_GENERATE"]["batches"]))
 def test_keep_never_generates(self):
  p=make_plan();self.assertTrue(all(not m["generation_allowed"] for b in p["tracks"]["KEEP_VERIFY"]["batches"] for m in b["members"]))
 def test_no_duplicate(self):
  ids=[m["badge_id"] for m in all_members(make_plan())];self.assertEqual(60,len(set(ids)))
if __name__=="__main__":unittest.main()
