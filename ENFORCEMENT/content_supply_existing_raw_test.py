"""Read-only existing TAKY RAW corpus -> real index search -> Play Camp parser test."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from content_supply_runner import execute

ROOT=Path(r"D:\Git PWA\TAKY")
APP=Path(__file__).resolve().parents[2] / "Play Camp"
REL="LEARNING/data/official-snapshots/standard-object-2022-elementary-v1.json"

class ExistingRawE2E(unittest.TestCase):
    @unittest.skipUnless((ROOT/REL).is_file() and (APP/"src/data/supplyCandidate.ts").is_file(), "corpus/app unavailable")
    def test_real_corpus_is_candidate_only(self):
        source=ROOT/REL
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        sid="TAKY:official-snapshots/standard-object-2022-elementary-v1.json"
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d)
            index=temp/"index.json"
            index.write_text(json.dumps({"records":[{
                "source_id":sid,
                "title":"2022 개정 초등학교 성취기준 표준 객체",
                "short_summary":"2022 개정 초등 성취기준 공식 정합성 참고"
            }]},ensure_ascii=False),encoding="utf-8")
            demand={"demand_id":"LOCAL-RAW-READBACK",
                    "consumer":"PLAY_CAMP",
                    "requirements":[{"id":"CURRICULUM-ALIGN","query":"2022 개정 초등 성취기준"}]}
            manifest={sid:{"source_id":sid,"raw_path":REL,"sha256":before}}
            result=execute(demand,index=index,manifest=manifest,raw_root=ROOT,
                           output=temp/"candidate.json",app_root=APP)
            self.assertEqual(result["supply"]["status"],"LOCAL_E2E_PASS",result)
            package=json.loads((temp/"candidate.json").read_text(encoding="utf-8"))
            self.assertEqual(package["units"][0]["raw_sha256"],before)
            self.assertEqual(package["forming"]["approval_status"],"NOT_APPROVED")
            self.assertEqual(result["supply"]["receipt"]["status"],"APP_CANDIDATE_PARSED")
            self.assertFalse(result["app_runtime_bound"])
            self.assertFalse(result["release_approved"])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
if __name__=="__main__":unittest.main()
