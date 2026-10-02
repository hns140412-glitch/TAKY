import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from architecture_source_probe import run, source_handoff

HERE = Path(__file__).parent
BASE = json.loads((HERE/'architecture_growth_backlog.json').read_text(encoding='utf-8'))
ROOT = HERE.parent
ENGINE = ROOT/'ENFORCEMENT'/'data_index_search.py'

class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.engine = ENGINE if ENGINE.is_file() else Path(self.tmp.name)/'index_engine_fixture.py'
        if not ENGINE.is_file():
            self.engine.write_text('''import json\nfrom pathlib import Path\ndef load_index(p): return json.loads(p.read_text(encoding="utf-8"))["sources"]\ndef search(rows, query, filters=None, limit=5, relation_depth=1):\n return {"semantic_mode":"FIXTURE_LEXICAL_ONLY","candidate_count":len(rows),"results":[{"source_id":r["source_id"],"title":r["title"],"authority_class":r["authority_level"],"source_ref":{"source_id":r["source_id"]},"provenance":{"origin_locator":r["origin_locator"]}} for r in rows[:limit]]}\n''', encoding='utf-8')
        self.file=Path(self.tmp.name)/'source_index.json'
        self.file.write_text(json.dumps({'sources':[{'source_id':'test-source-1','title':'official parcel source and land use',
            'source_family':'REFERENCE','authority_level':'OFFICIAL','origin_locator':'fixture://not-real'}]}),encoding='utf-8')
    def test_requires_existing_index(self):
        with self.assertRaises(FileNotFoundError):run(BASE, Path(self.tmp.name)/'missing', self.engine)
    def test_real_search_engine_candidates_not_receipts(self):
        res=run(BASE,self.file,self.engine)
        self.assertFalse(res['index_receipt_generated'])
        self.assertFalse(res['mining_invoked'])
        self.assertFalse(res['source_or_current_mutated'])
        self.assertEqual(len([x for x in res['results'] if x['state']=='HOLD_PRESERVED']),3)
        self.assertTrue(res['snapshot']['index_payload_sha256'])
        self.assertEqual(res['results'][0]['state'],'INDEX_OWNER_SUITABILITY_REVIEW_REQUIRED')
        self.assertFalse(res['results'][0]['may_emit_index_result'])
    def test_v26_generic_data_path_is_not_raw_and_preserves_owner_file_id(self):
        row={'source_id':'owner-drive-file-id','source_ref':{'source_id':'owner-drive-file-id','locator':'DATA'},'provenance':{}}
        handoff=source_handoff(row)
        self.assertEqual(handoff['source_id'],'owner-drive-file-id')
        self.assertTrue(handoff['owner_resolution_required'])
        self.assertIsNone(handoff['specific_locator'])
        self.assertFalse(handoff['content_claim_allowed'])

    def test_specific_origin_locator_retained_without_claiming_fetch(self):
        h=source_handoff({'source_ref':{'source_id':'sample-id','locator':'DATA'},
                          'provenance':{'origin_locator':'owner://raw/source'}})
        self.assertEqual(h['specific_locator'],'owner://raw/source')
        self.assertFalse(h['raw_content_retrieved'])

    def test_missing_engine_fails(self):
        with self.assertRaises(FileNotFoundError):run(BASE,self.file,Path(self.tmp.name)/'fake.py')
    def test_existing_arbitrary_python_engine_rejected_before_import(self):
        impostor=Path(self.tmp.name)/'impostor.py'
        impostor.write_text("raise RuntimeError('arbitrary module execution')",encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'UNTRUSTED_INDEX_ENGINE_PATH'):
            run(BASE,self.file,impostor)

    def test_duplicate_gap_fails(self):
        sample={'schema':BASE['schema'],'gaps':[BASE['gaps'][0],BASE['gaps'][0]]}
        with self.assertRaisesRegex(ValueError,'DUPLICATE_GAP_ID'):run(sample,self.file,self.engine)

if __name__=='__main__':unittest.main()
