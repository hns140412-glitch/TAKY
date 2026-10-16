import unittest
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from content_supply_index_bridge import inspect
from ai_reference_projection import build_verified_user_review_index

class IndexBridgeTest(unittest.TestCase):
    def task(self, query='교육'):
        return {'demand_id':'d','consumer':'PLAY_CAMP','requirements':[{'id':'r','query':query}]}
    @patch('content_supply_index_bridge.search')
    @patch('content_supply_index_bridge.load_index')
    def test_candidates_not_supply(self, load, search):
        load.return_value=[]
        search.return_value={'results':[{'source_id':'S1'}]}
        result=inspect(self.task(),'unused.json')
        self.assertEqual(result['inventory'][0]['candidates'],['S1'])
        self.assertEqual(result['status'],'HOLD')
        self.assertFalse(result['raw_verified'])
        self.assertFalse(result['production_invoked'])
    @patch('content_supply_index_bridge.load_index')
    def test_missing_index(self, load):
        load.side_effect=FileNotFoundError()
        result=inspect(self.task(),'missing.json')
        self.assertEqual(result['index_error'],'FileNotFoundError')
        self.assertEqual(result['status'],'HOLD')
    @patch('content_supply_index_bridge.load_index')
    def test_query_missing(self, load):
        load.return_value=[]
        result=inspect(self.task(''),'unused.json')
        self.assertEqual(result['inventory'][0]['state'],'QUERY_REQUIRED')
    def test_verified_review_raw_joins_existing_forming_router(self):
        with tempfile.TemporaryDirectory(prefix='taky-review-content-') as tmp:
            root=Path(tmp)
            intake=root/'direction_intake'/'review-test'
            intake.mkdir(parents=True)
            raw=intake/'response.bin'
            raw.write_bytes(b"# source only, not validated feature instructions\\n")
            digest=hashlib.sha256(raw.read_bytes()).hexdigest()
            payload={"defects":[],"items":[{
                "role":"USER_REVIEW_RAW",
                "source_id":"USER_REVIEW:playwright-tested",
                "source_url":"https://raw.githubusercontent.com/microsoft/playwright-mcp/main/README.md",
                "raw_path":str(raw), "sha256":digest,
                "raw_rechecked_now":True, "raw_exists":True,
            }]}
            src=root/'universe.json'
            src.write_text(json.dumps(payload),encoding='utf-8')
            index=root/'ai-index.json'
            index.write_text(json.dumps(build_verified_user_review_index(src)),encoding='utf-8')
            contract={'demand_id':'UI-REF-TEST','consumer':'TAKY',
                      'requirements':[{'id':'visual-test-reference','query':'playwright',
                                       'gap_cause':'KNOWLEDGE_NOT_FORMED'}]}
            with patch('content_supply_index_bridge.REVIEW_RAW_ROOT',root/'direction_intake'):
                got=inspect(contract,index)
                self.assertEqual(got['status'],'HOLD')
                self.assertEqual(got['inventory'][0]['candidates'],['USER_REVIEW:playwright-tested'])
                self.assertEqual(got['inventory'][0]['state'],'RAW_READY_FOR_MINING')
                self.assertEqual(got['inventory'][0]['evidence_based_next_stage'],'MINING')
                self.assertEqual(got['inventory'][0]['review_raw_receipts'][0]['raw_status'],'HASH_VERIFIED_AT_LOOKUP')
                self.assertEqual(got['actions'][0]['route'],'FORMING')  # original demand preserved
                self.assertFalse(got['production_invoked'])
                self.assertFalse(got['release_approved'])
                raw.write_bytes(b'changed after candidate indexing')
                failed=inspect(contract,index)
                self.assertEqual(failed['inventory'][0]['state'],'RAW_RECHECK_REQUIRED')
                self.assertEqual(failed['inventory'][0]['evidence_based_next_stage'],'GATHERING')
                self.assertEqual(failed['inventory'][0]['review_raw_receipts'][0]['raw_status'],'HASH_CHANGED')

    @patch('content_supply_index_bridge._review_raw_receipt')
    @patch('content_supply_index_bridge.search')
    @patch('content_supply_index_bridge.load_index')
    def test_mixed_valid_and_corrupt_review_sources_hold_gathering(self, load, search, receipt):
        load.return_value=[{'source_id':'USER_REVIEW:good'},{'source_id':'USER_REVIEW:bad'}]
        search.return_value={'results':[{'source_id':'USER_REVIEW:good'},{'source_id':'USER_REVIEW:bad'}]}
        def f(record):
            return {'raw_status':'HASH_VERIFIED_AT_LOOKUP' if record['source_id'].endswith('good') else 'HASH_CHANGED'}
        receipt.side_effect=f
        got=inspect(self.task('playwright'),'unused.json')
        self.assertEqual(got['inventory'][0]['state'],'RAW_RECHECK_REQUIRED')
        self.assertEqual(got['inventory'][0]['evidence_based_next_stage'],'GATHERING')

    @patch('content_supply_index_bridge.search')
    @patch('content_supply_index_bridge.load_index')
    def test_zero_hits_not_source_absent(self, load, search):
        load.return_value=[]
        search.return_value={'results':[]}
        self.assertEqual(inspect(self.task(),'unused.json')['inventory'][0]['state'],'COVERAGE_RECHECK')

if __name__=='__main__': unittest.main()
