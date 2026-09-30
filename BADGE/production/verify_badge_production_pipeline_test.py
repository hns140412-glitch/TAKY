#!/usr/bin/env python3
import copy,unittest
from verify_badge_production_pipeline import ROOT,load,verify

class PipelineGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=load("BADGE/production/badge-production-pipeline.json")
    def test_current_pipeline(self):
        self.assertEqual([],verify(ROOT,self.base))
    def test_display_item_drift_fails(self):
        p=copy.deepcopy(self.base);p["items"][0]["display_item"]="임의 제목"
        self.assertTrue(any("DISPLAY_ITEM" in e for e in verify(ROOT,p)))
    def test_core_detail_missing_fails(self):
        p=copy.deepcopy(self.base);p["items"][0]["core_detail"]=""
        self.assertTrue(any("CORE_DETAIL" in e for e in verify(ROOT,p)))
    def test_motif_drift_fails(self):
        p=copy.deepcopy(self.base);p["items"][0]["source_motif"]="generic sunrise"
        self.assertTrue(any("SOURCE_MOTIF" in e for e in verify(ROOT,p)))
    def test_character_cannot_be_baked(self):
        p=copy.deepcopy(self.base);p["items"][0]["base_art_policy"]="CHARACTER_ALLOWED"
        self.assertTrue(any("BASE_ART_POLICY" in e or "CHARACTER_BAKED" in e for e in verify(ROOT,p)))
    def test_overlay_policy_cannot_be_weakened(self):
        p=copy.deepcopy(self.base);p["items"][0]["character_overlay_policy"]="BAKED_OR_OPTIONAL"
        self.assertTrue(any("CHARACTER_OVERLAY_POLICY" in e for e in verify(ROOT,p)))
    def test_shared_ui_cannot_be_baked(self):
        p=copy.deepcopy(self.base);p["items"][0]["shared_ui_policy"]="BAKE_RIM_STARS"
        self.assertTrue(any("SHARED_UI_POLICY" in e for e in verify(ROOT,p)))
    def test_user_debug_loop_cannot_be_reintroduced(self):
        p=copy.deepcopy(self.base);p["invariants"]["no_user_debug_loop"]=False
        self.assertIn("PIPELINE_INVARIANTS_DRIFT",verify(ROOT,p))

if __name__=="__main__": unittest.main()
