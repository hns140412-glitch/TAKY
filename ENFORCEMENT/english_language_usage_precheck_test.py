#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"MIGRATION/INDEX_OWNER/ENGLISH_LANGUAGE_USAGE_PRECHECK_2026-10-02_V1.json"

class TestEnglishLanguageUsagePrecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))

    def test_precheck_never_self_promotes(self):
        d=self.d
        self.assertEqual(d["authority"],"INDEX_OWNER_PRECHECK_ONLY")
        self.assertFalse(d["decision"]["runtime_authority_granted"])
        self.assertFalse(d["decision"]["language_usage_gap_closed"])
        self.assertIn("PRECHECK != INDEXED",d["guards"])
        for row in d["candidates"]:
            self.assertFalse(row["promotion_authorized"])
            self.assertFalse(row["runtime_authority"])

    def test_tatoeba_is_example_only_decision_ready(self):
        rows={x["candidate_id"]:x for x in self.d["candidates"]}
        row=rows["ENGLISH_USAGE_TATOEBA_TEXT"]
        self.assertEqual(row["evidence_kind"],"EXAMPLE_SENTENCE")
        self.assertEqual(row["license"],"CC-BY-2.0-FR")
        self.assertTrue(row["attribution_required"])
        self.assertTrue(row["formal_index_owner_decision_ready"])
        self.assertIn("frequency_authority",row["forbidden_claims"])
        self.assertIn("universal_naturalness_truth",row["forbidden_claims"])

    def test_ud_pattern_sources_remain_blocked(self):
        rows={x["candidate_id"]:x for x in self.d["candidates"]}
        ewt=rows["ENGLISH_USAGE_UD_EWT"]
        childes=rows["ENGLISH_USAGE_UD_CHILDES"]
        self.assertEqual(ewt["evidence_kind"],"DEPENDENCY_PATTERN")
        self.assertEqual(ewt["license"],"CC-BY-SA-4.0")
        self.assertFalse(ewt["formal_index_owner_decision_ready"])
        self.assertTrue(ewt["blocking_items"])
        self.assertEqual(childes["evidence_kind"],
                         "CHILD_ADULT_SPOKEN_DEPENDENCY_PATTERN")
        self.assertEqual(childes["license"],"CC-BY-SA-4.0")
        self.assertFalse(childes["formal_index_owner_decision_ready"])
        self.assertIn("AGE_AND_CONTEXT_TRANSFER_POLICY_REQUIRED",
                      childes["blocking_items"])

    def test_partial_gap_model(self):
        d=self.d["decision"]
        self.assertEqual(d["ready_for_human_index_decision"],
                         ["ENGLISH_USAGE_TATOEBA_TEXT"])
        self.assertEqual(d["partial_gap_possible_after_tatoeba_indexing"],
                         "EXAMPLE_SENTENCE_ONLY")
        self.assertTrue(d["dependency_pattern_gap_remains"])

if __name__=="__main__":
    unittest.main()
