#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"MIGRATION/LEARNING_REFERENCE/ENGLISH_LEXICAL_USAGE_SOURCE_CANDIDATES_2026-10-02_V1.json"

class TestEnglishSourceCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PATH.read_text(encoding="utf-8"))

    def test_candidates_never_claim_runtime_authority(self):
        d=self.data
        self.assertEqual(d["status"],"SOURCE_CANDIDATES_ONLY__NO_RUNTIME_AUTHORITY")
        self.assertIn("SOURCE_CANDIDATE != INDEXED",d["guards"])
        self.assertIn("INDEXED != CANONICAL",d["guards"])
        self.assertIsNone(d["decision"]["preferred_usage_candidate"])
        self.assertEqual(d["decision"]["preferred_usage_precheck_candidate"],
                         "ENGLISH_USAGE_UD_EWT")
        self.assertEqual(d["decision"]["usage_gap_state"],
                         "CANDIDATE_FOUND__LICENSE_AND_INDEX_OWNER_REVIEW_OPEN")

    def test_open_english_wordnet_is_lexical_candidate_only(self):
        row=next(x for x in self.data["lexical_semantics"]
                 if x["candidate_id"]=="ENGLISH_LEXICAL_OEWN_2025")
        self.assertEqual(row["proposed_learning_evidence_role"],"LEXICAL_SEMANTICS")
        self.assertEqual(row["license"],"CC-BY-4.0")
        self.assertTrue(row["index_owner_review_required"])
        self.assertIn("grade/curriculum authority",row["forbidden_candidate_use"])
        self.assertIn("DERIVED_EASY_ENGLISH_PARAPHRASE_CANDIDATE",row["proposed_runtime_pattern"])

    def test_paid_or_restricted_sources_remain_hold(self):
        rows={x["candidate_id"]:x for x in self.data["lexical_semantics"]}
        self.assertTrue(rows["ENGLISH_LEXICAL_OXFORD_API"]["disposition"].startswith("HOLD_"))
        self.assertTrue(rows["ENGLISH_LEXICAL_CAMBRIDGE_API"]["disposition"].startswith("HOLD_"))
        usage={x["candidate_id"]:x for x in self.data["language_usage"]}
        self.assertEqual(usage["ENGLISH_USAGE_UD_EWT"]["license"],"CC-BY-SA-4.0")
        self.assertFalse(usage["ENGLISH_USAGE_UD_EWT"]["runtime_authority"])
        self.assertIn("LICENSE_COMPATIBILITY_REVIEW_OPEN",
                      usage["ENGLISH_USAGE_UD_EWT"]["disposition"])
        self.assertTrue(usage["ENGLISH_USAGE_SKETCH_ENGINE"]["disposition"].startswith("HOLD_"))
        self.assertIn("SECONDARY_CANDIDATE",usage["ENGLISH_USAGE_LEIPZIG_CORPORA"]["disposition"])

if __name__=="__main__":
    unittest.main()
