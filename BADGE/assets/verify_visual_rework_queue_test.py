#!/usr/bin/env python3
import copy
import json
import unittest
from verify_visual_rework_queue import ROOT, verify

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class BadgeReworkTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=load("BADGE/assets/visual-rework-queue-working.json")
        cls.s=load("BADGE/badge-60-story-20-history-working.json")
        cls.r=load("BADGE/assets/asset-registry-working.json")
        cls.v=load("BADGE/badge-visual-registry-working.json")
    def check(self,q=None,s=None,r=None,v=None):
        return verify(q or self.q,s or self.s,r or self.r,v or self.v)
    def test_exact_source_rework_baseline(self):
        self.assertEqual([],self.check())
    def test_fake_approval_fails(self):
        q=copy.deepcopy(self.q);q["final_approved_count"]=1
        self.assertIn("FALSE_PROGRESS_FINAL_APPROVED_COUNT",self.check(q=q))
    def test_012_is_not_final(self):
        q=copy.deepcopy(self.q);q["special_state"]["BDG-DRAFT-012"]="FINAL"
        self.assertIn("012_040_CORRECTION_LOST",self.check(q=q))
    def test_040_is_not_approved(self):
        q=copy.deepcopy(self.q);q["special_state"]["BDG-DRAFT-040"]="APPROVED"
        self.assertIn("012_040_CORRECTION_LOST",self.check(q=q))
    def test_rework_id_cannot_be_dropped(self):
        q=copy.deepcopy(self.q);q["correction_ids"].remove("BDG-DRAFT-040")
        self.assertIn("REWORK_31_29_PARTITION",self.check(q=q))
    def test_activation_fails(self):
        r=copy.deepcopy(self.r);r["items"][0]["runtime_approved"]=True
        self.assertIn("PREMATURE_CANDIDATE_PROMOTION",self.check(r=r))
    def test_story_change_fails(self):
        r=copy.deepcopy(self.r);r["items"][11]["scene_motif"]="invented"
        self.assertIn("SOURCE_SEMANTIC_DRIFT",self.check(r=r))
    def test_netlify_hold(self):
        q=copy.deepcopy(self.q);q["netlify"]="READY"
        self.assertIn("RELEASE_HOLD_BYPASS",self.check(q=q))

if __name__=="__main__":
    unittest.main()
