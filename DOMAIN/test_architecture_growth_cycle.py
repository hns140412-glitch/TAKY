#!/usr/bin/env python3
"""Regression and negative tests for the ARCHI GROW adapter."""
import copy
import json
import unittest
from pathlib import Path
from architecture_growth_cycle import VERSION, assess, make_board

BASE = json.loads((Path(__file__).parent / 'architecture_growth_backlog.json').read_text(encoding='utf-8'))


def base_item():
    return copy.deepcopy(BASE['gaps'][0])


def indexed_item():
    i = base_item()
    i['source_refs'].append({'id':'fixture-usable', 'location':'fixture://source', 'revision':'fixture-v1', 'role':'SOURCE_EVIDENCE'})
    i['index_receipt'] = {'checked': True, 'receipt_id': 'idx-001', 'sufficient': True,
                          'eligible_source_ids': ['fixture-usable'], 'sufficiency_evidence':'fixture-reviewed', 'index_payload_sha256':'fixture-index-hash'}
    return i


def method_item():
    i = indexed_item()
    i['method_candidate'] = {'id': 'method-001', 'rationale': 'Documented evidence gap',
        'tradeoff': 'Additional source cost', 'falsification': 'Could not reproduce',
        'source_ids': ['fixture-usable']}
    return i


class CycleTest(unittest.TestCase):
    def test_backlog_routes_open_and_frozen(self):
        board = make_board(BASE)
        self.assertEqual(len(board['items']), 6)
        self.assertEqual(board['next_action']['gap_id'], 'AG-GAP-001')
        self.assertEqual(sum(x['route'] == 'HOLD_PRESERVED' for x in board['items']), 3)
        self.assertFalse(board['no_external_actions_executed'] is False)

    def test_no_mining_without_index(self):
        self.assertEqual(assess(base_item())['result']['route'], 'INDEX_QUERY_REQUEST')

    def test_insufficient_index_routes_mining(self):
        i = base_item()
        i['index_receipt'] = {'checked': True, 'receipt_id': 'idx-002', 'sufficient': False, 'index_payload_sha256': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'insufficiency_evidence': 'Fixture source applicability review found missing original content.'}
        self.assertEqual(assess(i)['result']['route'], 'MINING_GAP_REQUEST')

    def test_unproved_insufficiency_cannot_request_mining(self):
        i = base_item()
        i['index_receipt'] = {'checked': True, 'receipt_id': 'self-asserted', 'sufficient': False}
        self.assertEqual(assess(i)['detected'], ['INDEX_INSUFFICIENCY_PROOF_REQUIRED'])

    def test_sufficient_index_routes_domain_method(self):
        self.assertEqual(assess(indexed_item())['result']['route'], 'DOMAIN_METHOD_SYNTHESIS')

    def test_proven_method_routes_work_os_and_not_self_execute(self):
        route = assess(method_item())['result']
        self.assertEqual((route['route'], route['next_owner']), ('WORK_OS_TRIAL_HANDOFF', 'WORK_OS'))
        self.assertFalse(route['automatic_canonical_promotion'])

    def test_trial_without_outcome_receipt(self):
        i = method_item()
        i['work_os_trial'] = {'receipt_id': 'work-001'}
        self.assertEqual(assess(i)['result']['route'], 'OUTCOME_RECEIPT_REQUEST')

    def test_failed_experiment_retains_failure(self):
        i = method_item()
        i['work_os_trial'] = {'receipt_id': 'work-001', 'outcome': {
            'receipt_id': 'failure-001', 'state': 'FAIL', 'failure_class': 'DRAWING_MISMATCH'}}
        self.assertEqual(assess(i)['result']['route'], 'REVISE_METHOD')

    def test_fake_pass_does_not_promote(self):
        i = method_item()
        i['work_os_trial'] = {'receipt_id': 'work-001', 'outcome': {'receipt_id': 'out-001', 'state': 'PASS'}}
        self.assertEqual(assess(i)['result']['route'], 'REAL_PROOF_GAP')

    def test_real_outcome_still_requires_human_review(self):
        i = method_item()
        i['work_os_trial'] = {'receipt_id': 'work-001', 'outcome': {'receipt_id': 'out-001',
            'state': 'PASS', 'real_project_ref': 'proj-001', 'project_revision': 'rev-001',
            'independent_verification_receipt': 'qa-001', 'regression_receipt': 'reg-001',
            'proof_preflight': 'FILE_HASH_PASS__DOMAIN_REVIEW_PENDING'}}
        r = assess(i)['result']
        self.assertEqual(r['route'], 'HUMAN_ADOPTION_REVIEW')
        self.assertFalse(r['automatic_canonical_promotion'])

    def test_frozen_tags_override_nominal_open_status(self):
        i = method_item()
        i['tags'] = ['CTB']
        self.assertEqual(assess(i)['result']['route'], 'HOLD_PRESERVED')

    def test_unapproved_current_best_rejected(self):
        i = base_item()
        i['status'] = 'CURRENT_BEST'
        self.assertEqual(assess(i)['detected'], ['UNAPPROVED_CURRENT_BEST'])

    def test_index_source_mismatch_rejected(self):
        i = indexed_item()
        i['index_receipt']['eligible_source_ids'] = ['invented-source']
        self.assertEqual(assess(i)['detected'], ['INDEX_SOURCE_TRACE_MISMATCH'])

    def test_duplicate_gap_rejected(self):
        i = base_item()
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_GAP_ID'):
            make_board({'schema': VERSION, 'gaps': [i, i]})

    def test_incomplete_source_provenance_rejected(self):
        i = base_item()
        i['source_refs'] = [{'id': 'no-provenance'}]
        self.assertEqual(assess(i)['detected'], ['SOURCE_PROVENANCE_INCOMPLETE'])


if __name__ == '__main__':
    unittest.main()
