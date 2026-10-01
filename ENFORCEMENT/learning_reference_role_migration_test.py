#!/usr/bin/env python3
import copy,json,unittest
from pathlib import Path
from learning_reference_role_migration import validate,PATH

class TestMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PATH.read_text(encoding="utf-8"))

    def test_valid_candidate_is_non_authoritative(self):
        out=validate(self.data)
        self.assertTrue(out["pass"],out)
        self.assertEqual(out["candidate_count"],3)

    def test_cannot_promote_before_index_review(self):
        bad=copy.deepcopy(self.data)
        bad["authority_guards"]["central_index_authority"]=True
        self.assertFalse(validate(bad)["pass"])

    def test_ro_on_cannot_become_lexical_authority(self):
        bad=copy.deepcopy(self.data)
        row=next(x for x in bad["candidates"] if x["candidate_id"]=="LRM-ROON-REFERENCE-2026-09-25")
        row["forbidden_use"]=[x for x in row["forbidden_use"] if x!="lexical-definition authority"]
        out=validate(bad)
        self.assertFalse(out["pass"])
        self.assertIn("ROON_LEXICAL_AUTHORITY_FORBIDDEN_GUARD_MISSING",out["issues"])

if __name__=="__main__":
    unittest.main()
