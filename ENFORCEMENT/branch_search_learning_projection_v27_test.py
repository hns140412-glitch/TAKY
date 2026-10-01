#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"MIGRATION/PROJECTION/DATA_INDEX_V27_BRANCH_SEARCH_LEARNING_PROJECTION_2026-10-02_V1.json"

class TestBranchProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))

    def test_non_current_projection(self):
        d=self.d
        self.assertEqual(d["status"],"BRANCH_SCOPED_REBUILT__NOT_CURRENT__NOT_CANONICAL")
        self.assertEqual(d["counts"]["total"],178)
        self.assertFalse(d["guards"]["current_pointer_changed"])
        self.assertFalse(d["guards"]["canonical_promotion"])
        self.assertTrue(d["guards"]["rebuildable_derived_layer"])

    def test_roles(self):
        rows=self.d["learning_projection"]
        curriculum=[x for x in rows if x["learning_evidence_role"]=="CURRICULUM_ALIGNMENT"]
        lexical=[x for x in rows if x["learning_evidence_role"]=="LEXICAL_SEMANTICS"]
        usage=[x for x in rows if x["learning_evidence_role"]=="LANGUAGE_USAGE"]
        self.assertEqual(len(curriculum),177)
        self.assertEqual(len(lexical),1)
        self.assertEqual(len(usage),0)
        self.assertEqual(lexical[0]["source_id"],"LEXICAL_OEWN_2025")
        self.assertFalse(lexical[0]["child_level_definition_authority"])
        self.assertFalse(lexical[0]["grade_alignment_authority"])
        self.assertEqual(len({x["source_id"] for x in rows}),178)

    def test_subject_counts(self):
        counts={}
        for row in self.d["learning_projection"]:
            cur=row.get("curriculum")
            if cur:
                counts[cur["subject"]]=counts.get(cur["subject"],0)+1
        self.assertEqual(counts,{"국어":34,"수학":45,"사회":27,"과학":51,"영어":20})
        self.assertTrue(self.d["guards"]["ud_ewt_language_usage_excluded"])

if __name__=="__main__":
    unittest.main()
