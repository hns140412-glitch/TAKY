#!/usr/bin/env python3
"""Negative admission tests: claims, fake evidence and wrong sources never become artwork."""
import copy
import unittest
from verify_art_admission import ROOT, read, verify

class BadgeArtAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty=read(ROOT,"BADGE/assets/production-art-admission.json")
    def test_current_draft_zero_admitted(self):
        self.assertEqual([],verify(ROOT,self.empty))
    def test_fake_reviewed_state_rejected_without_files(self):
        d=copy.deepcopy(self.empty);d["status"]="REVIEWED_ART_UNBOUND"
        self.assertIn("EMPTY_ADMISSION_CANNOT_BE_REVIEWED",verify(ROOT,d))
    def test_missing_physical_files_cannot_be_claimed(self):
        d=copy.deepcopy(self.empty);d["status"]="REVIEWED_ART_UNBOUND"
        d["items"]=[{"badge_id":"BDG-DRAFT-001","layers":{},"previews":{}}]
        problems=verify(ROOT,d)
        self.assertIn("001_REFERENCE_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_background_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_interior_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_composite_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_REVIEW_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_PREVIEW_SET_MISSING",problems)
        self.assertIn("ART_ADMISSION_SOURCE_OR_WIT_DRIFT_001",problems)
    def test_conditional_29_not_mistaken_for_corrections(self):
        d=copy.deepcopy(self.empty);d["status"]="REVIEWED_ART_UNBOUND"
        d["items"]=[{"badge_id":"BDG-DRAFT-002"}]
        self.assertIn("INVALID_OR_DUPLICATE_REWORK_ID",verify(ROOT,d))
    def test_declared_release_is_blocked(self):
        d=copy.deepcopy(self.empty);d["deployment"]="READY"
        self.assertIn("ART_ADMISSION_SCHEMA_OR_DEPLOY_HOLD",verify(ROOT,d))
    def test_no_unknown_empty_items_shape(self):
        d=copy.deepcopy(self.empty);d["items"]=None
        self.assertEqual(["ART_ADMISSION_ITEMS_REQUIRED"],verify(ROOT,d))

if __name__=="__main__": unittest.main()
