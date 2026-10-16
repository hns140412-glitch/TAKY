import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from gongbang_scope_gate_candidate import REQUIRED, _read_windows_handle, _safe_open_supported, evaluate

TASK = 'TASK-1'
REV = 'abc1234'
SAFE = _safe_open_supported()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def doc(task=TASK, rev=REV, **extra):
    return json.dumps({'task_id': task, 'revision': rev, **extra}).encode()


class TestGongbang(unittest.TestCase):
    def test_empty_is_hold(self):
        self.assertEqual(evaluate({})['status'], 'HOLD')
        self.assertEqual(len(evaluate({})['missing']), len(REQUIRED))

    def test_partial_is_hold(self):
        self.assertEqual(evaluate({'intent': {'status': 'PASS', 'evidence_ref': 'x'}})['status'], 'HOLD')

    def test_unproven_is_hold(self):
        self.assertEqual(evaluate({k: {'status': 'PASS', 'evidence_ref': 'x'} for k in REQUIRED[:-1]})['status'], 'HOLD')

    def test_shape_only_without_root_is_hold(self):
        result = evaluate({k: {'status': 'PASS', 'evidence_ref': 'x', 'evidence_sha256': 'a' * 64} for k in REQUIRED}, None, TASK, REV)
        self.assertEqual(result['status'], 'HOLD')
        self.assertIn('ROOT_REQUIRED', result['preconditions'])

    def test_non_dict_record_is_hold(self):
        self.assertEqual(evaluate(None, Path('.'), TASK, REV)['status'], 'HOLD')


class TestGongbangFileEvidence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / 'repo'
        (self.root / 'C2S').mkdir(parents=True)
        self.data = doc(note='real evidence')
        (self.root / 'C2S' / 'ev.txt').write_bytes(self.data)

    def record(self, **over):
        entry = {'status': 'PASS', 'evidence_ref': 'C2S/ev.txt', 'evidence_sha256': sha(self.data)}
        rec = {k: dict(entry) for k in REQUIRED}
        rec.update(over)
        return rec

    def ev(self, rec, **kw):
        return evaluate(rec, kw.get('root', self.root), kw.get('task', TASK), kw.get('rev', REV))

    def test_positive_issuer_still_unverified(self):
        result = self.ev(self.record())
        self.assertEqual(result['issuer'], 'UNVERIFIED')
        if SAFE:
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(result['unverified'], {})
            self.assertEqual(result['integrity'], 'FD_RELATIVE_NOFOLLOW')
        else:
            # Swap-safety cannot be proven here: valid evidence must still HOLD, never PASS.
            self.assertEqual(result['status'], 'HOLD')
            self.assertEqual(set(result['unverified'].values()), {'RACE_SAFETY_UNVERIFIED'})
            self.assertEqual(result['integrity'], 'UNVERIFIED')

    def test_unsupported_platform_never_passes(self):
        with mock.patch('gongbang_scope_gate_candidate._safe_open_supported', return_value=False):
            result = self.ev(self.record())
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(set(result['unverified'].values()), {'RACE_SAFETY_UNVERIFIED'})
        self.assertEqual(result['integrity'], 'UNVERIFIED')

    def _bound(self, payload, task=TASK, rev=REV):
        (self.root / 'C2S' / 'b.json').write_bytes(payload)
        rec = self.record(intent={'status': 'PASS', 'evidence_ref': 'C2S/b.json', 'evidence_sha256': sha(payload)})
        return self.ev(rec, task=task, rev=rev)['unverified'].get('intent')

    def test_prefix_collision_task_rejected(self):
        self.assertEqual(self._bound(doc(task='TASK-10')), 'BINDING_MISSING')
        self.assertEqual(self._bound(doc(task='TASK-1'), task='TASK-10'), 'BINDING_MISSING')

    def test_prefix_collision_revision_rejected(self):
        self.assertEqual(self._bound(doc(rev='abc12345')), 'BINDING_MISSING')
        self.assertEqual(self._bound(doc(rev='abc1234'), rev='abc12345'), 'BINDING_MISSING')

    def test_substring_in_other_fields_not_accepted(self):
        payload = json.dumps({'task_id': 'X', 'revision': 'Y', 'note': f'{TASK} {REV}'}).encode()
        self.assertEqual(self._bound(payload), 'BINDING_MISSING')

    def test_non_string_fields_rejected(self):
        self.assertEqual(self._bound(json.dumps({'task_id': [TASK], 'revision': REV}).encode()), 'BINDING_MISSING')
        self.assertEqual(self._bound(json.dumps({'task_id': TASK}).encode()), 'BINDING_MISSING')

    def test_unparseable_evidence_fails_closed(self):
        for payload in (f'plain text {TASK} {REV}'.encode(), b'\xff\xfe{}', b'[1, 2]', b'"str"',
                        f'{{"task_id": "{TASK}", "revision": "{REV}", "revision": "{REV}"}}'.encode(),
                        f'{{"task_id": "{TASK}", "revision": "{REV}", "n": NaN}}'.encode()):
            self.assertEqual(self._bound(payload), 'BINDING_UNPARSEABLE', payload)

    @unittest.skipUnless(SAFE and hasattr(os, 'mkfifo'), 'POSIX FIFO required')
    def test_fifo_does_not_block(self):
        os.mkfifo(self.root / 'C2S' / 'pipe')
        rec = self.record(intent={'status': 'PASS', 'evidence_ref': 'C2S/pipe', 'evidence_sha256': sha(self.data)})
        self.assertEqual(self.ev(rec)['unverified']['intent'], 'REF_FILE_MISSING')

    @unittest.skipUnless(SAFE, 'fd-relative open required')
    def test_intermediate_symlink_component_rejected(self):
        (self.root / 'real').mkdir()
        (self.root / 'real' / 'ev.txt').write_bytes(self.data)
        try:
            (self.root / 'swapped').symlink_to(self.root / 'real', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlink creation not permitted')
        rec = self.record(intent={'status': 'PASS', 'evidence_ref': 'swapped/ev.txt', 'evidence_sha256': sha(self.data)})
        self.assertEqual(self.ev(rec)['unverified']['intent'], 'REF_SYMLINK')

    def test_missing_task_or_revision_is_hold(self):
        for task, rev in ((None, REV), (TASK, None), ('', REV), (TASK, ' ')):
            result = self.ev(self.record(), task=task, rev=rev)
            self.assertEqual(result['status'], 'HOLD')
            self.assertTrue(result['preconditions'])

    def test_binding_other_task_or_revision(self):
        self.assertEqual(set(self.ev(self.record(), task='OTHER-9')['unverified'].values()), {'BINDING_MISSING'})
        self.assertEqual(self.ev(self.record(), rev='ffffff0')['status'], 'HOLD')

    def test_self_hash_without_binding_is_hold(self):
        # A file whose hash matches but was not written for this task/revision.
        (self.root / 'C2S' / 'generic.txt').write_bytes(b'generic')
        rec = self.record(intent={'status': 'PASS', 'evidence_ref': 'C2S/generic.txt', 'evidence_sha256': sha(b'generic')})
        self.assertEqual(self.ev(rec)['unverified']['intent'], 'BINDING_UNPARSEABLE')

    def test_missing_file(self):
        rec = self.record(intent={'status': 'PASS', 'evidence_ref': 'C2S/none.txt', 'evidence_sha256': sha(self.data)})
        result = self.ev(rec)
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(result['unverified']['intent'], 'REF_FILE_MISSING')

    def test_tamper(self):
        (self.root / 'C2S' / 'ev.txt').write_bytes(b'changed after review')
        result = self.ev(self.record())
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(set(result['unverified'].values()), {'SHA256_MISMATCH'})

    def test_missing_sha(self):
        rec = self.record(reuse={'status': 'PASS', 'evidence_ref': 'C2S/ev.txt'})
        self.assertEqual(self.ev(rec)['unverified']['reuse'], 'SHA256_MISSING')

    def test_path_traversal_and_absolute(self):
        outside = self.root.parent / 'outside.txt'
        outside.write_bytes(self.data)
        for ref in ('../outside.txt', 'C2S/../../outside.txt', str(outside), '/etc/passwd', 'C:/Windows/win.ini'):
            rec = self.record(authority={'status': 'PASS', 'evidence_ref': ref, 'evidence_sha256': sha(self.data)})
            result = self.ev(rec)
            self.assertEqual(result['status'], 'HOLD', ref)
            self.assertEqual(result['unverified']['authority'], 'REF_NOT_REPO_RELATIVE', ref)

    def test_directory_and_empty_file_rejected(self):
        (self.root / 'C2S' / 'empty.txt').write_bytes(b'  \n')
        for ref, code in (('C2S', 'REF_FILE_MISSING'), ('C2S/empty.txt', 'REF_FILE_EMPTY')):
            rec = self.record(regression={'status': 'PASS', 'evidence_ref': ref, 'evidence_sha256': sha(b'  \n')})
            self.assertEqual(self.ev(rec)['unverified']['regression'], code)

    def test_false_pass_fictitious_ref(self):
        rec = {k: {'status': 'PASS', 'evidence_ref': 'x', 'evidence_sha256': 'a' * 64} for k in REQUIRED}
        result = self.ev(rec)
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(len(result['unverified']), len(REQUIRED))

    def test_read_error_is_hold_not_exception(self):
        with mock.patch('gongbang_scope_gate_candidate.os.open', side_effect=PermissionError('denied')):
            result = self.ev(self.record())
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(set(result['unverified'].values()), {'REF_UNREADABLE'})

    def test_resolve_error_is_hold_not_exception(self):
        with mock.patch('gongbang_scope_gate_candidate.Path.resolve', side_effect=OSError('bad')):
            result = self.ev(self.record())
        self.assertEqual(result['status'], 'HOLD')

    def test_symlink_rejected(self):
        link = self.root / 'C2S' / 'link.txt'
        try:
            link.symlink_to(self.root / 'C2S' / 'ev.txt')
        except (OSError, NotImplementedError):
            self.skipTest('symlink creation not permitted')
        rec = self.record(intent={'status': 'PASS', 'evidence_ref': 'C2S/link.txt', 'evidence_sha256': sha(self.data)})
        self.assertEqual(self.ev(rec)['unverified']['intent'], 'REF_SYMLINK')

    def test_swap_during_read_is_hold(self):
        # Simulated: the path no longer refers to the file that was opened and read.
        # Exercises the path-based fallback's re-check (the fd-relative route has no resolve/reopen gap).
        with mock.patch('gongbang_scope_gate_candidate._safe_open_supported', return_value=False), \
                mock.patch('gongbang_scope_gate_candidate.os.path.samestat', return_value=False):
            result = self.ev(self.record())
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(set(result['unverified'].values()), {'REF_CHANGED_DURING_READ'})


class TestWindowsHandleEvidence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve() / 'repo'
        (self.root / 'C2S').mkdir(parents=True)
        self.data = doc(note='real evidence')
        (self.root / 'C2S' / 'ev.txt').write_bytes(self.data)

    def read(self, *parts):
        return _read_windows_handle(self.root, list(parts))

    @unittest.skipIf(os.name == 'nt', 'non-Windows only')
    def test_unsupported_off_windows(self):
        self.assertEqual(self.read('C2S', 'ev.txt'), (None, 'WINDOWS_HANDLE_UNSUPPORTED', None))

    @unittest.skipUnless(os.name == 'nt', 'native Windows required')
    def test_handle_evidence_collected_but_race_safety_unverified(self):
        data, reason, evidence = self.read('C2S', 'ev.txt')
        self.assertIsNone(reason)
        self.assertEqual(data, self.data)
        self.assertEqual(evidence['race_safety'], 'UNVERIFIED')
        self.assertEqual(evidence['size'], len(self.data))
        self.assertEqual(evidence['final_path'], os.path.normcase(str(self.root / 'C2S' / 'ev.txt')))

    @unittest.skipUnless(os.name == 'nt', 'native Windows required')
    def test_handle_evidence_never_passes_evaluate(self):
        rec = {k: {'status': 'PASS', 'evidence_ref': 'C2S/ev.txt', 'evidence_sha256': sha(self.data)} for k in REQUIRED}
        self.assertIsNone(self.read('C2S', 'ev.txt')[1])
        result = evaluate(rec, self.root, TASK, REV)
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(set(result['unverified'].values()), {'RACE_SAFETY_UNVERIFIED'})
        self.assertEqual(result['issuer'], 'UNVERIFIED')
        self.assertEqual(result['integrity'], 'UNVERIFIED')

    @unittest.skipUnless(os.name == 'nt', 'native Windows required')
    def test_missing_directory_and_device_name_rejected(self):
        for parts, code in ((('C2S', 'none.txt'), 'REF_FILE_MISSING'), (('C2S',), None),
                            (('C2S', 'CON'), None), (('C2S', 'ev.txt:stream'), None)):
            data, reason, evidence = self.read(*parts)
            self.assertIsNone(data, parts)
            self.assertIsNone(evidence, parts)
            self.assertTrue(reason, parts)
            if code:
                self.assertEqual(reason, code, parts)

    @unittest.skipUnless(os.name == 'nt', 'native Windows required')
    def test_symlink_and_junction_chain_rejected(self):
        try:
            (self.root / 'link.txt').symlink_to(self.root / 'C2S' / 'ev.txt')
            (self.root / 'swapped').symlink_to(self.root / 'C2S', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlink creation not permitted')
        self.assertEqual(self.read('link.txt')[1], 'REF_SYMLINK')
        data, reason, _ = self.read('swapped', 'ev.txt')
        self.assertIsNone(data)
        self.assertEqual(reason, 'REF_ESCAPES_ROOT')


if __name__ == '__main__':
    unittest.main()
