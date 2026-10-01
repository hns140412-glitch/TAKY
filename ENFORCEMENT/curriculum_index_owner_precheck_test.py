#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"MIGRATION/INDEX_OWNER/CURRICULUM_177_PRECHECK_2026-10-02_V1.json"

class TestCurriculumIndexOwnerPrecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PATH.read_text(encoding="utf-8"))

    def test_precheck_is_complete_but_non_authoritative(self):
        d=self.data
        self.assertEqual(d["status"],"PRECHECK_COMPLETE__NO_PROMOTION")
        self.assertEqual(d["authority"],"INDEX_OWNER_PRECHECK_ONLY")
        s=d["structural_checks"]
        self.assertEqual(s["record_count"],177)
        self.assertEqual(s["unique_standard_codes"],177)
        self.assertEqual(s["unique_proposed_source_ids"],177)
        self.assertEqual(s["duplicate_standard_codes"],[])
        self.assertEqual(s["duplicate_proposed_source_ids"],[])
        self.assertFalse(d["decision"]["central_index_authority"])
        self.assertFalse(d["decision"]["canonical_promotion"])
        self.assertFalse(d["decision"]["learning_index_consumption_allowed"])
        self.assertEqual(d["decision"]["blocking_items"],[])
        self.assertEqual(d["decision"]["disposition"],
                         "SOURCE_CONTENT_PRECHECK_COMPLETE__AWAITING_FORMAL_INDEX_OWNER_PROMOTION_DECISION")

    def test_source_family_counts_cover_all_records(self):
        rows=self.data["source_family_checks"]
        self.assertEqual(sum(x["record_count"] for x in rows),177)
        keys={x["source_key"] for x in rows}
        self.assertEqual(keys,{"GOE_KOREAN_56","GOE_FRAMEWORK_56","GOE_2026_EVAL","GOE_ENGLISH_56"})
        verified={x["source_key"]:x["external_verification"] for x in rows}
        self.assertEqual(verified["GOE_KOREAN_56"],
                         "VERIFIED_FULL_TABLE_EXACT_OFFICIAL_SOURCE_INDEX_EXTRACTION")
        korean=next(x for x in rows if x["source_key"]=="GOE_KOREAN_56")
        self.assertEqual(korean["verified_total_count"],34)
        self.assertEqual(sum(korean["verified_domain_counts"].values()),34)
        self.assertIn("6국06-04",korean["representative_codes"])
        self.assertEqual(verified["GOE_FRAMEWORK_56"],"VERIFIED_REPRESENTATIVE_CODES")
        self.assertEqual(verified["GOE_2026_EVAL"],"VERIFIED_EXACT_CODE")
        self.assertEqual(verified["GOE_ENGLISH_56"],"VERIFIED_REPRESENTATIVE_CODES")

if __name__=="__main__":
    unittest.main()
