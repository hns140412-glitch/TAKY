import hashlib
import tempfile
import unittest
from pathlib import Path
from architecture_work_os_proof import preflight

class ProofTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.packet={'source_owner':'WORK_OS','state':'PASS','project':{'project_id':'fixture-project', 'revision_id':'fixture-rev',
          'trial_receipt_id':'fixture-trial','outcome_receipt_id':'fixture-outcome'},'comparison':{'baseline':5,'observed':3,'unit':'errors'},'evidence':[]}
        for role in ('SOURCE_MANIFEST','WORK_OS_ARTIFACT','INDEPENDENT_QA','REGRESSION'):
            name=role+'.txt'; body=('synthetic fixture:'+role).encode(); (self.root/name).write_bytes(body)
            self.packet['evidence'].append({'role':role,'relative_path':name,'sha256':hashlib.sha256(body).hexdigest()})
    def test_bytes_preflight_does_not_promote(self):
        r=preflight(self.packet,self.root)
        self.assertEqual(r['problems'],[]);self.assertFalse(r['automatic_promotion'])
    def test_tampered_bytes_fail(self):
        (self.root/'INDEPENDENT_QA.txt').write_text('tampered')
        self.assertIn('HASH_MISMATCH:INDEPENDENT_QA',preflight(self.packet,self.root)['problems'])
    def test_missing_proof_for_pass(self):
        self.packet['evidence']=[e for e in self.packet['evidence'] if e['role']!='REGRESSION']
        self.assertIn('PASS_PROOF_MISSING:REGRESSION',preflight(self.packet,self.root)['problems'])
    def test_not_work_os(self):
        self.packet['source_owner']='ARCHI_GROW'
        self.assertIn('WORK_OS_OWNER_REQUIRED',preflight(self.packet,self.root)['problems'])
    def test_no_project_revision(self):
        self.packet['project']['revision_id']=''
        self.assertIn('MISSING_PROJECT_IDENTITY:revision_id',preflight(self.packet,self.root)['problems'])
    def test_path_escape(self):
        self.packet['evidence'][0]['relative_path']='../x'
        self.assertIn('PATH_ESCAPE:SOURCE_MANIFEST',preflight(self.packet,self.root)['problems'])
    def test_empty_evidence_rejected(self):
        e=self.packet['evidence'][0]
        (self.root/e['relative_path']).write_bytes(b'')
        e['sha256']=hashlib.sha256(b'').hexdigest()
        self.assertIn('EVIDENCE_FILE_EMPTY:SOURCE_MANIFEST',preflight(self.packet,self.root)['problems'])
    def test_reused_file_under_different_role_rejected(self):
        a,b=self.packet['evidence'][:2]
        b['relative_path']=a['relative_path']; b['sha256']=a['sha256']
        self.assertIn('EVIDENCE_FILE_REUSED:WORK_OS_ARTIFACT',preflight(self.packet,self.root)['problems'])
    def test_nan_metric_rejected(self):
        self.packet['comparison']['observed']=float('nan')
        self.assertIn('NONFINITE_COMPARISON_VALUE',preflight(self.packet,self.root)['problems'])
    def test_no_metric(self):
        self.packet.pop('comparison')
        self.assertIn('NUMERIC_BASELINE_OUTCOME_REQUIRED',preflight(self.packet,self.root)['problems'])

if __name__=='__main__':unittest.main()
