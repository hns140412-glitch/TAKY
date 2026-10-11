#!/usr/bin/env python3
import copy
import unittest
from grow_domain_router import load_registry,route,validate_registry

class GrowDomainRouterTest(unittest.TestCase):
    def setUp(self): self.r=load_registry()

    def test_registry_contains_both_domains(self):
        result=validate_registry(self.r)
        self.assertTrue(result["ok"])
        self.assertIn("ARCHI_GROW",self.r["domains"])
        self.assertIn("LEARNING_GROW",self.r["domains"])
        self.assertIn("SYSTEM_GROW",self.r["domains"])

    def test_registry_points_to_latest_current_index(self):
        pointer=self.r["shared_core"]["current_index"]
        self.assertEqual(pointer,"CURRENT/TAKY/TAKY_GROW_CURRENT_INDEX_2026-10-04_R2.json")
        self.assertTrue(validate_registry(self.r)["ok"])

    def test_stale_current_index_pointer_is_rejected(self):
        r=copy.deepcopy(self.r)
        r["shared_core"]["current_index"]="CURRENT/TAKY/TAKY_GROW_CURRENT_INDEX_2026-10-04.json"
        result=validate_registry(r)
        self.assertFalse(result["ok"])
        self.assertIn("GROW_CURRENT_INDEX_STALE",result["issues"])

    def test_architecture_routes_archigrow(self):
        x=route({"domain":"architecture","task_family":"design_competition","artifact_type":"drawing"},self.r)
        self.assertTrue(x["ok"]); self.assertEqual(x["grow_domain"],"ARCHI_GROW")
        self.assertFalse(x["authority_transfer"])

    def test_space_normalization_preserves_composite_scope(self):
        x=route({"task_family":"design competition"},self.r)
        self.assertTrue(x["ok"]); self.assertEqual(x["grow_domain"],"ARCHI_GROW")

    def test_learning_routes_learninggrow(self):
        x=route({"domain":"learning_engine","source_app":"hide_seek","task_family":"review_policy"},self.r)
        self.assertTrue(x["ok"]); self.assertEqual(x["grow_domain"],"LEARNING_GROW")
        self.assertFalse(x["authority_transfer"])

    def test_system_routes_systemgrow(self):
        x=route({"domain":"source_acquisition","task_family":"mining","owner":"ai_orchestration"},self.r)
        self.assertTrue(x["ok"]); self.assertEqual(x["grow_domain"],"SYSTEM_GROW")
        self.assertFalse(x["authority_transfer"])

    def test_substring_false_positive_is_rejected(self):
        x=route({"artifact_type":"combination","task_family":"reporting"},self.r)
        self.assertFalse(x["ok"]); self.assertIsNone(x["grow_domain"])

    def test_unknown_does_not_guess(self):
        x=route({"domain":"unknown","task_family":"other"},self.r)
        self.assertFalse(x["ok"]); self.assertIsNone(x["grow_domain"])

    def test_explicit_valid_domain(self):
        x=route({"grow_domain":"LEARNING_GROW","domain":"architecture"},self.r)
        self.assertTrue(x["ok"]); self.assertEqual(x["grow_domain"],"LEARNING_GROW")

if __name__=="__main__": unittest.main()
