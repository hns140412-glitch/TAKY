"""Original PDF bytes in disposable Central SQLite; never OCR or authority."""
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

import central_pdf_page_batch as pdf
import taky_central_source_factory as factory


class PdfPageBatch(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"isolated.sqlite3"
        self.db=factory.connect(self.path)
        self.addCleanup(self.db.close)
        with closing(sqlite3.connect(
            "file:"+str(factory.DB).replace("\\","/")+"?mode=ro",uri=True
        )) as c:
            c.row_factory=sqlite3.Row
            self.rows=pdf.candidates(c,16)
        self.assertEqual(len(self.rows),16)
        for row in self.rows:
            source=Path(row["locator"])
            sid=factory.register(self.db,"LOCAL_FILE",row["account"],
                row["locator"],source.name,row["source_role"],
                sha=row["original_sha256"],size=row["size_bytes"])
            self.assertEqual(sid,row["id"])

    def test_real_pdf_batch_replay_and_live_sha(self):
        result=pdf.run(self.db,16)
        self.assertEqual(result["processed"],16)
        self.assertGreater(result["indexed_pdf_sources"],8)
        self.assertGreater(result["page_units_added"],10)
        self.assertGreaterEqual(result["specialist_hold"],1)
        self.assertEqual(pdf.run(self.db,16)["processed"],0)
        examples=self.db.execute(
           "SELECT source_id,page_number FROM pdf_page_evidence ORDER BY source_id,page_number LIMIT 3"
        ).fetchall()
        for sid,n in examples:
            verified=pdf.read_verified_page(self.db,sid,n)
            self.assertEqual(verified["review_state"],"EXTRACTIVE_UNREVIEWED")
            self.assertFalse(verified["forming_authorized"])
        import re
        sample=self.db.execute(
            "SELECT source_id,page_number,page_text FROM pdf_page_evidence "
            "WHERE LENGTH(page_text)>100 LIMIT 1").fetchone()
        term=re.search(r"[A-Za-z가-힣]{3,}",sample["page_text"]).group(0)[:4]
        hits=pdf.find_pdf_page_units(self.db,term)
        self.assertTrue(any(x["source_id"]==sample["source_id"]
            and x["page_number"]==sample["page_number"] for x in hits))
        self.assertTrue(all(x["authority"] is False for x in hits))
        self.assertEqual(self.db.execute(
           "SELECT COUNT(*) FROM source WHERE authoritative_review!='UNREVIEWED'"
        ).fetchone()[0],0)
        self.db.commit()
        with closing(sqlite3.connect(self.path)) as reopened:
            self.assertEqual(reopened.execute(
                "SELECT COUNT(*) FROM pdf_page_evidence"
            ).fetchone()[0],result["page_units_added"])

    def test_300kb_to_4mb_real_pdf_batch_without_small_file_reprocessing(self):
        with closing(sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True)) as source:
            source.row_factory=sqlite3.Row
            large=pdf.candidates(source,16,min_bytes=300001)
        self.assertEqual(len(large),16)
        self.assertTrue(all(300001<=r["size_bytes"]<=pdf.MAX_FILE_BYTES
                            for r in large))
        for row in large:
            original=Path(row["locator"])
            self.assertEqual(factory.register(self.db,"LOCAL_FILE",
                row["account"],row["locator"],original.name,row["source_role"],
                sha=row["original_sha256"],size=row["size_bytes"]),row["id"])
        result=pdf.run(self.db,16,min_bytes=300001)
        self.assertEqual(result["processed"],16)
        self.assertGreater(result["indexed_pdf_sources"],5)
        self.assertGreater(result["page_units_added"],10)
        self.assertEqual(pdf.run(self.db,16,min_bytes=300001)["processed"],0)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM source WHERE authoritative_review!='UNREVIEWED'"
        ).fetchone()[0],0)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM source WHERE status='INDEXED_CANDIDATE'"
        ).fetchone()[0],result["indexed_pdf_sources"])

    def test_pdf_text_tamper_is_rejected(self):
        result=pdf.run(self.db,16)
        sid,n=self.db.execute(
            "SELECT source_id,page_number FROM pdf_page_evidence LIMIT 1"
        ).fetchone()
        original=self.db.execute("SELECT text_sha256 FROM pdf_page_evidence "
              "WHERE source_id=? AND page_number=?",(sid,n)).fetchone()[0]
        self.db.execute("UPDATE pdf_page_evidence SET text_sha256=? "
              "WHERE source_id=? AND page_number=?",("0"*64,sid,n))
        with self.assertRaisesRegex(ValueError,"PDF_PAGE_EXTRACTED_TEXT_CHANGED"):
            pdf.read_verified_page(self.db,sid,n)
        self.db.execute("UPDATE pdf_page_evidence SET text_sha256=? "
              "WHERE source_id=? AND page_number=?",(original,sid,n))
        self.assertIsNotNone(pdf.read_verified_page(self.db,sid,n))


if __name__=="__main__":
    unittest.main()
