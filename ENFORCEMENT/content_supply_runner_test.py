import hashlib, json, tempfile, unittest
from pathlib import Path
from content_supply_runner import execute

APP=Path(__file__).resolve().parents[2] / "Play Camp"
class RunnerTest(unittest.TestCase):
    @unittest.skipUnless((APP/'src/data/supplyCandidate.ts').is_file(),'app unavailable')
    def test_full_cross_repository(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'src.txt').write_text('한글 자음 모음 학습 자료',encoding='utf-8')
            digest=hashlib.sha256((p/'src.txt').read_bytes()).hexdigest()
            (p/'index.json').write_text(json.dumps({'records':[{'source_id':'SRC','title':'한글 자음 모음 학습 자료'}]},ensure_ascii=False),encoding='utf-8')
            contract={'demand_id':'D','consumer':'PLAY_CAMP','requirements':[{'id':'R','query':'한글 자음'}]}
            manifest={'SRC':{'source_id':'SRC','raw_path':'src.txt','sha256':digest}}
            report=execute(contract,index=p/'index.json',manifest=manifest,raw_root=p,output=p/'out.json',app_root=APP)
            self.assertEqual(report['supply']['status'],'LOCAL_E2E_PASS',report)
            self.assertEqual(report['feedback']['next_stage'],'APPLICATION_INTEGRATION')
            self.assertTrue(report['raw_goal']['raw_goal_sufficient'])
            self.assertFalse(report['raw_goal']['content_goal_sufficient'])
            self.assertFalse(report['release_approved'])
            self.assertFalse(report['learning_engine_evidence_sent'])
if __name__=='__main__':unittest.main()
