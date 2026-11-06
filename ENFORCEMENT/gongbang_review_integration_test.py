import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from executor_review_loop import review as _review, sign_review_receipt, verify_review_receipt
from gongbang_scope_gate_candidate import REQUIRED, _safe_open_supported

KEY = 'verifier-held-secret-key-0123456789'


def review(task, report, root=None, receipt_key=KEY):
    return _review(task, report, root, receipt_key=receipt_key)


INTENT = 'Keep the photo-processing PIPELINE; do not replace it with a webapp.'


def _git(root, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args],
                          cwd=root, capture_output=True, text=True, check=True).stdout.strip()


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _git(self.root, 'init', '-q')
        (self.root / 'seed.txt').write_text('seed')
        (self.root / 'x.py').write_bytes(b'original source')
        _git(self.root, 'add', 'seed.txt', 'x.py')
        _git(self.root, 'commit', '-q', '-m', 'seed')
        self.sha = _git(self.root, 'rev-parse', 'HEAD')
        self.data = json.dumps({'task_id': 'T', 'revision': self.sha}).encode()
        (self.root / 'ev.txt').write_bytes(self.data)
        self.write_review()

    def review_doc(self, **override):
        doc = {'task_id': 'T', 'revision': self.sha, 'reviewer_kind': 'codex',
               'reviewer_id': 'codex-reviewer', 'reviewer_session_id': 'sess-1',
               'review_scope': 'ORIGINAL_SOURCE', 'verdict': 'PASS',
               'source_path': 'x.py',
               'source_sha256': hashlib.sha256(b'original source').hexdigest(),
               'intent_sha256': hashlib.sha256(INTENT.encode()).hexdigest(),
               'intent_verdict': 'MATCH'}
        doc.update(override)
        return doc

    def write_review(self, _receipt=True, **override):
        doc = self.review_doc(**override)
        if _receipt:
            doc['provider_receipt'] = sign_review_receipt(doc, 'taky-verifier', KEY)
        data = json.dumps(doc).encode()
        (self.root / 'review.json').write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def base(self):
        return ({'task_id': 'T', 'change_scope': {'allowed': ['x.py']}, 'acceptance_tests': [],
                 'validation': {'required': []}, 'material_taky_turn': True,
                 'human_approval': {'merge_required': True},
                 'original_user_intent': {'source': 'user', 'text': INTENT}},
                {'task_id': 'T', 'changed_files': ['x.py'], 'commit_ref': self.sha,
                 'executor_id': 'claude-executor'})

    def evidence(self, ref='ev.txt', digest=None):
        digest = digest or hashlib.sha256(self.data).hexdigest()
        out = {k: {'status': 'PASS', 'evidence_ref': ref, 'evidence_sha256': digest} for k in REQUIRED}
        out['independent_review'] = {'status': 'PASS', 'evidence_ref': 'review.json',
                                     'evidence_sha256': hashlib.sha256((self.root / 'review.json').read_bytes()).hexdigest()}
        return out

    def full(self):
        t, r = self.base()
        r['gongbang_evidence'] = self.evidence()
        return t, r

    def provenance(self, result):
        return [d for d in result['defects'] if d['code'] == 'INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED']

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
        r['commit_ref'] = 'abc'  # legacy path keeps its old non-strict behaviour
        self.assertTrue(review(t, r, self.root)['pass'])

    # --- anti-rubber-stamp attacks (material tasks) ---

    def test_nonexistent_commit_is_rework(self):
        t, r = self.full()
        for bad in ('deadbeefdeadbeef', 'abc', 'local-only-unmerged', '--help', 'HEAD'):
            r['commit_ref'] = bad
            result = review(t, r, self.root)
            self.assertFalse(result['pass'], bad)
            self.assertIn('COMMIT_REF_NOT_FOUND', self.codes(result), bad)

    def test_self_reported_string_pass_is_rework(self):
        t, r = self.full()
        t['acceptance_tests'] = ['crit']
        t['validation'] = {'required': ['gate']}
        r['acceptance_results'] = [{'criterion': 'crit', 'status': 'PASS', 'evidence': 'trust me'}]
        r['validation_results'] = {'gate': {'status': 'PASS', 'evidence': 'ran it, honest'}}
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        kinds = {(d['kind'], d['name']) for d in result['defects'] if d['code'] == 'PASS_CLAIM_UNVERIFIED'}
        self.assertEqual(kinds, {('acceptance', 'crit'), ('validation', 'gate')})

    def test_pass_claim_with_tampered_hash_is_rework(self):
        t, r = self.full()
        t['acceptance_tests'] = ['crit']
        r['acceptance_results'] = [{'criterion': 'crit', 'status': 'PASS', 'evidence': 'x',
                                    'evidence_ref': 'ev.txt', 'evidence_sha256': '0' * 64}]
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('PASS_CLAIM_UNVERIFIED', self.codes(result))

    def test_missing_review_record_has_no_provenance(self):
        t, r = self.full()
        del r['gongbang_evidence']['independent_review']
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertTrue(self.provenance(result))

    def test_executor_reviewing_itself_is_rework(self):
        t, r = self.base()
        self.write_review(reviewer_id='Claude-Executor')
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('REVIEWER_IS_EXECUTOR', self.provenance(result)[0]['reason'])

    def test_unknown_reviewer_or_missing_identity_is_rework(self):
        for override in ({'reviewer_kind': 'self'}, {'reviewer_session_id': ''}, {'reviewer_id': ''}):
            t, r = self.base()
            self.write_review(**override)
            r['gongbang_evidence'] = self.evidence()
            result = review(t, r, self.root)
            self.assertFalse(result['pass'], override)
            self.assertTrue(self.provenance(result), override)

    def test_missing_executor_id_is_rework(self):
        t, r = self.full()
        del r['executor_id']
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('EXECUTOR_ID_MISSING', self.provenance(result)[0]['reason'])

    def test_limited_excerpt_review_is_not_independent(self):
        t, r = self.base()
        self.write_review(review_scope='LIMITED')
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('REVIEW_SCOPE_NOT_ORIGINAL_SOURCE', self.provenance(result)[0]['reason'])

    def test_non_pass_review_verdict_is_rework(self):
        t, r = self.base()
        self.write_review(verdict='FAIL')
        r['gongbang_evidence'] = self.evidence()
        self.assertFalse(review(t, r, self.root)['pass'])

    def test_missing_or_assistant_authored_intent_is_rework(self):
        for intent in (None, '', {'source': 'assistant', 'text': INTENT}, {'source': 'user', 'text': ' '}):
            t, r = self.full()
            if intent is None:
                del t['original_user_intent']
            else:
                t['original_user_intent'] = intent
            result = review(t, r, self.root)
            self.assertFalse(result['pass'], intent)
            self.assertIn('ORIGINAL_USER_INTENT_MISSING', self.codes(result), intent)

    def test_review_not_compared_to_this_intent_is_rework(self):
        for override in ({'intent_sha256': hashlib.sha256(b'build a webapp').hexdigest()},
                         {'intent_verdict': 'MISMATCH'}, {'intent_sha256': None}):
            t, r = self.base()
            self.write_review(**override)
            r['gongbang_evidence'] = self.evidence()
            result = review(t, r, self.root)
            self.assertFalse(result['pass'], override)
            self.assertIn('ORIGINAL_INTENT_NOT_COMPARED', self.codes(result), override)

    def test_review_record_tampered_after_hashing_is_rework(self):
        t, r = self.full()
        self.write_review(reviewer_id='someone-else')
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertTrue(self.provenance(result))

    # --- valid positive ---

    def test_independent_verified_intent_matched_review_has_no_new_defects(self):
        t, r = self.full()
        t['acceptance_tests'] = ['crit']
        r['acceptance_results'] = [{'criterion': 'crit', 'status': 'PASS', 'evidence': 'x',
                                    'evidence_ref': 'ev.txt',
                                    'evidence_sha256': hashlib.sha256(self.data).hexdigest()}]
        result = review(t, r, self.root)
        new = {'COMMIT_REF_NOT_FOUND', 'PASS_CLAIM_UNVERIFIED', 'ORIGINAL_USER_INTENT_MISSING',
               'INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED', 'ORIGINAL_INTENT_NOT_COMPARED'}
        if _safe_open_supported():
            self.assertTrue(result['pass'], result['defects'])
            self.assertEqual(result['commit_ref'], self.sha)
        else:  # Windows cannot prove swap-safety, so verified refs HOLD rather than PASS.
            self.assertFalse(result['pass'])
        self.assertFalse(new & set(self.codes(result)) - {'PASS_CLAIM_UNVERIFIED'})
        if _safe_open_supported():
            self.assertNotIn('PASS_CLAIM_UNVERIFIED', self.codes(result))

    # --- identity authentication: claimed reviewer ID/session/source hash is not proof ---

    def test_self_attested_review_without_receipt_is_hold_not_pass(self):
        t, r = self.base()
        self.write_review(_receipt=False)
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertNotEqual(result['review_decision'], 'HUMAN_APPROVAL')
        self.assertIs(result['independent_pass_verified'], False)
        if _safe_open_supported():  # everything else verifies, so only identity is outstanding
            self.assertEqual(result['review_decision'], 'HOLD')
            self.assertEqual(result['defects'], [])
            self.assertEqual(result['holds'][0]['code'], 'REVIEWER_IDENTITY_UNAUTHENTICATED')
            self.assertFalse(result['holds'][0]['verified'])

    def test_receipt_without_verifier_key_is_hold_not_pass(self):
        t, r = self.full()
        result = review(t, r, self.root, receipt_key='')
        self.assertFalse(result['pass'])
        self.assertIs(result['independent_pass_verified'], False)
        if _safe_open_supported():
            self.assertEqual(result['review_decision'], 'HOLD')
            self.assertIn('NO_VERIFIER_KEY_CONFIGURED', result['holds'][0]['reason'])

    def test_forged_receipt_signed_with_other_key_is_hold(self):
        t, r = self.base()
        doc = self.review_doc()
        doc['provider_receipt'] = sign_review_receipt(doc, 'taky-verifier', 'executor-guessed-key-000000000')
        data = json.dumps(doc).encode()
        (self.root / 'review.json').write_bytes(data)
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIs(result['independent_pass_verified'], False)
        if _safe_open_supported():
            self.assertIn('PROVIDER_RECEIPT_SIGNATURE_INVALID', result['holds'][0]['reason'])

    def test_receipt_verification_is_platform_independent(self):
        doc = self.review_doc()
        doc['provider_receipt'] = sign_review_receipt(doc, 'taky-verifier', KEY)
        ok = lambda d, **kw: verify_review_receipt(d, kw.get('task', 'T'), kw.get('rev', self.sha),
                                                   kw.get('executor', 'claude-executor'), kw.get('key', KEY))
        self.assertEqual(ok(doc), [])
        self.assertEqual(ok(doc, key=None), ['NO_VERIFIER_KEY_CONFIGURED'])
        self.assertEqual(ok(doc, key='short'), ['NO_VERIFIER_KEY_CONFIGURED'])
        self.assertEqual(ok(doc, key='another-verifier-key-0123456789'), ['PROVIDER_RECEIPT_SIGNATURE_INVALID'])
        self.assertIn('RECEIPT_TASK_MISMATCH', ok(doc, task='OTHER'))
        self.assertIn('RECEIPT_REVISION_MISMATCH', ok(doc, rev='0' * 40))
        self.assertIn('RECEIPT_ISSUER_NOT_INDEPENDENT', ok(doc, executor='Taky-Verifier'))

    def test_post_signature_edits_invalidate_receipt(self):
        doc = self.review_doc()
        doc['provider_receipt'] = sign_review_receipt(doc, 'taky-verifier', KEY)
        for field, value in (('reviewer_id', 'someone-else'), ('reviewer_session_id', 'sess-2'),
                             ('source_sha256', '1' * 64), ('verdict', 'FAIL')):
            tampered = dict(doc, **{field: value})
            self.assertEqual(verify_review_receipt(tampered, 'T', self.sha, 'claude-executor', KEY),
                             ['PROVIDER_RECEIPT_SIGNATURE_INVALID'], field)
        self.assertEqual(verify_review_receipt({k: v for k, v in doc.items() if k != 'provider_receipt'},
                                               'T', self.sha, 'claude-executor', KEY),
                         ['PROVIDER_RECEIPT_MISSING_SELF_ATTESTED_ONLY'])

    def test_authenticated_sha_claim_for_different_source_is_rejected(self):
        """Valid provider MAC must not authenticate an unrelated source blob."""
        t, r = self.full()
        self.write_review(source_sha256=hashlib.sha256(b'unrelated code').hexdigest())
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED', self.codes(result))
        self.assertIn('REVIEW_SOURCE_HASH_NOT_BOUND_TO_COMMIT',
                      self.provenance(result)[0]['reason'])

    def test_authenticated_review_of_unlisted_source_is_rejected(self):
        """A signed review cannot silently substitute an unrelated source file."""
        t, r = self.full()
        self.write_review(source_path='seed.txt',
                          source_sha256=hashlib.sha256(b'seed').hexdigest())
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertIn('INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED', self.codes(result))
        self.assertIn('REVIEW_SOURCE_NOT_IN_CHANGED_FILES',
                      self.provenance(result)[0]['reason'])

    def test_multiple_changed_files_cannot_hide_unreviewed_original_source(self):
        t, r = self.full()
        t['change_scope']['allowed'].append('seed.txt')
        r['changed_files'].append('seed.txt')
        # A validly MAC-signed PASS for x.py alone is not a complete review
        # when another original file changed in the exact same revision.
        self.write_review()
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(result['pass'])
        self.assertIn('INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED', self.codes(result))
        self.assertIn('REVIEW_SOURCE_COVERAGE_INCOMPLETE',
                      self.provenance(result)[0]['reason'])

    def test_multiple_changed_sources_pass_provenance_only_with_full_signed_manifest(self):
        t, r = self.full()
        t['change_scope']['allowed'].append('seed.txt')
        r['changed_files'].append('seed.txt')
        self.write_review(reviewed_sources=[
            {'path': 'x.py', 'sha256': hashlib.sha256(b'original source').hexdigest()},
            {'path': 'seed.txt', 'sha256': hashlib.sha256(b'seed').hexdigest()},
        ])
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(self.provenance(result))
        self.assertIs(result['independent_pass_verified'], _safe_open_supported())

    def test_signed_full_manifest_secondary_source_tamper_is_rework(self):
        t, r = self.full()
        t['change_scope']['allowed'].append('seed.txt')
        r['changed_files'].append('seed.txt')
        self.write_review(reviewed_sources=[
            {'path': 'x.py', 'sha256': hashlib.sha256(b'original source').hexdigest()},
            {'path': 'seed.txt', 'sha256': hashlib.sha256(b'fake seed').hexdigest()},
        ])
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertIn('REVIEW_SOURCE_HASH_NOT_BOUND_TO_COMMIT',
                      self.provenance(result)[0]['reason'])

    def test_signed_manifest_duplicate_or_traversal_source_is_rejected(self):
        t, r = self.full()
        t['change_scope']['allowed'].append('seed.txt')
        r['changed_files'].append('seed.txt')
        cases = [
            [{'path': 'x.py', 'sha256': hashlib.sha256(b'original source').hexdigest()}] * 2,
            [{'path': 'x.py', 'sha256': hashlib.sha256(b'original source').hexdigest()},
             {'path': '../seed.txt', 'sha256': hashlib.sha256(b'seed').hexdigest()}],
        ]
        for manifest in cases:
            with self.subTest(manifest=manifest):
                self.write_review(reviewed_sources=manifest)
                r['gongbang_evidence'] = self.evidence()
                result = review(t, r, self.root)
                self.assertIn('INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED', self.codes(result))

    def test_signed_review_missing_original_source_path_fails_closed(self):
        t, r = self.full()
        doc = self.review_doc()
        doc.pop('source_path')
        doc['provider_receipt'] = sign_review_receipt(doc, 'taky-verifier', KEY)
        (self.root / 'review.json').write_bytes(json.dumps(doc).encode())
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertIn('REVIEW_SOURCE_PATH_MISSING_OR_INVALID',
                      self.provenance(result)[0]['reason'])

    def test_original_revision_not_uncommitted_worktree_is_source_authority(self):
        t, r = self.full()
        (self.root / 'x.py').write_bytes(b'unsaved local changes')
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertFalse(self.provenance(result),
                         'review is pinned to committed source, not moving worktree')

    def test_receipt_requires_source_hash(self):
        doc = self.review_doc(source_sha256='not-a-hash')
        doc['provider_receipt'] = sign_review_receipt(doc, 'taky-verifier', KEY)
        self.assertEqual(verify_review_receipt(doc, 'T', self.sha, 'claude-executor', KEY),
                         ['RECEIPT_SOURCE_HASH_MISSING'])

    def test_receipt_cannot_launder_a_defective_review(self):
        t, r = self.base()
        self.write_review(reviewer_id='Claude-Executor')  # validly signed, but reviewer is the executor
        r['gongbang_evidence'] = self.evidence()
        result = review(t, r, self.root)
        self.assertEqual(result['review_decision'], 'REWORK')
        self.assertIn('REVIEWER_IS_EXECUTOR', self.provenance(result)[0]['reason'])

    def test_verified_receipt_review_passes_and_marks_identity_verified(self):
        t, r = self.full()
        result = review(t, r, self.root)
        if _safe_open_supported():
            self.assertTrue(result['pass'], result['defects'])
            self.assertEqual(result['review_decision'], 'HUMAN_APPROVAL')
            self.assertIs(result['independent_pass_verified'], True)
            self.assertIn({'kind': 'independent_review', 'identity': 'PROVIDER_RECEIPT_VERIFIED'},
                          result['evidence'])
        else:
            self.assertFalse(result['pass'])
            self.assertIs(result['independent_pass_verified'], False)

    def test_optional_no_false_block(self):
        t, r = self.base()
        t['material_taky_turn'] = False
        self.assertTrue(review(t, r, self.root)['pass'])


if __name__ == '__main__':
    unittest.main()
