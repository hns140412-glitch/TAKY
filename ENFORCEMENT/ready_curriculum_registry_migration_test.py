#!/usr/bin/env python3
import copy, json, unittest
from pathlib import Path
from ready_curriculum_registry_migration import load,validate

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"MIGRATION/CURRICULUM/READY_OFFICIAL_STANDARD_REGISTRY_2026-10-02_V1.json"

class TestReadyCurriculumMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load(PATH)

    def test_seed_is_complete_but_non_authoritative(self):
        out=validate(self.data)
        self.assertTrue(out["pass"],out)
        self.assertEqual(out["record_count"],177)
        self.assertEqual(out["by_subject"],{"국어":34,"수학":45,"사회":27,"과학":51,"영어":20})
        self.assertFalse(out["central_index_authority"])
        self.assertEqual(out["next_handoff"],"INDEPENDENT_INDEX_OWNER_REVIEW")

    def test_pre_review_promotion_fails(self):
        bad=copy.deepcopy(self.data)
        bad["records"][0]["proposed_index_record"]["index_state"]="INDEXED"
        bad["records"][0]["central_index_authority"]=True
        out=validate(bad)
        self.assertFalse(out["pass"])
        self.assertTrue(any("INDEX_STATE_MUST_BE_NULL" in x for x in out["issues"]))
        self.assertTrue(any("ROW_AUTHORITY_MUST_BE_FALSE" in x for x in out["issues"]))

    def test_duplicate_standard_fails(self):
        bad=copy.deepcopy(self.data)
        bad["records"][1]["standard_code"]=bad["records"][0]["standard_code"]
        out=validate(bad)
        self.assertFalse(out["pass"])
        self.assertIn("DUPLICATE_STANDARD_CODE",out["issues"])

if __name__=="__main__":
    unittest.main()
