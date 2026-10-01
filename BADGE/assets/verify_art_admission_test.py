#!/usr/bin/env python3
"""Negative admission tests: claims, fake evidence and wrong sources never become artwork."""
import copy
import unittest
from verify_art_admission import ROOT, read, verify, check_circle_png, exact_file
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image

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
        self.assertIn("001_base_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_bg_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_subject_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_fx_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_composite_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_REVIEW_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_DEPTH_PROFILE_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_INDIVIDUAL_MANIFEST_FILE_IDENTITY_REQUIRED",problems)
        self.assertIn("001_PREVIEW_SET_MISSING",problems)
        self.assertIn("ART_ADMISSION_SOURCE_OR_WIT_DRIFT_001",problems)
    def test_conditional_29_share_same_admission_route(self):
        d=copy.deepcopy(self.empty);d["status"]="REVIEWED_ART_UNBOUND"
        d["items"]=[{"badge_id":"BDG-DRAFT-002"}]
        problems=verify(ROOT,d)
        self.assertNotIn("INVALID_OR_DUPLICATE_BADGE_ID",problems)
        self.assertIn("002_REFERENCE_FILE_IDENTITY_REQUIRED",problems)
    def test_declared_release_is_blocked(self):
        d=copy.deepcopy(self.empty);d["deployment"]="READY"
        self.assertIn("ART_ADMISSION_SCHEMA_OR_DEPLOY_HOLD",verify(ROOT,d))
    def test_opaque_square_is_rejected_from_actual_pixels(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.png"
            Image.new("RGBA",(1024,1024),(20,30,40,255)).save(path)
            issues=[]
            check_circle_png(path,1024,issues,"001_composite")
            self.assertIn("001_composite_OUTSIDE_CIRCLE_NOT_TRANSPARENT",issues)
    def test_wrong_alpha_or_dimensions_rejected(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.png"
            Image.new("RGB",(800,800),(20,30,40)).save(path)
            issues=[]
            check_circle_png(path,1024,issues,"001_composite")
            self.assertIn("001_composite_SIZE_OR_RGBA",issues)
    def test_fake_hash_is_rejected_even_when_file_exists(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"BADGE/assets/individual/001/base.png"
            path.parent.mkdir(parents=True)
            Image.new("RGBA",(1024,1024),(0,0,0,0)).save(path)
            issues=[]
            found=exact_file(Path(tmp),{"path":"BADGE/assets/individual/001/base.png","sha256":"0"*64},
                             "BADGE/assets/individual/001/",(".png",),issues,"001_base")
            self.assertIsNone(found)
            self.assertIn("001_base_MISSING_OR_HASH_MISMATCH",issues)
    def test_four_digit_badge_slot_is_not_truncated(self):
        from verify_art_admission import slot_for_badge_id
        self.assertEqual("1000",slot_for_badge_id("BDG-DRAFT-1000"))
    def test_no_unknown_empty_items_shape(self):
        d=copy.deepcopy(self.empty);d["items"]=None
        self.assertEqual(["ART_ADMISSION_ITEMS_REQUIRED"],verify(ROOT,d))

if __name__=="__main__": unittest.main()
