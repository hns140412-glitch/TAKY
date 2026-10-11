#!/usr/bin/env python3
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from producer_artifact_gate import preflight, postflight, _digest

class CharacterDerivativeProducerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'source.txt').write_text('approved source truth',encoding='utf-8')
        (self.root/'authority.txt').write_text('visual id authority',encoding='utf-8')
        self.contract={
            'kind':'character_derivative_asset',
            'task_id':'CREW-ASSET-TEST',
            'user_intent':'Produce derivative crew package',
            'output_path':'package.json',
            'source_ref':'source.txt',
            'authority_ref':'authority.txt',
            'protected_state':'approved Visual ID unchanged',
            'acceptance_plan':'Validate package manifest and evidence',
            'visual_witness_plan':'Render and compare actual derivative images',
            'producer':'AI',
        }

    def _asset(self,name,payload):
        p=self.root/name
        p.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    def _package(self):
        turn=self._asset('turnaround.png',b'turnaround-real')
        face=self._asset('face.png',b'face-real')
        action=self._asset('action.png',b'action-real')
        return {
            'schema':'TAKY_CHARACTER_DERIVATIVE_PACKAGE_V1',
            'visual_id':'CREW-19-LIN',
            'visual_id_revision':'REV-1',
            'identity_fingerprint':'fp:lin:001',
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
                'TURNAROUND':{'path':'turnaround.png','sha256':turn,'visual_id':'CREW-19-LIN','identity_fingerprint':'fp:lin:001','actual_image_review_pass':True,'production_gate_pass':True,'views':['FRONT','3/4','SIDE','BACK']},
                'FACE_SHEET':{'path':'face.png','sha256':face,'visual_id':'CREW-19-LIN','identity_fingerprint':'fp:lin:001','actual_image_review_pass':True,'production_gate_pass':True,'head_face_lock_verified':True,'identity_anchors':['eyes','nose','hair']},
                'ACTION_SHEET':{'path':'action.png','sha256':action,'visual_id':'CREW-19-LIN','identity_fingerprint':'fp:lin:001','actual_image_review_pass':True,'production_gate_pass':True,'body_identity_lock_verified':True,'may_redefine_body_identity':False,'actions':['READ_BOOK','RADIO']},
            },
        }

    def _evidence(self):
        output=self.root/'package.json'
        witnesses={}
        for key in ('source_trace','semantic_check','regression_check','delivery_check'):
            p=self.root/f'{key}.txt'
            p.write_text(key,encoding='utf-8')
            witnesses[key]={'passed':True,'evidence_path':p.name,'evidence_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        visual=self.root/'visual_check.png'
        visual.write_bytes(b'\x89PNG\r\n\x1a\n'+b'actual visual witness')
        witnesses['visual_check']={'passed':True,'evidence_path':visual.name,'evidence_sha256':hashlib.sha256(visual.read_bytes()).hexdigest()}
        return {'contract_sha256':_digest(self.contract),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),**witnesses}

    def test_valid_character_package_is_enforced_by_common_producer_gate(self):
        receipt=preflight(self.contract,self.root)
        self.assertTrue(receipt['pass'],receipt)
        (self.root/'package.json').write_text(json.dumps(self._package()),encoding='utf-8')
        result=postflight(self.contract,receipt,self._evidence(),self.root)
        self.assertTrue(result['pass'],result)

    def test_identity_drift_blocks_common_producer_postflight(self):
        receipt=preflight(self.contract,self.root)
        pkg=self._package()
        pkg['assets']['FACE_SHEET']['identity_fingerprint']='drift'
        (self.root/'package.json').write_text(json.dumps(pkg),encoding='utf-8')
        result=postflight(self.contract,receipt,self._evidence(),self.root)
        self.assertFalse(result['pass'])
        self.assertIn('CHARACTER_PACKAGE_FACE_SHEET_FINGERPRINT_MISMATCH',result['detected'])

    def test_missing_actual_image_review_blocks_common_producer_postflight(self):
        receipt=preflight(self.contract,self.root)
        pkg=self._package()
        pkg['qa']['actual_image_comparison_complete']=False
        (self.root/'package.json').write_text(json.dumps(pkg),encoding='utf-8')
        result=postflight(self.contract,receipt,self._evidence(),self.root)
        self.assertFalse(result['pass'])
        self.assertIn('CHARACTER_PACKAGE_ACTUAL_IMAGE_COMPARISON_REQUIRED',result['detected'])

if __name__=='__main__':
    unittest.main()
