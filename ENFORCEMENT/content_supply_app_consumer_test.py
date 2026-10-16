import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from content_supply_app_consumer import consume_playcamp_candidate

APP = Path(__file__).resolve().parents[2] / "Play Camp"
class PlayCampCandidateAdapterTest(unittest.TestCase):
    def candidate(self):
        return {"schema":"TAKY_SUPPLY_SLICE_V1","demand_id":"D1","consumer":"PLAY_CAMP",
                "units":[{"requirement_id":"R1","source_id":"SRC","raw_sha256":"b"*64,
                          "source_excerpt":"소리와 글자를 연결하는 원문"}],"generated_content":False}
    @unittest.skipUnless((APP/"src"/"data"/"supplyCandidate.ts").is_file(), "app unavailable")
    def test_app_parser_receipt_matches_exact_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"candidate.json"
            p.write_text(json.dumps(self.candidate(),ensure_ascii=False),encoding="utf-8")
            receipt=consume_playcamp_candidate(p, APP)
            self.assertEqual(receipt["status"],"APP_CANDIDATE_PARSED",receipt)
            self.assertEqual(receipt["artifact_sha256"],hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(receipt["requirement_ids"],["R1"])
            self.assertFalse(receipt["canEmitLearningEvidence"])
    @unittest.skipUnless((APP/"src"/"data"/"supplyCandidate.ts").is_file(), "app unavailable")
    def test_reject_invalid_consumer(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"candidate.json"
            data=self.candidate()
            data["consumer"]="HIDE"
            p.write_text(json.dumps(data),encoding="utf-8")
            self.assertEqual(consume_playcamp_candidate(p,APP)["status"],"APP_CANDIDATE_REJECTED")
    def test_missing_artifact(self):
        self.assertEqual(consume_playcamp_candidate("missing.json",APP)["status"],"INPUT_UNAVAILABLE")
if __name__ == "__main__": unittest.main()
