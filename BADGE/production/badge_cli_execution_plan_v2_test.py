#!/usr/bin/env python3
import copy,unittest
from badge_cli_execution_plan_v2 import make_plan,validate,resumable_members,digest_obj
class PlanTests(unittest.TestCase):
    def test_plan_is_31_in_7_batches(self):
        p=make_plan();self.assertEqual([],validate(p));self.assertEqual(7,len(p["batches"]))
        self.assertEqual(31,sum(len(b["members"]) for b in p["batches"]))
    def test_failed_badge_is_resumable_without_restarting_passed(self):
        p=make_plan();p["batches"][0]["members"][0]["state"]="PASSED";p["batches"][0]["members"][1]["state"]="FAILED_ISOLATED"
        p["plan_sha256"]=digest_obj({k:v for k,v in p.items() if k!="plan_sha256"})
        r=resumable_members(p);self.assertNotIn(p["batches"][0]["members"][0]["badge_id"],r);self.assertIn(p["batches"][0]["members"][1]["badge_id"],r)
    def test_tampered_checkpoint_fails(self):
        p=make_plan();p["batches"][0]["members"][0]["attempt"]=99
        self.assertIn("PLAN_HASH_MISMATCH",validate(p))
    def test_overwrite_cannot_be_enabled(self):
        p=make_plan();p["overwrite"]=True;p["plan_sha256"]=digest_obj({k:v for k,v in p.items() if k!="plan_sha256"})
        self.assertIn("OVERWRITE_FORBIDDEN",validate(p))
if __name__=="__main__":unittest.main()
