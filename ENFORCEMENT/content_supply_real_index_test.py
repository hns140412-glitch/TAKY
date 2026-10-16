import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from content_supply_e2e_slice import run_slice, local_consumer

class RealIndexE2E(unittest.TestCase):
    def test_real_index_parser_and_search(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=root/'original.txt'
            raw.write_text('한글 자음과 모음의 결합 원리',encoding='utf-8')
            sha=hashlib.sha256(raw.read_bytes()).hexdigest()
            idx=root/'index.json'
            idx.write_text(json.dumps({'records':[{'source_id':'SRC1','title':'한글 자음과 모음의 결합 원리','short_summary':'한글 자음 모음 교육자료'}]},ensure_ascii=False),encoding='utf-8')
            contract={'demand_id':'D','consumer':'PLAY_CAMP','requirements':[{'id':'R','query':'한글 자음'}]}
            manifest={'SRC1':{'source_id':'SRC1','raw_path':'original.txt','sha256':sha}}
            result=run_slice(contract,idx,manifest,root,root/'artifact.json',local_consumer)
            self.assertEqual(result['status'],'LOCAL_E2E_PASS',result)
            self.assertEqual(result['unit_count'],1)
            self.assertFalse(result['release_approved'])

if __name__=='__main__':unittest.main()
