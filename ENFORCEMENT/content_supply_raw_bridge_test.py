import hashlib
import tempfile
import unittest
from pathlib import Path
from content_supply_raw_bridge import verify_raw_candidates

class RawBridgeTest(unittest.TestCase):
    def test_verified_bytes_remain_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "source.txt"
            p.write_bytes(b"source body")
            manifest = {"s1": {"source_id":"s1","raw_path":"source.txt","sha256":hashlib.sha256(p.read_bytes()).hexdigest()}}
            out = verify_raw_candidates([{"id":"r1","candidates":["s1"]}],root=d,manifest=manifest)
            self.assertEqual(out["items"][0]["raw_candidates"][0]["state"],"RAW_HASH_MATCH_CANDIDATE")
            self.assertEqual(out["status"],"HOLD")
            self.assertFalse(out["content_sufficient"])
    def test_missing_provenance(self):
        out=verify_raw_candidates([{"id":"r","candidates":["x"]}],root=".",manifest={})
        self.assertEqual(out["items"][0]["raw_candidates"][0]["state"],"PROVENANCE_MISSING")
    def test_outside_root(self):
        with tempfile.TemporaryDirectory() as d:
            evidence={"source_id":"x","raw_path":"../outside.txt","sha256":"a"*64}
            out=verify_raw_candidates([{"id":"r","candidates":["x"]}],root=d,manifest={"x":evidence})
            self.assertNotEqual(out["items"][0]["raw_candidates"][0]["state"],"RAW_HASH_MATCH_CANDIDATE")
    def test_wrong_hash(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/"s.txt").write_text("actual")
            out=verify_raw_candidates([{"id":"r","candidates":["x"]}],root=d,manifest={"x":{"source_id":"x","raw_path":"s.txt","sha256":"a"*64}})
            self.assertEqual(out["items"][0]["raw_candidates"][0]["state"],"RAW_HASH_MISMATCH")
    def test_invalid_manifest(self):
        self.assertEqual(verify_raw_candidates([],root=".",manifest=None)["reason"],"INPUT_INVALID")

if __name__=="__main__": unittest.main()
