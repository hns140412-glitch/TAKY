#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"MIGRATION/INDEX_OWNER/DATA_INDEX_V27_INDEX_OWNER_RECEIPT_2026-10-02_V1.json"
CURR=ROOT/"MIGRATION/CURRICULUM/READY_OFFICIAL_STANDARD_REGISTRY_2026-10-02_V1.json"

class TestV27IndexOwnerReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.c=json.loads(CURR.read_text(encoding="utf-8"))

    def test_exact_promotion_scope(self):
        r=self.r
        self.assertEqual(r["status"],"INDEXED_REVISION_CREATED__NOT_CURRENT__NOT_CANONICAL")
        self.assertEqual(len(self.c["records"]),177)
        self.assertEqual(r["counts"]["base"],679)
        self.assertEqual(r["counts"]["added"],178)
        self.assertEqual(r["counts"]["total"],857)
        self.assertEqual(r["counts"]["curriculum_alignment"],177)
        self.assertEqual(r["counts"]["lexical_semantics"],1)
        self.assertEqual(r["counts"]["language_usage"],0)

    def test_roles_and_holds(self):
        roles=self.r["roles"]
        self.assertEqual(roles["CURRICULUM_ALIGNMENT"]["state"],"INDEXED")
        self.assertTrue(roles["CURRICULUM_ALIGNMENT"]["learning_index_consumption_allowed"])
        self.assertEqual(roles["LEXICAL_SEMANTICS"]["source_id"],"LEXICAL_OEWN_2025")
        self.assertEqual(roles["LEXICAL_SEMANTICS"]["license"],"CC-BY-4.0")
        self.assertTrue(roles["LEXICAL_SEMANTICS"]["attribution_required"])
        self.assertEqual(roles["LANGUAGE_USAGE"]["state"],"HOLD")

    def test_no_current_or_canonical_promotion(self):
        g=self.r["guards"]
        self.assertFalse(g["canonical"])
        self.assertFalse(g["current"])
        self.assertFalse(g["current_pointer_changed"])
        self.assertFalse(g["main_merge"])
        self.assertFalse(g["deployment"])
        self.assertFalse(g["oewn_gloss_is_child_level_easy_english"])
        self.assertFalse(g["curriculum_alignment_is_lexical_semantics"])

if __name__=="__main__":
    unittest.main()
