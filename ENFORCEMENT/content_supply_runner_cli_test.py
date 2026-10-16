import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

RUNNER=Path(__file__).with_name('content_supply_runner.py')
APP=Path(__file__).resolve().parents[2] / "Play Camp"
class RunnerCliTest(unittest.TestCase):
    @unittest.skipUnless((APP/'src/data/supplyCandidate.ts').is_file(),'app unavailable')
    def test_immutable_receipt_and_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/'source.txt'
            src.write_text('한글 자음 모음 학습',encoding='utf-8')
            sha=hashlib.sha256(src.read_bytes()).hexdigest()
            paths={'contract':root/'contract.json','index':root/'index.json','manifest':root/'manifest.json'}
            paths['contract'].write_text(json.dumps({'demand_id':'D','consumer':'PLAY_CAMP','requirements':[{'id':'R','query':'한글 자음'}]},ensure_ascii=False),encoding='utf-8')
            paths['index'].write_text(json.dumps({'records':[{'source_id':'SRC','title':'한글 자음 모음 학습'}]},ensure_ascii=False),encoding='utf-8')
            paths['manifest'].write_text(json.dumps({'SRC':{'source_id':'SRC','raw_path':'source.txt','sha256':sha}}),encoding='utf-8')
            cmd=[sys.executable,str(RUNNER)]
            for name,path in paths.items():
                cmd.extend(['--'+name,str(path)])
            cmd += ['--raw-root',str(root),'--output',str(root/'artifact.json'),'--app-root',str(APP),'--receipt-out',str(root/'receipt.json')]
            first=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=20)
            self.assertEqual(first.returncode,0,first.stderr+first.stdout)
            receipt=(root/'receipt.json').read_bytes()
            self.assertEqual(json.loads(receipt)['supply']['status'],'LOCAL_E2E_PASS')
            second=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=20)
            self.assertEqual(second.returncode,2)
            self.assertEqual((root/'receipt.json').read_bytes(),receipt)
if __name__=='__main__':unittest.main()
