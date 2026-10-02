"""Focused authority routing regression tests; no network or runtime promotion."""
import copy
from pathlib import Path
from uuid import uuid4
import unittest

import semantic_current_resolver as resolver


class SemanticCurrentTests(unittest.TestCase):
    def setUp(self):
        self.registry = resolver.load_json(resolver.ROOT / resolver.REGISTRY)

    def test_exact_semantic_owners_and_learning_roles(self):
        expected = {
            'system': 'MASTER/MASTER_LOGIC.md',
            'learning_engine': 'OS/LEARNING_ENGINE_CORE.md',
            'explorer_crew': 'OS/EXPLORATION_CREW_CANONICAL.md',
            'ready_set': 'PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md',
            'design_ui_assets': 'MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md',
            'learning_data': 'OS/LEARNING_ENGINE_CORE.md',
        }
        for namespace, path in expected.items():
            self.assertEqual(resolver.resolve(namespace)['path'], path)
        self.assertEqual(resolver.resolve('learning_engine', role='current')['path'],
                         'CURRENT/LEARNING_ENGINE_DATA_READINESS_CURRENT.json')
        for role, path in (
            ('change_ledger', 'CURRENT/LEARNING_ENGINE_CHANGE_LEDGER_CURRENT.json'),
            ('verification_checkpoint', 'CURRENT/LEARNING_ENGINE_VERIFICATION_CURRENT_2026-09-25.md'),
        ):
            self.assertEqual(resolver.resolve('learning_engine', role=role)['path'], path)
            self.assertFalse(resolver.resolve('learning_engine', role=role)['resume_pointer'])
            with self.assertRaises(resolver.ResolutionError):
                resolver.resolve('learning_engine', role='current', expected_path=path)
        self.assertEqual(resolver.resolve('learning_data', role='current')['path'],
                         'CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json')
        for role in ('change_ledger', 'verification_checkpoint'):
            with self.assertRaises(resolver.ResolutionError):
                resolver.resolve('learning_data', role=role)

    def test_unknown_duplicate_missing_and_noncanonical_fail_closed(self):
        with self.assertRaises(resolver.ResolutionError):
            resolver.resolve('unknown')
        for mutation in ('duplicate', 'missing', 'noncanonical', 'ambiguous'):
            registry = copy.deepcopy(self.registry)
            row = registry['semantic_owners'][0]
            if mutation == 'duplicate':
                registry['semantic_owners'].append(copy.deepcopy(row))
            elif mutation == 'missing':
                row['paths']['owner'] = 'MASTER/MISSING_REV_999.md'
            elif mutation == 'noncanonical':
                row['paths']['owner'] = 'MASTER/REMASTER_REV00_DRAFT.md'
            else:
                row['paths']['current'] = row['paths']['owner']
            with self.subTest(mutation=mutation), self.assertRaises(resolver.ResolutionError):
                resolver.bindings(resolver.ROOT, registry)

    def test_no_revision_ranking_or_path_fallback(self):
        root = resolver.ROOT / ('.semantic-test-' + uuid4().hex)
        root.mkdir(mode=0o755)
        try:
            (root / 'OWNER_REV_01.md').write_text('owner', encoding='utf-8')
            (root / 'OWNER_REV_999.md').write_text('candidate', encoding='utf-8')
            registry = {'semantic_owners': [{'namespace': 'sample', 'state': 'ACTIVE_OWNER',
                        'paths': {'owner': 'OWNER_REV_01.md'}}]}
            self.assertEqual(resolver.resolve('sample', root=root, registry=registry)['path'],
                             'OWNER_REV_01.md')
            for path in ('OWNER_REV_999.md', '../OWNER_REV_01.md', 'owner_rev_01.md'):
                with self.assertRaises(resolver.ResolutionError):
                    resolver.resolve('sample', expected_path=path, root=root, registry=registry)
            (root / 'OWNER_REV_01.md').unlink()
            with self.assertRaises(resolver.ResolutionError):
                resolver.resolve('sample', root=root, registry=registry)
            (root / 'duplicate.json').write_text('{"owner":1,"owner":2}', encoding='utf-8')
            with self.assertRaises(resolver.ResolutionError):
                resolver.load_json(root / 'duplicate.json')
        finally:
            for child in root.iterdir():
                child.unlink()
            root.rmdir()

    def test_audited_scope_boundaries(self):
        self.assertTrue(resolver.validate_system_current()['pass'])
        current = resolver.load_json(resolver.ROOT / resolver.CURRENT)
        self.assertEqual(current['audit_date'], '2026-10-02')
        self.assertEqual(current['resume']['learning_role'], 'OPERATIONAL_CURRENT')
        scopes = {row['id']: row for row in current['scopes']}
        for scope in ('tatoeba_language_usage_example_sentence', 'mining_index_learning_core_loop',
                      'learning_planner_ready_path', 'exploration_crew_canonical_v2'):
            self.assertEqual(scopes[scope]['state'], 'MAIN/CLOSED')
        for scope, pr in (('exploration_crew_central_runtime', 191), ('badge_central', 196),
                          ('design_to_ui', 194), ('assets_approved_results_pointer_contract', 4)):
            self.assertEqual(scopes[scope]['state'], 'DRAFT_CANDIDATE')
            self.assertEqual(scopes[scope]['pr'], pr)
            self.assertIs(scopes[scope]['main_authority'], False)
        for scope in ('exploration_crew_hide_consumer_v2', 'exploration_crew_snap_consumer_v2'):
            self.assertEqual(scopes[scope]['state'], 'OPEN')
        self.assertEqual(scopes['snap_legacy_browser_closure']['state'], 'UNVERIFIED')
        self.assertEqual(scopes['deployment_netlify']['state'], 'HOLD')
        self.assertEqual(scopes['recent_family_profile_radio_ux']['state'], 'OPEN')
        self.assertEqual(scopes['recent_family_profile_radio_ux']['exact_radio_gesture'],
                         'OPEN__TAP_VS_HOLD_TO_TALK_UNRESOLVED')
        self.assertEqual(scopes['exploration_crew_canonical_v2']['pr'], 193)
        self.assertEqual(scopes['learning_planner_ready_path']['schedule_owner'], 'PLANNER')
        self.assertIs(scopes['learning_planner_ready_path']['learning_schedule_authority'], False)

    def test_exact_audited_heads_and_preserved_boundaries(self):
        current = resolver.load_json(resolver.ROOT / resolver.CURRENT)
        self.assertEqual(current['source_heads'], {
            'TAKY': 'ccfb372ed10110121cec5be615c3e3e0c59f3601',
            'Ready-Set': 'daed2ebd072061b870bfd0d2f2472dd344661bad',
            'Hide-Seek': 'f1c4bd7a61edcfab3c9bb0836db162e38ca2311f',
            'Snap-Pop': '2b9c6941792269244f847b1b978125996a49b5f8',
            'TAKY-MOBILE': '9bcb7d9660834818457704db2c0a5b16c9964c95',
            'TAKY-ASSETS': '8d902a93dbb7cde3f38580c4f4d0653a4f1314aa',
        })
        scopes = {row['id']: row for row in current['scopes']}
        self.assertEqual(scopes['badge_central']['producer_snapshot'],
                         {'source_producers': 15, 'active_producers': 0, 'total': 60})
        self.assertEqual(scopes['badge_central']['live_hosted_e2e'], 'OPEN')
        self.assertEqual(scopes['badge_central']['head_ref'],
                         'de9ca733168bdace6b114b147ffc95ec7c09f064')
        self.assertEqual(scopes['badge_central']['candidate_refs']['TAKY-MOBILE']['head'],
                         'b42f7e2d0fdf220e552817c41629c5384034888b')
        self.assertEqual(scopes['exploration_crew_ready_consumer_v2']['state'], 'MAIN/CLOSED')
        state = (resolver.ROOT / 'STATE.md').read_text(encoding='utf-8')
        active_state = state.split('Historical quotation of the superseded Ready state')[0]
        self.assertIn('RESOLVE system:current', active_state)
        self.assertIn(resolver.CURRENT, active_state)
        self.assertNotIn('Ready main remains `6142', active_state)
        readiness = resolver.load_json(resolver.ROOT / resolver.resolve('learning_engine', role='current')['path'])
        tatoeba = next(x for x in readiness['scopes'] if x['source_id'] == 'LANGUAGE_TATOEBA_TEXT_2026')
        self.assertEqual(tatoeba['state'], 'CLOSED')
        self.assertFalse(tatoeba['schedule_authority'])
        data_current = resolver.load_json(resolver.ROOT / resolver.resolve('learning_data', role='current')['path'])
        self.assertEqual(data_current['namespace'], 'DATA')
        self.assertEqual(data_current['external_index_evidence']['tatoeba']['state'], 'CLOSED')
        self.assertEqual(data_current['external_index_evidence']['tatoeba']['authority'], 'EXTERNAL_INDEX_EVIDENCE_ONLY')


if __name__ == '__main__':
    unittest.main(verbosity=2)
