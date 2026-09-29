import copy
import json
import unittest
from pathlib import Path
from architecture_growth_event_replay import replay

BASE = json.loads((Path(__file__).parent / 'architecture_growth_backlog.json').read_text(encoding='utf-8'))


def ev(id_, kind, issuer, receipt, payload, gap='AG-GAP-001'):
    return {'event_id': id_, 'gap_id': gap, 'type': kind, 'issuer': issuer,
            'receipt_id': receipt, 'occurred_at': '2026-09-29T10:00:00Z', 'payload': payload}


class ReplayTest(unittest.TestCase):
    def test_progression_index_to_trial_outcome_and_next_action(self):
        events = [
            ev('source1', 'SOURCE_RECEIPT', 'INDEXING', 'src1', {'id':'fixture-usable','location':'fixture://source','revision':'fixture-v1','role':'SOURCE_EVIDENCE'}),
            ev('e1', 'INDEX_RESULT', 'INDEXING', 'idx-1', {'checked': True, 'sufficient': True,
                'receipt_id': 'idx-1', 'eligible_source_ids': ['fixture-usable'], 'sufficiency_evidence':'fixture-review', 'index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}),
            ev('e2', 'METHOD_CANDIDATE', 'ARCHI_GROW', 'method-1', {'id': 'method-1',
                'rationale': 'Compare', 'tradeoff': 'Time', 'falsification': 'Missing applicability',
                'source_ids': ['fixture-usable']}),
            ev('e3', 'WORK_OS_TRIAL', 'WORK_OS', 'trial-1', {'receipt_id': 'trial-1'}),
            ev('e4', 'WORK_OS_OUTCOME', 'WORK_OS', 'result-1', {'receipt_id': 'result-1', 'state': 'FAIL',
                'failure_class': 'NO_NATIVE_DRAWING'})
        ]
        original = copy.deepcopy(BASE)
        result = replay(BASE, events)
        self.assertEqual(result['event_history'][-1]['resulting_route'], 'REVISE_METHOD')
        self.assertEqual(BASE, original)
        self.assertEqual(result['board']['next_action']['gap_id'], 'AG-GAP-001')

    def test_exact_duplicate_event_is_idempotent(self):
        event = ev('e1', 'INDEX_RESULT', 'INDEXING', 'idx-1', {'checked': True,
            'sufficient': False, 'receipt_id': 'idx-1', 'index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'insufficiency_evidence':'fixture reviewed missing source'})
        self.assertEqual(len(replay(BASE, [event, copy.deepcopy(event)])['event_history']), 1)

    def test_id_conflict_rejected(self):
        event = ev('e1', 'INDEX_RESULT', 'INDEXING', 'idx-1', {'checked': True,
            'sufficient': False, 'receipt_id': 'idx-1', 'index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'insufficiency_evidence':'fixture reviewed missing source'})
        conflict = copy.deepcopy(event); conflict['payload']['sufficient'] = True
        with self.assertRaisesRegex(ValueError, 'EVENT_ID_CONTENT_CONFLICT'):
            replay(BASE, [event, conflict])

    def test_hold_cannot_be_bypassed(self):
        event = ev('e5', 'INDEX_RESULT', 'INDEXING', 'idx-5', {'checked': True,
            'sufficient': False, 'receipt_id': 'idx-5', 'index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'insufficiency_evidence':'fixture review'}, 'AG-HOLD-CTB')
        with self.assertRaisesRegex(ValueError, 'HELD_SCOPE_EVENT_REJECTED'):
            replay(BASE, [event])

    def test_unproved_insufficiency_rejected(self):
        event = ev('bad-index', 'INDEX_RESULT', 'INDEXING', 'idx-bad',
            {'checked': True, 'sufficient': False, 'receipt_id': 'idx-bad'})
        with self.assertRaisesRegex(ValueError, 'INDEX_SNAPSHOT_SHA256_REQUIRED'):
            replay(BASE, [event])

    def test_trial_cannot_arrive_before_method(self):
        event = ev('early-trial', 'WORK_OS_TRIAL', 'WORK_OS', 'trial-early', {'receipt_id':'trial-early'})
        with self.assertRaisesRegex(ValueError, 'TRIAL_OUT_OF_ORDER'):
            replay(BASE, [event])

    def test_outcome_without_trial_rejected(self):
        event = ev('e6', 'WORK_OS_OUTCOME', 'WORK_OS', 'out-6', {'receipt_id': 'out-6', 'state': 'PASS'})
        with self.assertRaisesRegex(ValueError, 'OUTCOME_WITHOUT_OPEN_TRIAL'):
            replay(BASE, [event])

    def test_invalid_issuer_rejected(self):
        event = ev('e7', 'INDEX_RESULT', 'ARCHI_GROW', 'idx-7', {'checked': True,
            'sufficient': False, 'receipt_id': 'idx-7', 'index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'insufficiency_evidence':'fixture review'})
        with self.assertRaisesRegex(ValueError, 'EVENT_OWNER_OR_TYPE_INVALID'):
            replay(BASE, [event])


if __name__ == '__main__':
    unittest.main()

class ProofReplayTest(unittest.TestCase):
    def test_synthetic_pass_without_actual_files_fails_closed(self):
        from architecture_growth_event_replay import replay
        prefix = [
            ev('src-p','SOURCE_RECEIPT','INDEXING','src-p', {'id':'fixture-usable','location':'fixture://source','revision':'fixture-v1','role':'SOURCE_EVIDENCE'}),
            ev('p1','INDEX_RESULT','INDEXING','idx-p', {'checked':True,'sufficient':True,'receipt_id':'idx-p','eligible_source_ids':['fixture-usable'], 'sufficiency_evidence':'fixture-review','index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}),
            ev('p2','METHOD_CANDIDATE','ARCHI_GROW','method-p',{'id':'method-p','rationale':'fixture','tradeoff':'fixture','falsification':'fixture','source_ids':['fixture-usable']}),
            ev('p3','WORK_OS_TRIAL','WORK_OS','trial-p',{'receipt_id':'trial-p'}),
        ]
        without_proof=ev('p4','WORK_OS_OUTCOME','WORK_OS','out-p',{'receipt_id':'out-p','state':'PASS',
            'real_project_ref':'fake','project_revision':'fake','independent_verification_receipt':'fake','regression_receipt':'fake'})
        with self.assertRaisesRegex(ValueError,'PASS_PROOF_MANIFEST_REQUIRED'):
            replay(BASE,prefix+[without_proof])

    def test_pass_bound_to_bytes_only_reaches_human_review(self):
        import tempfile, hashlib
        from architecture_growth_event_replay import replay
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);evidence=[]
            for role in ('SOURCE_MANIFEST','WORK_OS_ARTIFACT','INDEPENDENT_QA','REGRESSION'):
                name=role+'.txt';body=('fixture:'+role).encode();(root/name).write_bytes(body)
                evidence.append({'role':role,'relative_path':name,'sha256':hashlib.sha256(body).hexdigest()})
            manifest={'source_owner':'WORK_OS','state':'PASS','project':{
                'project_id':'fixture-project','revision_id':'fixture-rev',
                'trial_receipt_id':'trial-p','outcome_receipt_id':'out-p'},
                'comparison':{'baseline':4,'observed':2,'unit':'fixture-errors'},'evidence':evidence}
            mb=json.dumps(manifest).encode();(root/'manifest.json').write_bytes(mb)
            prefix=[
                ev('src-p','SOURCE_RECEIPT','INDEXING','src-p', {'id':'fixture-usable','location':'fixture://source','revision':'fixture-v1','role':'SOURCE_EVIDENCE'}),
            ev('p1','INDEX_RESULT','INDEXING','idx-p', {'checked':True,'sufficient':True,'receipt_id':'idx-p','eligible_source_ids':['fixture-usable'], 'sufficiency_evidence':'fixture-review','index_payload_sha256':'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}),
                ev('p2','METHOD_CANDIDATE','ARCHI_GROW','method-p',{'id':'method-p','rationale':'fixture','tradeoff':'fixture','falsification':'fixture','source_ids':['fixture-usable']}),
                ev('p3','WORK_OS_TRIAL','WORK_OS','trial-p',{'receipt_id':'trial-p'}),
            ]
            out=ev('p4','WORK_OS_OUTCOME','WORK_OS','out-p',{'receipt_id':'out-p','state':'PASS',
                'real_project_ref':'fixture-project','project_revision':'fixture-rev',
                'independent_verification_receipt':'fixture-qa','regression_receipt':'fixture-regression',
                'evidence_manifest':'manifest.json','evidence_manifest_sha256':hashlib.sha256(mb).hexdigest()})
            result=replay(BASE,prefix+[out],evidence_root=root)
            self.assertEqual(result['event_history'][-1]['resulting_route'],'HUMAN_ADOPTION_REVIEW')
            (root/'REGRESSION.txt').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'PASS_PROOF_PREFLIGHT_FAILED'):
                replay(BASE,prefix+[out],evidence_root=root)
