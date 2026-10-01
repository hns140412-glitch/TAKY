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
        self.assertEqual(d["status"],
                         "BRANCH_INDEXED_AND_IO_VALIDATED__CURRENT_CANONICAL_PROMOTION_HOLD")
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
        self.assertIn("recommended_quantity_intent",s["LEARNING_ENGINE"]["owns"])
        self.assertIn("allocated_quantity",s["LEARNING_ENGINE"]["forbidden"])
        self.assertIn("actual_quantity_materialization",s["PLANNER"]["owns"])
        self.assertIn("local_language_quality_grading",s["SNAP_POP"]["forbidden"])
        self.assertIn("mastery_authority",s["HIDE_SEEK"]["forbidden"])
        self.assertIn("IMAGINATION_CLOUD",s)
        self.assertIn("mastery",s["IMAGINATION_CLOUD"]["forbidden"])

    def test_learning_index_roles_are_separate(self):
        roles=self.d["systems"]["LEARNING_INDEX"]["evidence_roles"]
        self.assertEqual(set(roles),{
            "CURRICULUM_ALIGNMENT","LEXICAL_SEMANTICS","LANGUAGE_USAGE",
            "PEDAGOGICAL_USAGE","GENERAL_REFERENCE"
        })
        inv=set(self.d["invariants"])
        self.assertIn("CURRICULUM_ALIGNMENT != LEXICAL_SEMANTICS",inv)
        self.assertIn("LEXICAL_SEMANTICS != LANGUAGE_USAGE",inv)

    def test_v27_indexed_sources_are_not_current_or_canonical(self):
        src=self.d["source_authority_status"]
        curriculum=src["curriculum_177"]
        self.assertEqual(curriculum["index_state"],"INDEXED")
        self.assertEqual(curriculum["index_revision"],"V27")
        self.assertEqual(curriculum["record_count"],177)
        self.assertTrue(curriculum["central_index_authority_in_revision"])
        self.assertTrue(curriculum["learning_index_consumption_allowed"])
        self.assertFalse(curriculum["current"])
        self.assertFalse(curriculum["canonical"])

        lexical=src["english_lexical"]
        self.assertEqual(lexical["index_state"],"INDEXED")
        self.assertEqual(lexical["index_revision"],"V27")
        self.assertEqual(lexical["source_id"],"LEXICAL_OEWN_2025")
        self.assertEqual(lexical["license"],"CC-BY-4.0")
        self.assertTrue(lexical["attribution_required"])
        self.assertTrue(lexical["learning_index_consumption_allowed"])
        self.assertFalse(lexical["current"])
        self.assertFalse(lexical["canonical"])

        usage=src["english_language_usage"]
        self.assertEqual(usage["index_state"],"HOLD")
        self.assertEqual(usage["indexed_count"],0)
        self.assertFalse(usage["learning_index_consumption_allowed"])
        self.assertEqual(usage["license"],"CC-BY-SA-4.0")
        self.assertFalse(usage["current"])
        self.assertFalse(usage["canonical"])

    def test_memory_routing_stays_candidate(self):
        c=set(self.d["systems"]["HIDE_SEEK"]["candidate_not_core"])
        self.assertEqual(c,{
            "per_word_auto_routing","adaptive_past_word_ratio","delayed_recall_automation"
        })

if __name__=="__main__":
    unittest.main()
