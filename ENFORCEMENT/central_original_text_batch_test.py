"""Disposable SQLite / real filesystem proof for bounded raw body-text indexer."""
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

import central_original_text_batch as batch
import taky_central_source_factory as factory


class OriginalTextBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.db=self.root/"isolated.sqlite3"
        self.c=factory.connect(self.db)
        self.addCleanup(self.c.close)
        self.path=self.root/"source.txt"
        self.raw=("# Source document\n\n"+("\n".join(
           f"Line {i:03d}: authentic source material with unicode text." for i in range(110))
           )+"\n").encode("utf-8")
        self.path.write_bytes(self.raw)
        self.sha=hashlib.sha256(self.raw).hexdigest()
        self.sid=factory.register(self.c,"LOCAL_FILE","TAKY_REVIEW_RAW",str(self.path),
           "source.txt","RAW_VERIFIED_PENDING_REVIEW",
           sha=self.sha,size=len(self.raw),modified=str(self.path.stat().st_mtime_ns))
        self.assertEqual(self.sid,"raw:"+self.sha)

    def test_hash_anchored_text_and_idempotent_stage(self):
        with patch.object(batch,"ROOT",self.root.resolve()):
            result=batch.run(self.c,limit=3)
            self.assertEqual(result["processed"],1)
            self.assertGreater(result["units_added"],1)
            self.assertEqual(batch.run(self.c,limit=3)["processed"],0)
        self.assertEqual(self.c.execute(
            "SELECT state FROM stage WHERE source_id=? AND stage='INDEX'",
            (self.sid,)).fetchone()[0],"TECHNICAL_INDEX_READY")
        self.assertEqual(self.c.execute(
            "SELECT state FROM stage WHERE source_id=? AND stage='FORMING'",
            (self.sid,)).fetchone()[0],"BLOCKED_REVIEW_NOT_APPROVED")
        self.assertEqual(self.c.execute(
            "SELECT authoritative_review FROM source WHERE id=?",(self.sid,)
            ).fetchone()[0],"UNREVIEWED")
        rows=self.c.execute("SELECT unit_id,review_state FROM evidence_unit WHERE source_id=?",
                            (self.sid,)).fetchall()
        self.assertEqual(len(rows),result["units_added"])
        for unit_id,state in rows:
            self.assertEqual(state,"EXTRACTIVE_UNREVIEWED")
            check=factory.read_verified_evidence_unit(self.c,self.sid,unit_id)
            self.assertEqual(check["raw_sha256"],self.sha)
            self.assertFalse(check["forming_authorized"])
        self.c.commit()
        with closing(sqlite3.connect(self.db)) as persisted:
            self.assertEqual(persisted.execute(
                "SELECT COUNT(*) FROM evidence_unit WHERE source_id=?",
                (self.sid,)).fetchone()[0],len(rows))

    def test_changed_original_refused_without_index(self):
        self.path.write_bytes(self.raw+b"CHANGED")
        with patch.object(batch,"ROOT",self.root.resolve()):
            with self.assertRaisesRegex(ValueError,"RAW_SIZE_CHANGED"):
                batch.run(self.c,limit=3)
        self.assertEqual(self.c.execute(
            "SELECT COUNT(*) FROM evidence_unit").fetchone()[0],0)

    def test_metadata_json_is_not_body_candidate(self):
        fake=self.root/"links.json"
        fake.write_text('{"links":["https://example.org"]}',encoding="utf-8")
        content=fake.read_bytes()
        factory.register(self.c,"LOCAL_FILE","TAKY_REVIEW_RAW",str(fake),
                         fake.name,"RAW_VERIFIED_PENDING_REVIEW",
                         sha=hashlib.sha256(content).hexdigest(),size=len(content))
        results=batch.candidates(self.c,limit=4)
        self.assertEqual([x["id"] for x in results],[self.sid])

    def test_unsafe_role_and_original_immutability(self):
        row=batch.candidates(self.c,1)[0]
        forged=dict(row,source_role="USER_DATA")
        with patch.object(batch,"ROOT",self.root.resolve()):
            with self.assertRaisesRegex(ValueError,"SOURCE_ACCOUNT_ROLE_SCOPE_INVALID"):
                batch.process_one(self.c,forged)
        self.assertEqual(self.c.execute(
            "SELECT COUNT(*) FROM evidence_unit").fetchone()[0],0)


if __name__=="__main__":
    unittest.main()
