"""Non-authoritative repair of SHA-identical re-registration regressions."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import central_original_text_batch as original
import central_source_state_reconciler as repair
import taky_central_source_factory as factory


class ReRegisterRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.original=self.root/"original.txt"
        self.original.write_text(
          "# Verified source\n"+("\n".join(
           f"Row {i:03d} independent source data evidence" for i in range(180))),
          encoding="utf-8")
        self.digest=factory.file_hash(self.original)
        self.c=factory.connect(self.root/"test.sqlite3")
        self.addCleanup(self.c.close)
        self.sid=factory.register(self.c,"LOCAL_FILE","TAKY_REVIEW_RAW",
           str(self.original),self.original.name,"RAW_VERIFIED_PENDING_REVIEW",
           sha=self.digest,size=self.original.stat().st_size)
        with patch.object(original,"ROOT",self.root):
            result=original.run(self.c,4)
        self.assertEqual(result["processed"],1)
        self.c.execute("UPDATE source SET status='RAW_VERIFIED' WHERE id=?",
            (self.sid,))
        factory.put_stage(self.c,self.sid,"EXTRACT","PENDING",
                          {"simulated_same_hash_legacy_regression":True})

    def test_repair_full_raw_and_all_anchors_before_restoring(self):
        self.assertEqual(len(repair.select_inconsistent(self.c)),1)
        result=repair.reconcile(self.c)
        self.assertEqual(result["corrected_sources"],1)
        self.assertGreater(result["verified_original_line_units"],1)
        self.assertEqual(repair.reconcile(self.c)["corrected_sources"],0)
        self.assertEqual(self.c.execute("SELECT status FROM source").fetchone()[0],
                         "INDEXED_CANDIDATE")
        self.assertEqual(self.c.execute(
            "SELECT state FROM stage WHERE source_id=? AND stage='EXTRACT'",
            (self.sid,)).fetchone()[0],"DONE")
        factory.register(self.c,"LOCAL_FILE","TAKY_REVIEW_RAW",
           str(self.original),self.original.name,"RAW_VERIFIED_PENDING_REVIEW",
           sha=self.digest,size=self.original.stat().st_size)
        self.assertEqual(self.c.execute("SELECT status FROM source").fetchone()[0],
                         "INDEXED_CANDIDATE")
        self.assertEqual(self.c.execute(
            "SELECT state FROM stage WHERE source_id=? AND stage='EXTRACT'",
            (self.sid,)).fetchone()[0],"DONE")
        self.assertEqual(self.c.execute(
            "SELECT authoritative_review FROM source").fetchone()[0],"UNREVIEWED")

    def test_modified_original_fails_without_mutating_stage(self):
        self.original.write_text("CHANGED ORIGINAL CONTENT",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"DETAIL_SOURCE_RAW_HASH_MISMATCH"):
            repair.reconcile(self.c)
        self.assertEqual(self.c.execute(
            "SELECT state FROM stage WHERE source_id=? AND stage='EXTRACT'",
            (self.sid,)).fetchone()[0],"PENDING")


if __name__=="__main__":
    unittest.main()
