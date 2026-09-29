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
    def test_batch_01_is_source_locked(self):
        self.assertEqual([], self.check())
    def test_batch_01_cannot_falsely_claim_approval(self):
        from unittest.mock import patch
        import verify_visual_rework_queue as gate
        original=gate.Path.read_text
        def changed(path, *args, **kwargs):
            raw=original(path,*args,**kwargs)
            if str(path).endswith("rework-batch-01-source-locked.json"):
                document=json.loads(raw)
                document["items"][0]["final_approved"]=True
                return json.dumps(document)
            return raw
        with patch.object(gate.Path,"read_text",changed):
            self.assertIn("REWORK_BATCH_FALSE_COMPLETION",self.check())
    def test_batch_01_source_motif_change_rejected(self):
        from unittest.mock import patch
        import verify_visual_rework_queue as gate
        original=gate.Path.read_text
        def changed(path, *args, **kwargs):
            raw=original(path,*args,**kwargs)
            if str(path).endswith("rework-batch-01-source-locked.json"):
                document=json.loads(raw)
                document["items"][0]["source_motif"]="invented"
                return json.dumps(document)
            return raw
        with patch.object(gate.Path,"read_text",changed):
            self.assertIn("REWORK_BATCH_SOURCE_DRIFT",self.check())
    def test_netlify_hold(self):
        q=copy.deepcopy(self.q);q["netlify"]="READY"
        self.assertIn("RELEASE_HOLD_BYPASS",self.check(q=q))

if __name__=="__main__":
    unittest.main()
