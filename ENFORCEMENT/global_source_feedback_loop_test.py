"""Real-source local readback plus explicitly synthetic authority/correction tests.

Only a disposable Central SQLite is mutated. Operational Central is opened ro.
"""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

import taky_central_source_factory as factory
import global_source_learning_feedback as flow


class GlobalFeedbackLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'central.sqlite3'
        self.c = factory.connect(self.db)
        self.addCleanup(self.c.close)
        sid = 'raw:b33aa71a13d655e96e6b736d0c9de1e5ddea52f205916ca20b876387ff830e87'
        with closing(sqlite3.connect(factory.DB.as_uri()+'?mode=ro', uri=True)) as src:
            for table, key in [('source','id'),('location','source_id'),('stage','source_id'),
                               ('evidence','source_id'),('evidence_unit','source_id'),('event','source_id')]:
                rows = src.execute(f'SELECT * FROM {table} WHERE {key}=?', (sid,)).fetchall()
                for row in rows:
                    self.c.execute(f'INSERT INTO {table} VALUES ({",".join("?" for _ in row)})', row)
        self.c.commit()

    def test_real_source_consumer_durable_feedback_and_requery(self):
        protected = list(self.c.execute('SELECT * FROM stage'))
        first = flow.record_technical_method_decision(self.c, 'real-playwright-local-readback')
        self.assertEqual(first['decision'], 'LOCAL_EVALUATION_REQUIRED')
        self.assertFalse(first['approved_local_consumption'])
        self.assertEqual(first['knowledge_projection']['owner'], 'SYSTEM_GROW')
        self.assertFalse(first['knowledge_projection']['authoritative'])
        observed = flow.load_json(flow.EVIDENCE / 'TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json')['selected_adoption']['local_consumer_observations'][0]
        receipt = {'run_id':observed['run_id'], 'outcome':'SUCCESS',
                   'evidence_sha256':observed['runtime_receipt_sha256']}
        event_id = flow.record_technical_feedback(self.c, first['decision_event_id'], receipt)
        self.assertEqual(event_id, flow.record_technical_feedback(self.c, first['decision_event_id'], receipt))
        self.c.commit()
        with closing(sqlite3.connect(self.db)) as reopened:
            reopened.row_factory = sqlite3.Row
            second = flow.technical_method_decision(reopened)
        self.assertEqual(second['decision'], 'REUSE_CANDIDATE')
        self.assertEqual(second['feedback'], [{'event_id':event_id,'outcome':'SUCCESS'}])
        self.assertFalse(second['approved_local_consumption'])
        self.assertFalse(second['knowledge_projection']['authoritative'])
        self.assertEqual([tuple(r) for r in protected], [tuple(r) for r in self.c.execute('SELECT * FROM stage')])
        # A receipt hash is verified again after durable reopen, not just on append.
        forged = dict(receipt, evidence_sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'OBSERVATION_OUTCOME_MISMATCH'):
            flow.record_technical_feedback(self.c, first['decision_event_id'], forged)
        type(self).real_receipt = {'run_id':'TAKY-GLOBAL-FEEDBACK-LOOP-20261014',
            'scope':'REAL_SOURCE_AND_PRIOR_LOCAL_RUN_REPLAY_DISPOSABLE_SQLITE',
            'before':first['decision'], 'after':second['decision'],
            'binding':second['binding'], 'forming_draft':second['prepared'],
            'original_local_run_id':receipt['run_id'],
            'temporary_decision_event_id':first['decision_event_id'],
            'temporary_feedback_event_id':event_id,
            'operational_db_written':False,'current_written':False,
            'real_approval':False,'new_browser_execution':False}

    def test_existing_local_run_flows_to_durable_feedback_once(self):
        report = flow.load_json(flow.EVIDENCE /
            'TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json')
        observed_run_id = report['selected_adoption']['local_consumer_observations'][0]['run_id']
        protected = list(self.c.execute('SELECT * FROM stage'))
        source_rows = list(self.c.execute('SELECT * FROM source'))
        original_events = self.c.execute('SELECT COUNT(*) FROM event').fetchone()[0]
        result = flow.consume_verified_local_observation(
            self.c, 'TAKY_LOCAL_CONSUMER_REAL_REPLAY_20261014', observed_run_id)
        self.assertEqual(result['before'], 'LOCAL_EVALUATION_REQUIRED')
        self.assertEqual(result['after'], 'REUSE_CANDIDATE')
        self.assertEqual(result['feedback_count'], 1)
        self.assertFalse(result['semantic_approved'])
        self.assertFalse(result['global_knowledge_approved'])
        self.assertFalse(result['production_consumption_verified'])
        self.assertEqual(list(self.c.execute('SELECT * FROM stage')), protected)
        self.assertEqual(list(self.c.execute('SELECT * FROM source')), source_rows)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM event').fetchone()[0],
                         original_events + 2)
        self.c.commit()
        with closing(sqlite3.connect(self.db)) as persisted:
            persisted.row_factory = sqlite3.Row
            after = flow.technical_method_decision(persisted)
            self.assertEqual(after['decision'], 'REUSE_CANDIDATE')
            repeated = flow.consume_verified_local_observation(
                persisted, 'TAKY_LOCAL_CONSUMER_REAL_REPLAY_20261014', observed_run_id)
            self.assertEqual(repeated['feedback_event_id'], result['feedback_event_id'])
            self.assertEqual(repeated['decision_event_id'], result['decision_event_id'])
            self.assertEqual(persisted.execute('SELECT COUNT(*) FROM event').fetchone()[0],
                             original_events + 2)
            with self.assertRaisesRegex(ValueError, 'OBSERVATION_RUN_UNKNOWN'):
                flow.consume_verified_local_observation(persisted,
                    'TAKY_UNKNOWN_LOCAL_RUN', 'unverified-run-id')
            self.assertEqual(persisted.execute('SELECT COUNT(*) FROM event').fetchone()[0],
                             original_events + 2)
            persisted.execute('SAVEPOINT tamper')
            persisted.execute('UPDATE evidence_unit SET content_sha256=? WHERE source_id=?',
                              ('0'*64, result['source_id']))
            with self.assertRaisesRegex(ValueError, 'UNIT_HASH_MISMATCH'):
                flow.consume_verified_local_observation(
                    persisted, 'TAKY_LOCAL_TAMPER_REPLAY', observed_run_id)
            persisted.execute('ROLLBACK TO tamper')
            persisted.execute('RELEASE tamper')
            self.assertEqual(persisted.execute('SELECT COUNT(*) FROM event').fetchone()[0],
                             original_events + 2)

    def test_raw_anchor_owner_and_event_tamper_block(self):
        from unittest.mock import patch
        with patch('ai_reference_projection.build_learning', return_value={
                'owner':'LEARNING_ENGINE','authoritative':True,'learnings':[]}):
            with self.assertRaisesRegex(ValueError, 'SYSTEM_GROW_CONSUMER_PROJECTION_REJECTED'):
                flow.technical_method_decision(self.c)
        initial = flow.record_technical_method_decision(self.c, 'tamper-test')
        sid = initial['binding']['source_id']
        self.c.execute('SAVEPOINT tamper')
        self.c.execute('UPDATE evidence_unit SET raw_sha256=? WHERE source_id=?', ('0'*64,sid))
        with self.assertRaisesRegex(ValueError, 'RAW_HASH_MISMATCH'):
            flow.technical_method_decision(self.c)
        self.c.execute('ROLLBACK TO tamper')
        self.c.execute('UPDATE evidence_unit SET content_sha256=? WHERE source_id=?', ('0'*64,sid))
        with self.assertRaisesRegex(ValueError, 'UNIT_HASH_MISMATCH'):
            flow.technical_method_decision(self.c)
        self.c.execute('ROLLBACK TO tamper')
        row = self.c.execute("SELECT receipt_json FROM stage WHERE source_id=? AND stage='ANALYZE'",(sid,)).fetchone()
        claim = json.loads(row[0]); claim['suggested_consumer']='LEARNING_ENGINE'
        self.c.execute("UPDATE stage SET receipt_json=? WHERE source_id=? AND stage='ANALYZE'",(json.dumps(claim),sid))
        with self.assertRaisesRegex(ValueError, 'SEMANTIC_BINDING_INVALID'):
            flow.technical_method_decision(self.c)
        self.c.execute('ROLLBACK TO tamper')
        self.c.execute('UPDATE event SET detail_json=? WHERE event_id=?',('{}',initial['decision_event_id']))
        with self.assertRaisesRegex(ValueError, 'EVENT_HASH_CHANGED'):
            flow.record_technical_feedback(self.c,initial['decision_event_id'],{})

    def test_fixture_authority_is_exact_and_does_not_approve_projection(self):
        draft = flow.technical_method_decision(self.c)['prepared']['formed']
        authority=self.root/'authority'; evidence=self.root/'evidence'
        authority.mkdir(); evidence.mkdir()
        (evidence/'fixture.txt').write_text('SYNTHETIC UNIT TEST ONLY',encoding='utf8')
        record={'issuer':'FORMING_APPROVAL_AUTHORITY','decision':'APPROVED',
            'artifact_id':draft['artifact_id'],'artifact_revision':draft['artifact_revision'],
            'owner_namespace':'SYSTEM_GROW','target_consumer':'TAKY_EXECUTION_EVIDENCE',
            'approved_by':'FIXTURE_OWNER','approved_at':'2026-10-14',
            'evidence_ref':'fixture.txt','evidence_sha256':flow.sha((evidence/'fixture.txt').read_bytes())}
        file=authority/'fixture.json'; file.write_text(json.dumps(record),encoding='utf8')
        policy={'recordPath':str(file),'authorityRoot':str(authority),'evidenceRoot':str(evidence),
                'recordSha256':flow.sha(file.read_bytes()),'approvedBy':'FIXTURE_OWNER'}
        valid=flow.technical_method_decision(self.c,trusted_policy=policy)
        self.assertEqual(valid['decision'],'SELECT_APPROVED_LOCAL_METHOD')
        self.assertFalse(valid['knowledge_projection']['authoritative'])
        self.assertFalse(flow.technical_method_decision(self.c)['approved_local_consumption'])
        wrong=copy.deepcopy(policy); wrong['approvedBy']='WRONG_OWNER'
        self.assertFalse(flow.technical_method_decision(self.c,trusted_policy=wrong)['approved_local_consumption'])
        record['target_consumer']='LEARNING_ENGINE'; file.write_text(json.dumps(record),encoding='utf8')
        policy['recordSha256']=flow.sha(file.read_bytes())
        self.assertFalse(flow.technical_method_decision(self.c,trusted_policy=policy)['approved_local_consumption'])

    def test_fixture_failure_requires_correction_not_later_success(self):
        # This trusted verifier models a future runtime integration, NOT real results.
        verify=lambda receipt,binding: receipt.get('fixture') is True
        first=flow.record_technical_method_decision(self.c,'fixture-correction',outcome_verifier=verify)
        for outcome in ['FAILURE','SUCCESS']:
            flow.record_technical_feedback(self.c,first['decision_event_id'],
                {'run_id':'fixture-'+outcome,'outcome':outcome,'fixture':True},outcome_verifier=verify)
        self.c.commit()
        self.assertEqual(flow.technical_method_decision(self.c,outcome_verifier=verify)['decision'],'REVIEW_REQUIRED')
        with self.assertRaisesRegex(ValueError,'OBSERVATION_RUN_UNKNOWN'):
            flow.technical_method_decision(self.c)


if __name__ == '__main__':
    unittest.main()
