"""Review notes stay untrusted and never confer FORMING authority."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import central_review_notes_router as router


class LocalReviewNotesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection=json.loads(router.SOURCE.read_text(encoding="utf-8"))
        cls.source_id=cls.projection["projected_sources"][0]["source_id"]

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"notes.json"
        self.notes={
           "schema":"TAKY_LOCAL_REVIEW_NOTES_V1",
           "source_projection_sha256":self.projection["manifest_sha256"],
           "non_authoritative":True,"independent_approval":False,
           "records":[{"source_id":self.source_id,"status":"revisit",
                       "text":"TEST_ONLY source applicability requires review"}]}
        self.path.write_text(json.dumps(self.notes),encoding="utf-8")

    def test_notes_are_non_authoritative_and_append_only(self):
        result=router.parse_notes(self.path,self.projection)
        self.assertEqual(result["source_count"],1)
        self.assertEqual(result["independent_approved_sources"],0)
        self.assertFalse(result["forming_approved"])
        self.assertFalse(result["notes"][0]["independent_index_owner_authorized"])
        folder=Path(self.temp.name)/"inbox"
        p,created=router.write_result(result,folder)
        again,second=router.write_result(result,folder)
        self.assertTrue(created)
        self.assertFalse(second)
        self.assertEqual(p,again)

    def test_forged_approval_and_stale_revision_are_refused(self):
        self.notes["independent_approval"]=True
        self.path.write_text(json.dumps(self.notes),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"AUTHORITY_INVALID"):
            router.parse_notes(self.path,self.projection)
        self.notes["independent_approval"]=False
        self.notes["source_projection_sha256"]="0"*64
        self.path.write_text(json.dumps(self.notes),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"AUTHORITY_INVALID"):
            router.parse_notes(self.path,self.projection)

    def test_unknown_or_duplicate_source_id_rejected(self):
        self.notes["records"]*=2
        self.path.write_text(json.dumps(self.notes),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"DUPLICATED"):
            router.parse_notes(self.path,self.projection)
        self.notes["records"]=[{"source_id":"raw:"+"0"*64,"status":"noted","text":"bad"}]
        self.path.write_text(json.dumps(self.notes),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"ROW_INVALID"):
            router.parse_notes(self.path,self.projection)


if __name__=="__main__":unittest.main()
