import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from content_supply_e2e_slice import run_slice, local_consumer

class SupplyE2E(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.raw=self.root/'source.txt'
        self.raw.write_text('한글 글자와 소리의 대응을 관찰합니다.',encoding='utf-8')
        self.sha=hashlib.sha256(self.raw.read_bytes()).hexdigest()
        self.manifest={'s1':{'source_id':'s1','raw_path':'source.txt','sha256':self.sha}}
        self.contract={'demand_id':'D1','consumer':'PLAY_CAMP','requirements':[{'id':'R1','query':'한글'}]}
        self.out=self.root/'formed.json'
    def execute(self, consumer=local_consumer):
        with patch('content_supply_index_bridge.load_index',return_value=[]), patch('content_supply_index_bridge.search',return_value={'results':[{'source_id':'s1'}]}):
            return run_slice(self.contract,'mock-index.json',self.manifest,self.root,self.out,consumer)
    def test_full_local(self):
        result=self.execute()
        self.assertEqual(result['status'],'LOCAL_E2E_PASS')
        self.assertFalse(result['release_approved'])
        self.assertEqual(json.loads(self.out.read_text(encoding='utf-8'))['units'][0]['source_id'],'s1')
    def test_missing_raw(self):
        self.raw.unlink()
        self.assertEqual(self.execute()['stage'],'GATHERING')
        self.assertFalse(self.out.exists())
    def test_hash_tamper(self):
        self.raw.write_text('변조',encoding='utf-8')
        self.assertEqual(self.execute()['stage'],'GATHERING')
    def test_binary_raw_requires_mining_extraction(self):
        self.raw.write_bytes(bytes([255,254]))
        self.manifest['s1']['sha256']=hashlib.sha256(self.raw.read_bytes()).hexdigest()
        result=self.execute()
        self.assertEqual(result['stage'],'MINING')
        self.assertEqual(result['reason'],'TEXT_EXTRACTION_REQUIRED')
    def test_bad_consumer(self):
        self.assertEqual(self.execute(lambda path:{'artifact_sha256':'fake','requirement_ids':['R1']})['stage'],'INTEGRATION')
    def test_forged_or_duplicate_consumer_receipts(self):
        variants = ({'status':'INVALID'}, {'requirement_ids':['R1','R1']},
                    {'canRegisterActivity':True}, {'canEmitLearningEvidence':True},
                    {'consumer_adapter':'FAKE'})
        for overrides in variants:
            with self.subTest(overrides=overrides):
                result=self.execute(lambda path:{**local_consumer(path),**overrides})
                self.assertEqual(result['stage'],'INTEGRATION')
    def test_existing_output_is_preserved(self):
        self.out.write_text('protected',encoding='utf-8')
        self.assertEqual(self.execute()['stage'],'PRODUCTION')
        self.assertEqual(self.out.read_text(encoding='utf-8'),'protected')
    def test_missing_query(self):
        self.contract['requirements'][0].pop('query')
        self.assertEqual(self.execute()['stage'],'INTENT')
    def test_identical_artifact_replays_without_overwrite(self):
        first=self.execute()
        before=self.out.read_bytes()
        second=self.execute()
        self.assertEqual(first['status'],'LOCAL_E2E_PASS')
        self.assertEqual(second['status'],'LOCAL_E2E_PASS')
        self.assertTrue(second['reused_artifact'])
        self.assertEqual(before,self.out.read_bytes())
    def test_recover_after_consumer_failure(self):
        failure=self.execute(lambda path:{})
        self.assertEqual(failure['stage'],'INTEGRATION')
        success=self.execute()
        self.assertEqual(success['status'],'LOCAL_E2E_PASS')
        self.assertTrue(success['reused_artifact'])
    def test_user_review_raw_requires_body_mining_before_forming(self):
        evidence={'status':'HOLD','inventory':[{
            'id':'R1','state':'RAW_READY_FOR_MINING','candidates':['USER_REVIEW:one'],
            'evidence_based_next_stage':'MINING',
            'review_raw_receipts':[{'raw_status':'HASH_VERIFIED_AT_LOOKUP'}],
        }]}
        with patch('content_supply_e2e_slice.inspect', return_value=evidence):
            out=run_slice(self.contract,'unused-index.json',self.manifest,self.root,self.out,local_consumer)
        self.assertEqual(out['stage'],'MINING')
        self.assertEqual(out['reason'],'REVIEW_RAW_BODY_MINING_REQUIRED')
        self.assertFalse(self.out.exists())

    def test_user_review_raw_changed_requires_gathering(self):
        evidence={'status':'HOLD','inventory':[{
            'id':'R1','state':'RAW_RECHECK_REQUIRED','candidates':['USER_REVIEW:one'],
            'evidence_based_next_stage':'GATHERING',
            'review_raw_receipts':[{'raw_status':'HASH_CHANGED'}],
        }]}
        with patch('content_supply_e2e_slice.inspect', return_value=evidence):
            out=run_slice(self.contract,'unused-index.json',self.manifest,self.root,self.out,local_consumer)
        self.assertEqual(out['stage'],'GATHERING')
        self.assertEqual(out['reason'],'REVIEW_RAW_INTEGRITY_RECHECK_REQUIRED')
        self.assertFalse(self.out.exists())

    @unittest.skipUnless(
        (Path(__file__).resolve().parents[2] / "TAKY_AI_WORKBENCH"
         / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
         / "TAKY_ONE_SOURCE_FORMING_REAL_APP_20261014.json").is_file(),
        "verified historical FORMING evidence unavailable")
    def test_real_review_formed_code_capability_reaches_integration_only(self):
        folder=Path(__file__).resolve().parents[2] / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
        index=folder/"USER_REVIEW_AI_DISCOVERY_INDEX_MINED_CANDIDATE_20261014.json"
        forming=folder/"TAKY_ONE_SOURCE_FORMING_REAL_APP_20261014.json"
        self.contract={
            "demand_id":"TREND-RUNTIME-PILOT", "work_id":"TAKY-PLAYWRIGHT-SOURCE-PILOT",
            "consumer":"PLAY_CAMP",
            "requirements":[{
                "id":"PLAYWRIGHT-R1", "source_id":"USER_REVIEW:1fe7096c36a73359acf8",
                "query":"playwright", "gap_cause":"KNOWLEDGE_NOT_FORMED"
            }]
        }
        def forbidden_consumer(path):
            self.fail("App curriculum consumer must not receive technology-review evidence")
        no_forming=run_slice(self.contract,index,{},self.root,self.out,forbidden_consumer)
        self.assertEqual(no_forming["stage"],"MINING")
        self.assertFalse(self.out.exists())
        accepted=run_slice(self.contract,index,{},self.root,self.out,forbidden_consumer,
                           forming_evidence_path=forming)
        self.assertEqual(accepted["stage"],"INTEGRATION")
        self.assertEqual(accepted["status"],"HOLD")
        self.assertTrue(accepted["local_runtime_evidence_verified"])
        self.assertFalse(accepted["content_artifact_created"])
        self.assertFalse(accepted["release_approved"])
        self.assertFalse(self.out.exists())
        self.contract["work_id"]="FORGED-DIFFERENT-WORK"
        forged=run_slice(self.contract,index,{},self.root,self.out,forbidden_consumer,
                         forming_evidence_path=forming)
        self.assertEqual(forged["stage"],"FORMING")
        self.assertEqual(forged["reason"],"REVIEW_FORMING_PROOF_INVALID")
        self.assertFalse(self.out.exists())
        self.contract["work_id"]="TAKY-PLAYWRIGHT-SOURCE-PILOT"
        self.contract["consumer"]="HIDE_SEEK"
        other=run_slice(self.contract,index,{},self.root,self.out,forbidden_consumer,
                        forming_evidence_path=forming)
        self.assertEqual(other["stage"],"FORMING")
        self.assertFalse(self.out.exists())
        self.contract["consumer"]="PLAY_CAMP"
        original=json.loads(forming.read_text(encoding="utf-8"))
        from content_supply_index_bridge import _bounded_evidence_json
        import copy
        for path,value in [
            (("source","sha256"),"0"*64),
            (("source","source_url"),"https://example.invalid/other.md"),
            (("source","selected_source_line"),999999),
            (("execution","result"),"UNVERIFIED_SELF_REPORTED_PASS"),
            (("execution","run_id"),"other-run"),
            (("execution","browser_receipt_path"),"D:/not-existing-browser-receipt.json"),
            (("forming","downstream_app"),"Hide & Seek"),
        ]:
            with self.subTest(path=path):
                altered=copy.deepcopy(original)
                altered[path[0]][path[1]]=value
                def read_mutated(file,limit=2_000_000):
                    if str(file)==str(forming):
                        return altered
                    return _bounded_evidence_json(file,limit=limit)
                with patch('content_supply_index_bridge._bounded_evidence_json',side_effect=read_mutated):
                    bad=run_slice(self.contract,index,{},self.root,self.out,forbidden_consumer,
                                  forming_evidence_path=forming)
                self.assertEqual(bad["stage"],"FORMING")
                self.assertFalse(self.out.exists())

    def test_no_index_hits_routes_coverage_discovery_not_index_failure(self):
        with patch('content_supply_index_bridge.load_index',return_value=[]), patch('content_supply_index_bridge.search',return_value={'results':[]}):
            result=run_slice(self.contract,'mock-index.json',self.manifest,self.root,self.out,local_consumer)
        self.assertEqual(result['stage'],'COVERAGE_DIAGNOSIS')
        self.assertEqual(result['reason'],'INDEX_NO_MATCH_NOT_SOURCE_ABSENCE')
        self.assertFalse(self.out.exists())

if __name__=='__main__':unittest.main()
