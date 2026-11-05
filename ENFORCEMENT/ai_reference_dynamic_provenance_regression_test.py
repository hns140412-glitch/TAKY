"""Regression: authored learning claims cannot jump RAW/INDEX/FORMING by
calling the generic learning projector with index labels and fabricated facts.
A verified Central DETAIL+runtime path retains a narrowly scoped opt-in.
"""
import hashlib
import json
import unittest
from pathlib import Path
from ai_reference_projection import build_learning

class DynamicLearningIntake(unittest.TestCase):
    def setUp(self):
        self.records=[
           {'source_id':'SITE_WATCH:invented-source',
            'learning_eligible':True,'ai_categories':[],
            'learning_candidates':[{
               'learning_id':'AI-LRN-INVENTED-100',
               'insight':'The published article proves 100% external tool success.'
            }]},
           {'source_id':'INDEX:found-phrase',
            'learning_eligible':True,'ai_categories':[],
            'learning_candidates':[{
               'learning_id':'AI-LRN-INVENTED-101',
               'insight':'The site claims this works so adoption must proceed.'
            }]},
        ]
    def test_source_supplied_claims_are_not_learnings_by_default(self):
        output=build_learning(self.records)
        self.assertEqual(output['learning_count'],0)
        self.assertEqual(output['unverified_dynamic_claims_excluded'],2)
        self.assertFalse(output['authoritative'])
        self.assertEqual(len(output['pending_dynamic_learning_review']),2)
        self.assertEqual(output['proposals_accounted_for'],2)
        self.assertEqual({x['learning_id'] for x in output['pending_dynamic_learning_review']},
                         {'AI-LRN-INVENTED-100','AI-LRN-INVENTED-101'})
    def test_unreviewed_site_claim_remains_excluded_under_normal_projection(self):
        proposal=build_learning(self.records[:1])
        self.assertEqual(proposal['learnings'],[])
        self.assertEqual(proposal['unverified_dynamic_claims_excluded'],1)
    def test_explicit_verified_path_is_scoped_and_non_canonical(self):
        source='SITE_WATCH:invented-source'
        out=build_learning(self.records,verified_dynamic_source_ids=frozenset({source}))
        self.assertEqual(out['learning_count'],1)
        self.assertEqual(out['unverified_dynamic_claims_excluded'],1)
        self.assertEqual(out['learnings'][0]['state'],'EVIDENCE_CANDIDATE')
        self.assertFalse(out['learnings'][0]['canonical_promotion'])
        self.assertFalse(out['authoritative'])
        # Scoped admission is not a runtime proof and not a semantic fact.
        self.assertIn('NOT_AUTOMATIC_SEMANTIC_APPROVAL',out['dynamic_evidence_scope'])
    def test_prior_twelve_hypotheses_cannot_become_learning_via_generic_projector(self):
        p=Path(r'D:\Git PWA\TAKY\LEARNING\evidence\EVERY_AI_SOURCE_BOUND_METHOD_LEARNING_CANDIDATES_20261017.json')
        if not p.exists():self.skipTest('prior source corpus not mounted')
        prior=json.loads(p.read_text(encoding='utf-8'))
        records=[{'source_id':i['source_grounding']['source_id'],
          'learning_eligible':True,
          'ai_categories':[],
          'learning_candidates':[{'learning_id':i['learning_id'],'insight':i['learning_hypothesis']}]}
          for i in prior['candidates']]
        out=build_learning(records)
        self.assertEqual(out['learning_count'],0)
        self.assertEqual(out['unverified_dynamic_claims_excluded'],12)
        self.assertEqual(len(out['pending_dynamic_learning_review']),12)
        self.assertEqual(out['proposals_accounted_for'],12)
    def test_not_learning_eligible_is_recorded_as_review_not_lost(self):
        source={'source_id':'RAW-Z','learning_eligible':False,
            'learning_candidates':[{'learning_id':'Z','insight':'valuable original method'}]}
        out=build_learning([source])
        self.assertEqual(out['learning_count'],0)
        self.assertEqual(out['pending_dynamic_learning_review'][0]['reason'],
                         'SOURCE_NOT_LEARNING_ELIGIBLE')
        self.assertEqual(out['pending_dynamic_learning_review'][0]['proposed_insight'],
                         'valuable original method')
        self.assertEqual(out['proposals_accounted_for'],1)
    def test_matched_rule_not_semantic_success(self):
        r={'source_id':'REF-X','title':'AI Korean style QA','ai_categories':['ORCHESTRATION'],
           'learning_eligible':True,'source_family':'TEST',
           'controlled_terms':['NOT_AUTHORSHIP_DETECTOR','KOREAN_WRITING_QA']}
        out=build_learning([r])
        self.assertGreaterEqual(out['learning_count'],1)
        self.assertTrue(all(x['state']=='EVIDENCE_CANDIDATE' and
                        x['canonical_promotion'] is False for x in out['learnings']))
if __name__=='__main__':
    unittest.main()
