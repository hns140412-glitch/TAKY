#!/usr/bin/env python3
import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"HANDOFF/CROSS_REPO_AUTHORITY_MATRIX_2026-10-02_V1.json"

class TestCrossRepoAuthorityMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))

    def test_global_promotion_is_hold(self):
        d=self.d
        self.assertEqual(d["status"],"BRANCH_VALIDATED__PROMOTION_HOLD")
        self.assertFalse(d["promotion_authorized"])
        self.assertFalse(d["main_merge_authorized"])
        self.assertFalse(d["deployment_authorized"])

    def test_owner_boundaries(self):
        s=self.d["systems"]
        self.assertIn("learner_state",s["LEARNING_ENGINE"]["owns"])
        self.assertIn("calendar_date",s["LEARNING_ENGINE"]["forbidden"])
        self.assertIn("dates",s["PLANNER"]["owns"])
        self.assertIn("learner_state",s["PLANNER"]["forbidden"])
        self.assertIn("confirmed_assignment_decomposition",s["READY_SET"]["owns"])
        self.assertIn("learner_state",s["READY_SET"]["forbidden"])
        self.assertFalse(s["READY_SET"]["legacy_adaptive_execution_authorized"])
        self.assertIn("external_acquisition",s["MINING_ENGINE"]["owns"])
        self.assertIn("source_authority",s["MINING_ENGINE"]["forbidden"])
        self.assertIn("source_identity",s["MINING_INDEX"]["owns"])
        self.assertIn("pedagogical_decision",s["MINING_INDEX"]["forbidden"])

    def test_learning_index_roles_are_separate(self):
        roles=self.d["systems"]["LEARNING_INDEX"]["evidence_roles"]
        self.assertEqual(set(roles),{
            "CURRICULUM_ALIGNMENT","LEXICAL_SEMANTICS","LANGUAGE_USAGE",
            "PEDAGOGICAL_USAGE","GENERAL_REFERENCE"
        })
        inv=set(self.d["invariants"])
        self.assertIn("CURRICULUM_ALIGNMENT != LEXICAL_SEMANTICS",inv)
        self.assertIn("LEXICAL_SEMANTICS != LANGUAGE_USAGE",inv)

    def test_source_candidates_are_not_promoted(self):
        src=self.d["source_authority_status"]
        self.assertTrue(src["curriculum_177"]["source_content_precheck_complete"])
        self.assertFalse(src["curriculum_177"]["central_index_authority"])
        self.assertFalse(src["curriculum_177"]["canonical_promotion"])
        self.assertFalse(src["curriculum_177"]["learning_index_consumption_allowed"])
        self.assertIsNone(src["curriculum_177"]["blocking_item"])
        self.assertEqual(src["curriculum_177"]["guard"],
                         "PRECHECK_COMPLETE != INDEX_OWNER_PROMOTION")
        self.assertFalse(src["english_lexical"]["runtime_authority"])
        self.assertFalse(src["english_language_usage"]["runtime_authority"])
        self.assertEqual(src["english_language_usage"]["state"],
                         "OPEN__NO_UNCONDITIONAL_PROVIDER_SELECTED")

    def test_memory_routing_stays_candidate(self):
        c=set(self.d["systems"]["HIDE_SEEK"]["candidate_not_core"])
        self.assertEqual(c,{
            "per_word_auto_routing","adaptive_past_word_ratio","delayed_recall_automation"
        })

if __name__=="__main__":
    unittest.main()
