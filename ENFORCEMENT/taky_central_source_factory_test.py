"""Centralized source factory regression on isolated disposable SQLite."""
import hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
import taky_central_source_factory as factory

class CentralFactoryTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  self.c=factory.connect(self.root/"central.sqlite3")
  self.addCleanup(self.c.close)
 def test_drive_metadata_remains_missing_raw_and_runtime_excluded(self):
  item=lambda fid,title:{"file_id":fid,"name":title,"kind":"file","size_bytes":"100",
   "mime_type":"application/pdf","modified":"2026-10-12"}
  d={"schema":"TAKY_CROSS_STORAGE_DRIVE_DISCOVERY_V1","folders":[
   {"account":"HNS","role":"RAW","group":"LEARNING_RAW","id":"loc","files":[item("f1","과학교재.pdf")]},
   {"account":"HNS","role":"RAW","group":"LEARNING_RAW","id":"loc","files":[item("f1","과학교재.pdf")]},
   {"account":"SIEZEALL","role":"MIXED_EXCLUDE_RUNTIME","group":"ROOT","id":"root","files":[item("secret","learner_session.json")]},
   {"account":"HNS","role":"RAW","group":"folders","id":"root","files":[{"file_id":"folder","name":"unit","kind":"folder"}]}
  ]}
  r=factory.ingest_drive(self.c,d)
  self.assertEqual(r["file_locations"],3)
  self.assertEqual(self.c.execute("SELECT COUNT(*) FROM location").fetchone()[0],2)
  self.assertEqual(r["excluded_operational"],1)
  s=factory.report(self.c)
  self.assertEqual(s["source_statuses"].get("RAW_VERIFIED",0),0)
  self.assertEqual(self.c.execute("SELECT COUNT(*) FROM event WHERE kind='SOURCE_REGISTERED'").fetchone()[0],2)
  self.assertEqual(self.c.execute("SELECT COUNT(*) FROM stage WHERE stage='LEARNING'").fetchone()[0],0)
 def test_one_content_multiple_project_paths_no_duplicate_source(self):
  p=self.root/"source";p.mkdir()
  files=[p/"one.txt",p/"two.txt"]
  for f in files:f.write_text("학습 단어 분류\nword words word\n",encoding="utf-8")
  checksum=factory.file_hash(files[0])
  ids=[factory.register(self.c,"LOCAL_FILE","TAKY_SOURCE_VAULT",str(f),f.name,
    "REFERENCE_CANDIDATE",sha=checksum,size=f.stat().st_size,consumer="ARCHI_GROW")
    for f in files]
  self.assertEqual(ids[0],ids[1])
  self.assertEqual(factory.report(self.c)["source_records"],1)
  self.assertEqual(factory.report(self.c)["source_locations"],2)
  result=factory.run_bounded(self.c,max_items=4,max_hash_bytes=100_000)
  self.assertEqual(result["technical_index_candidates"],1)
  self.assertEqual(self.c.execute("SELECT state FROM stage WHERE stage='FORMING'").fetchone()[0],"BLOCKED_REVIEW_NOT_APPROVED")
  self.assertEqual(self.c.execute("SELECT state FROM stage WHERE stage='LEARNING'").fetchone()[0],"BLOCKED_FORMING_NOT_APPROVED")
  for f in files:
   self.assertEqual(factory.register(self.c,"LOCAL_FILE","TAKY_SOURCE_VAULT",
       str(f),f.name,"REFERENCE_CANDIDATE",sha=checksum,
       size=f.stat().st_size,consumer="ARCHI_GROW"),ids[0])
  self.assertEqual(self.c.execute("SELECT status FROM source").fetchone()[0],"INDEXED_CANDIDATE")
  self.assertEqual(self.c.execute("SELECT state FROM stage WHERE stage='EXTRACT'").fetchone()[0],"DONE")
  self.assertEqual(factory.run_bounded(self.c,4,100_000)["technical_index_candidates"],0)
 def test_local_unverified_only_hashed_under_budget(self):
  p=self.root/"archive";p.mkdir()
  f=p/"reference.txt";f.write_text("Hello classification",encoding="utf-8")
  r=factory.discover_archive(self.c,p,limit=10,allowed_root=self.root)
  self.assertEqual(r["files"],1)
  self.assertEqual(factory.report(self.c)["source_statuses"]["RAW_NOT_VERIFIED"],1)
  skip=factory.run_bounded(self.c,1,0)
  self.assertEqual(skip["local_hashes_computed"],0)
  done=factory.run_bounded(self.c,1,1000)
  self.assertEqual(done["local_hashes_computed"],1)
  self.assertEqual(factory.report(self.c)["source_statuses"]["INDEXED_CANDIDATE"],1)
  self.assertEqual(factory.run_bounded(self.c,1,1000)["local_hashes_computed"],0)
 def test_raw_cannot_claim_verified_after_revision(self):
  p=self.root/"archive";p.mkdir()
  f=p/"same.txt";f.write_text("old revision",encoding="utf-8")
  factory.discover_archive(self.c,p,allowed_root=self.root)
  factory.run_bounded(self.c,1,1000)
  before=factory.report(self.c)["source_records"]
  f.write_text("changed revision new payload",encoding="utf-8")
  factory.discover_archive(self.c,p,allowed_root=self.root)
  state=factory.report(self.c)
  # Current physical source path changed, but old hash source/event remains
  # addressable for immutable history.
  self.assertEqual(state["source_records"],before+1)
  self.assertEqual(factory.run_bounded(self.c,1,1000)["local_hashes_computed"],1)
  # A new archive version must not silently inherit RAW_VERIFIED. See change
  # detection gate in the source factory; ingestion should demote and reverify.
  self.assertGreaterEqual(factory.report(self.c)['source_statuses'].get('SUPERSEDED',0),1)
  self.assertEqual(factory.run_bounded(self.c,1,1000)['local_hashes_computed'],0)
 def test_reject_invalid_hash_and_untrusted_folder_overrides(self):
  with self.assertRaises(ValueError):
   factory.register(self.c,"LOCAL_FILE","LOCAL","x","document.txt","REFERENCE",sha="notsha")
  with self.assertRaises(ValueError):
   factory.ingest_drive(self.c,{"schema":"WRONG","folders":[]})

if __name__=="__main__":unittest.main()
