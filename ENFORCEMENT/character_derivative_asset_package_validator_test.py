#!/usr/bin/env python3
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from character_derivative_asset_package_validator import validate_package, load_projection

class CharacterDerivativeAssetPackageValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.files={}
        for name,payload in [('turnaround.png',b'turnaround-bytes'),('face.png',b'face-bytes'),('action.png',b'action-bytes')]:
            p=self.root/name
            p.write_bytes(payload)
            self.files[name]=hashlib.sha256(payload).hexdigest()
        self.package={
            'schema':'TAKY_CHARACTER_DERIVATIVE_PACKAGE_V1',
            'visual_id':'CREW-19-LIN',
            'visual_id_revision':'REV-LOCKED-1',
            'identity_fingerprint':'fp:lin:approved:001',
            'approved_source_sha256':'a'*64,
            'registration_generated_reference_sheet_used':False,
            'external_reference_as_visual_authority':False,
            'qa':{
                'actual_image_comparison_complete':True,
                'cross_sheet_identity_match_pass':True,
                'color_material_lock_pass':True,
                'costume_equipment_lock_pass':True,
            },
            'assets':{
                'TURNAROUND':{
                    'path':'turnaround.png','sha256':self.files['turnaround.png'],
                    'visual_id':'CREW-19-LIN','identity_fingerprint':'fp:lin:approved:001',
                    'actual_image_review_pass':True,'production_gate_pass':True,
                    'views':['FRONT','3/4 VIEW','SIDE','BACK'],
                },
                'FACE_SHEET':{
                    'path':'face.png','sha256':self.files['face.png'],
                    'visual_id':'CREW-19-LIN','identity_fingerprint':'fp:lin:approved:001',
                    'actual_image_review_pass':True,'production_gate_pass':True,
                    'head_face_lock_verified':True,
                    'identity_anchors':['eyes','nose','hair'],
                },
                'ACTION_SHEET':{
                    'path':'action.png','sha256':self.files['action.png'],
                    'visual_id':'CREW-19-LIN','identity_fingerprint':'fp:lin:approved:001',
                    'actual_image_review_pass':True,'production_gate_pass':True,
                    'body_identity_lock_verified':True,
                    'may_redefine_body_identity':False,
                    'actions':['READ_BOOK','RADIO','REST'],
                },
            },
        }
        self.projection=load_projection()

    def check(self,pkg=None,projection=None):
        return validate_package(pkg or self.package,self.root,self.projection if projection is None else projection)

    def test_valid_three_sheet_package_passes_and_consumes_ref097(self):
        result=self.check()
        self.assertTrue(result['pass'],result)
        self.assertEqual(result['checked_roles'],['TURNAROUND','FACE_SHEET','ACTION_SHEET'])
        self.assertIn('INDEX:REF-097',result['supplemental_reference_sources'])
        self.assertIn('FOUR_VIEW_TURNAROUND',result['supplemental_pattern_ids'])
        self.assertEqual(result['authority'],'APPROVED_SOURCE_AND_VISUAL_ID_ONLY')

    def test_missing_action_sheet_blocks(self):
        pkg=copy.deepcopy(self.package)
        del pkg['assets']['ACTION_SHEET']
        self.assertIn('ACTION_SHEET_REQUIRED',self.check(pkg)['errors'])

    def test_cross_sheet_fingerprint_drift_blocks(self):
        pkg=copy.deepcopy(self.package)
        pkg['assets']['FACE_SHEET']['identity_fingerprint']='different'
        self.assertIn('FACE_SHEET_FINGERPRINT_MISMATCH',self.check(pkg)['errors'])

    def test_actual_file_hash_mismatch_blocks(self):
        pkg=copy.deepcopy(self.package)
        pkg['assets']['TURNAROUND']['sha256']='0'*64
        self.assertIn('TURNAROUND_SHA256_MISMATCH',self.check(pkg)['errors'])

    def test_generated_registration_reference_is_forbidden(self):
        pkg=copy.deepcopy(self.package)
        pkg['registration_generated_reference_sheet_used']=True
        self.assertIn('GENERATED_REFERENCE_SHEET_CANNOT_BE_REGISTRATION_AUTHORITY',self.check(pkg)['errors'])

    def test_external_reference_cannot_be_visual_authority(self):
        pkg=copy.deepcopy(self.package)
        pkg['external_reference_as_visual_authority']=True
        self.assertIn('EXTERNAL_REFERENCE_VISUAL_AUTHORITY_FORBIDDEN',self.check(pkg)['errors'])

    def test_projection_cannot_escalate_authority(self):
        projection=copy.deepcopy(self.projection)
        projection['authority']='VISUAL_AUTHORITY'
        result=self.check(projection=projection)
        self.assertIn('REFERENCE_AUTHORITY_ESCALATION',result['errors'])

    def test_turnaround_requires_four_identity_views(self):
        pkg=copy.deepcopy(self.package)
        pkg['assets']['TURNAROUND']['views']=['FRONT','SIDE','BACK']
        self.assertIn('TURNAROUND_REQUIRED_VIEWS_MISSING:THREE_QUARTER',self.check(pkg)['errors'])

    def test_action_sheet_cannot_redefine_body(self):
        pkg=copy.deepcopy(self.package)
        pkg['assets']['ACTION_SHEET']['may_redefine_body_identity']=True
        self.assertIn('ACTION_SHEET_MAY_NOT_REDEFINE_BODY_IDENTITY',self.check(pkg)['errors'])

    def test_path_escape_blocks(self):
        pkg=copy.deepcopy(self.package)
        pkg['assets']['FACE_SHEET']['path']='../outside.png'
        self.assertIn('FACE_SHEET_PATH_ESCAPES_ROOT',self.check(pkg)['errors'])

if __name__=='__main__':
    unittest.main()
