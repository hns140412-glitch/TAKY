import tempfile,unittest,sqlite3
from contextlib import closing
from pathlib import Path
import taky_review_reference_intake as intake
class TestIntake(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  root=Path(self.tmp.name)
  self.wh=root/"REFERENCE"
  self.db=root/"source.sqlite3"
  self.a=root/"uploaded_과학자료.txt"
  self.a.write_text("교과서 과학 참조 원문",encoding="utf-8")
 def test_one_physical_original_two_upload_names(self):
  first=intake.from_file(self.a,title="초등 과학 교과 참고",warehouse=self.wh,db=self.db)
  self.assertTrue(first["new_physical_copy_created"])
  self.assertTrue(Path(first["canonical_path"]).is_file())
  b=Path(self.tmp.name)/"another.txt";b.write_bytes(self.a.read_bytes())
  second=intake.from_file(b,title="동일 파일 다른 이름",warehouse=self.wh,db=self.db)
  self.assertFalse(second["new_physical_copy_created"])
  self.assertEqual(first["source_id"],second["source_id"])
  self.assertEqual(first["canonical_path"],second["canonical_path"])
  self.assertEqual(sum(1 for x in self.wh.rglob("*") if x.is_file()),1)
  with closing(sqlite3.connect(self.db)) as conn:
   self.assertEqual(conn.execute("SELECT state FROM stage WHERE stage='FORMING'").fetchone()[0],"BLOCKED_PENDING_REVIEW")
 def test_url_is_not_falsely_mined(self):
  record=intake.from_url("https://example.com/learn/physics",title="초등 과학",warehouse=self.wh,db=self.db)
  self.assertFalse(record["physical_snapshot_acquired"])
  with closing(sqlite3.connect(self.db)) as c:
   self.assertEqual(c.execute("SELECT state FROM stage WHERE stage='EXTRACT'").fetchone()[0],"WAITING_RAW_BYTES")
   self.assertEqual(c.execute("SELECT status FROM source").fetchone()[0],"RAW_NOT_VERIFIED")
 def test_reject_zero_and_bad_url(self):
  self.a.write_bytes(b"")
  with self.assertRaises(ValueError):intake.from_file(self.a,warehouse=self.wh,db=self.db)
  with self.assertRaises(ValueError):intake.from_url("file:///secret",warehouse=self.wh,db=self.db)
if __name__=="__main__":unittest.main()
