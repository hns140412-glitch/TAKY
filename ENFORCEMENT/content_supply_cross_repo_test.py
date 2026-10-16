"""Cross-repo TAKY Python producer -> Play Camp TypeScript consumer test."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from content_supply_e2e_slice import run_slice, local_consumer

APP=Path(__file__).resolve().parents[2] / "Play Camp"
ADAPTER = APP / "src" / "data" / "supplyCandidate.ts"

class CrossRepoConsumer(unittest.TestCase):
    @unittest.skipUnless(ADAPTER.is_file(), "Play Camp source not available")
    def test_real_generated_artifact_consumed_by_app_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = root / "source.txt"
            raw.write_text("한글 자음과 모음을 비교하는 자료",encoding="utf-8")
            sha = hashlib.sha256(raw.read_bytes()).hexdigest()
            (root / "index.json").write_text(json.dumps({"records":[{"source_id":"SRC","title":"한글 자음과 모음 비교 자료"}]},ensure_ascii=False),encoding="utf-8")
            contract={"demand_id":"D1","consumer":"PLAY_CAMP","requirements":[{"id":"R1","query":"한글 자음"}]}
            manifest={"SRC":{"source_id":"SRC","raw_path":"source.txt","sha256":sha}}
            output=root/"candidate.json"
            result=run_slice(contract,root/"index.json",manifest,root,output,local_consumer)
            self.assertEqual(result["status"],"LOCAL_E2E_PASS",result)
            script="import {readFileSync} from 'node:fs'; const m=await import(process.argv[1]); console.log(JSON.stringify(m.inspectSupplyCandidate(JSON.parse(readFileSync(process.argv[2],'utf8')))));"
            cp=subprocess.run(["node","--input-type=module","-e",script,ADAPTER.as_uri(),str(output)],cwd=APP,capture_output=True,text=True,encoding="utf-8",timeout=20)
            self.assertEqual(cp.returncode,0,cp.stderr)
            verdict=json.loads(cp.stdout)
            self.assertEqual(verdict["status"],"CANDIDATE_NOT_AUTHORIZED")
            self.assertEqual(verdict["sourceIds"],["SRC"])
            self.assertFalse(verdict["canRegisterActivity"])
            self.assertFalse(verdict["canEmitLearningEvidence"])

if __name__ == "__main__": unittest.main()
