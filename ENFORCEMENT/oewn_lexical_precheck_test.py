#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"MIGRATION/INDEX_OWNER/OEWN_2025_LEXICAL_PRECHECK_2026-10-02_V1.json"

class TestOEWNPrecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))

    def test_source_and_license_precheck_does_not_promote(self):
        d=self.d
        self.assertEqual(d["status"],
          "SOURCE_LICENSE_PRECHECK_COMPLETE__FORMAL_PROMOTION_DECISION_OPEN")
        self.assertEqual(d["source"]["license"],"CC-BY-4.0")
        self.assertEqual(d["source"]["release"],"2025")
        p=d["proposed_index_contract"]
        self.assertEqual(p["learning_evidence_role"],"LEXICAL_SEMANTICS")
        self.assertFalse(p["central_index_authority"])
        self.assertFalse(p["runtime_consumption_allowed"])
        self.assertFalse(p["canonical_promotion"])
        self.assertFalse(d["decision"]["promotion_authorized"])
        self.assertTrue(d["decision"]["formal_index_owner_promotion_required"])

    def test_easy_english_stays_derived(self):
        c=self.d["derived_use_contract"]
        self.assertTrue(c["source_gloss_is_lexical_evidence"])
        self.assertFalse(c["source_gloss_is_child_level_definition"])
        self.assertTrue(c["easy_english_definition_must_be_derived_and_traceable"])
        self.assertTrue(c["attribution_required"])
        self.assertFalse(c["grade_alignment_authority"])
        self.assertFalse(c["learner_state_authority"])

if __name__=="__main__":
    unittest.main()
