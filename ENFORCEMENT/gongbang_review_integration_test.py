import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from executor_review_loop import review
from gongbang_scope_gate_candidate import REQUIRED, _safe_open_supported


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.data = json.dumps({'task_id': 'T', 'revision': 'abc'}).encode()
        (self.root / 'ev.txt').write_bytes(self.data)

    def base(self):
        return {'task_id': 'T', 'change_scope': {'allowed': ['x.py']}, 'acceptance_tests': [], 'validation': {'required': []}, 'material_taky_turn': True, 'human_approval': {'merge_required': True}}, {'task_id': 'T', 'changed_files': ['x.py'], 'commit_ref': 'abc'}

    def evidence(self, ref='ev.txt', digest=None):
        digest = digest or hashlib.sha256(self.data).hexdigest()
        return {k: {'status': 'PASS', 'evidence_ref': ref, 'evidence_sha256': digest} for k in REQUIRED}

    def codes(self, result):
        return [d['code'] for d in result['defects']]

    def test_material_missing_is_rework(self):
        t, r = self.base()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('GONGBANG_SCOPE_INCOMPLETE', self.codes(result))

    def test_complete_verified_contract_review(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence()
        # Without provable swap-safety (e.g. Windows) the gate HOLDs, so review must not pass.
        self.assertEqual(review(t, r, self.root)['pass'], _safe_open_supported())

    def test_gongbang_required_flag_alone_triggers(self):
        t, r = self.base()
        t['material_taky_turn'] = False
        t['gongbang_required'] = True
        self.assertFalse(review(t, r, self.root)['pass'])

    def test_false_pass_fictitious_evidence_is_rework(self):
        t, r = self.base()
        r['gongbang_evidence'] = {k: {'status': 'PASS', 'evidence_ref': 'reference'} for k in REQUIRED}
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('GONGBANG_SCOPE_INCOMPLETE', self.codes(result))

    def test_tamper_is_rework(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence()
        (self.root / 'ev.txt').write_bytes(b'tampered')
        self.assertFalse(review(t, r, self.root)['pass'])

    def test_path_traversal_is_rework(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence(ref='../ev.txt')
        self.assertFalse(review(t, r, self.root)['pass'])

    def test_evidence_for_other_revision_is_rework(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence()
        r['commit_ref'] = 'zzz'
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('GONGBANG_SCOPE_INCOMPLETE', self.codes(result))

    def test_pass_does_not_claim_issuer_identity(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        if not _safe_open_supported():
            self.skipTest('PASS path requires fd-relative open')
        self.assertTrue(result['pass'])
        self.assertIn({'kind': 'gongbang', 'issuer': 'UNVERIFIED'}, result['evidence'])

    def test_unreadable_root_is_rework_not_exception(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root / 'does-not-exist')
        self.assertFalse(result['pass'])

    def test_unmarked_legacy_task_not_blocked(self):
        t, r = self.base()
        del t['material_taky_turn']
        self.assertTrue(review(t, r, self.root)['pass'])

    def test_optional_no_false_block(self):
        t, r = self.base()
        t['material_taky_turn'] = False
        self.assertTrue(review(t, r, self.root)['pass'])


if __name__ == '__main__':
    unittest.main()
