#!/usr/bin/env python3
import copy,unittest
from verify_badge_production_standard_v2 import ROOT,load,verify,classify

class StandardV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=load("BADGE/production/badge-production-standard-v2.json")
    def test_current_standard(self):
        self.assertEqual([],verify(ROOT,self.base))
    def test_new_badge_defaults_unreviewed(self):
        c=classify(["A","B","NEW"],["B"],["A","B"])
        self.assertEqual(c["A"],"KEEP_CANDIDATE")
        self.assertEqual(c["B"],"REWORK_REQUIRED")
        self.assertEqual(c["NEW"],"NEW_UNREVIEWED")
    def test_first_award_must_be_one_star(self):
        s=copy.deepcopy(self.base);s["ownership_visual_states"]["FIRST_AWARD"]["star_count"]=0
        self.assertIn("FIRST_AWARD_ONE_STAR_RULE_DRIFT",verify(ROOT,s))
    def test_unearned_depth_forbidden(self):
        s=copy.deepcopy(self.base);s["ownership_visual_states"]["UNEARNED"]["detail_depth"]=True
        self.assertIn("UNEARNED_VISUAL_RULE_DRIFT",verify(ROOT,s))
    def test_depth_detail_only(self):
        s=copy.deepcopy(self.base);s["depth_detail_only"]["enabled_surface"]="ALL_SURFACES"
        self.assertIn("DEPTH_SCOPE_DRIFT",verify(ROOT,s))
    def test_layers_are_fixed_semantic_roles(self):
        s=copy.deepcopy(self.base);s["art_contract"]["required_depth_layers"]=["background","interior"]
        self.assertIn("DEPTH_LAYER_CONTRACT_DRIFT",verify(ROOT,s))
    def test_unapproved_candidate_never_renders(self):
        s=copy.deepcopy(self.base);s["ownership_visual_states"]["UNAPPROVED_ART"]["render"]=True
        self.assertIn("UNAPPROVED_ART_RENDER_FORBIDDEN",verify(ROOT,s))

if __name__=="__main__": unittest.main()
