#!/usr/bin/env python3
import hashlib, json, tempfile, unittest, zipfile
from pathlib import Path
from mining_verified_archive_manifest import review_original_archive

DATA=b"official-test-byte-content"
SHA=hashlib.sha256(DATA).hexdigest()
NAME="science.pdf"
URL="https://www.ice.go.kr/upload/ice/science.pdf"
def archive(path, *, digest=SHA, declared=len(DATA), name=NAME, extra=False):
    m={"publisher_post":"https://www.ice.go.kr/ice/post",
       "source_entries":[{"name":name,"bytes":declared,"sha256":digest,
                          "official_url":URL}]}
    with zipfile.ZipFile(path,"w") as z:
        z.writestr(name,DATA)
        if extra:z.writestr("unmanifested.pdf",b"x")
        z.writestr("SOURCE_MANIFEST.json",json.dumps(m))
class VerifiedArchiveTest(unittest.TestCase):
 def test_physical_hash_and_nonpromotion(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"proof.zip"; archive(path)
   x=review_original_archive(path)
   self.assertEqual(x["file_count"],1)
   self.assertEqual(x["files"][0]["sha256"],SHA)
   self.assertEqual(x["files"][0]["classification"],"NO_KNOWN_HASH_MATCH_OWNER_REVIEW_PENDING")
   self.assertFalse(x["canonical_write"])
 def test_exact_hash_and_title_only_are_distinct(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"proof.zip";archive(p)
   exact=review_original_archive(p,[{"source_id":"EXACT","content_hash":SHA}])
   self.assertEqual(exact["files"][0]["classification"],"EXACT_DUPLICATE_CANDIDATE")
   titled=review_original_archive(p,[{"source_id":"OLD","canonical_title":NAME,"content_hash":"0"*64}])
   self.assertEqual(titled["files"][0]["classification"],"POSSIBLE_VERSION_HOLD")
 def test_mismatched_declared_hash_size_and_omitted_file_fail(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"proof.zip"
   for options in ({"digest":"0"*64},{"declared":len(DATA)+1},{"extra":True}):
    archive(p,**options)
    with self.assertRaises(ValueError):review_original_archive(p)
 def test_path_traversal_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"proof.zip";archive(p,name="../science.pdf")
   with self.assertRaises(ValueError):review_original_archive(p)
 def test_high_compression_ratio_rejected_before_crc_expansion(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"bomb.zip"
   body=b"0"*(1024*1024)
   m={"publisher_post":"https://www.ice.go.kr/ice/post",
      "source_entries":[{"name":"science.pdf","bytes":len(body),
                         "sha256":hashlib.sha256(body).hexdigest(),"official_url":URL}]}
   with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr("science.pdf",body)
    z.writestr("SOURCE_MANIFEST.json",json.dumps(m))
   with self.assertRaisesRegex(ValueError,"ARCHIVE_PREFLIGHT_RESOURCE_OR_ENTRY_INVALID"):
    review_original_archive(p)

 def test_oversize_manifest_is_preflight_hold(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"large-manifest.zip"
   with zipfile.ZipFile(p,"w") as z:
    z.writestr(NAME,DATA)
    z.writestr("SOURCE_MANIFEST.json"," "* (257*1024))
   with self.assertRaisesRegex(ValueError,"ARCHIVE_PREFLIGHT_RESOURCE_OR_ENTRY_INVALID"):
    review_original_archive(p)

if __name__=="__main__":unittest.main()
