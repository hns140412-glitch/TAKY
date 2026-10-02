#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from source_vault_snapshot_evidence import build_snapshot_receipt, _folder, _extract, InputError

class VaultSnapshotEvidenceTest(unittest.TestCase):
    def setup_case(self, root, *, with_file=True, corrupt=False, child=False):
        p=Path(root); fid='1'*64; pid='test-page-1'
        folder=p/'data'/'notion_incremental'/'snapshots'/pid/fid
        folder.mkdir(parents=True)
        block={'id':'block-1','type':'paragraph','paragraph':{'rich_text':[{'plain_text':'verified sample'}]},'has_children':False}
        if child:
            block={'id':'block-1','type':'child_page','child_page':{'title':'child'},'has_children':False}
        if with_file:
            (folder/'blocks.json').write_text('bad json' if corrupt else json.dumps([block]),encoding='utf8')
        q=[{'notion_page_id':pid,'mining_status':'PENDING_NOT_PROMOTED','block_status':'OK',
            'block_snapshot_folder':str(folder),'url':'https://example.org'}]
        report=p/'reports';report.mkdir()
        (report/'INCREMENTAL_QUEUE.json').write_text(json.dumps(q))
        (report/'MINING_INBOX_HANDOFF.json').write_text(json.dumps({'items':q}))
        (report/'INCREMENTAL_SUMMARY.json').write_text(json.dumps({'queue_count':1}))
        return p,report,q

    def test_actual_raw_snapshot_extract_without_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,_=self.setup_case(td)
            before=(report/'INCREMENTAL_QUEUE.json').read_bytes()
            receipt=build_snapshot_receipt(report,root)
            self.assertEqual(receipt['snapshot_evidence_count'],1)
            self.assertEqual(receipt['entries'][0]['state'],'NOTION_BLOCK_TEXT_EXTRACTED')
            self.assertEqual(receipt['entries'][0]['extracted'][0]['block_id'],'block-1')
            self.assertEqual(receipt['entries'][0]['extracted'][0]['text'],'verified sample')
            self.assertFalse(receipt['semantic_mining_executed'])
            self.assertFalse(receipt['canonical_promotion'])
            self.assertFalse(receipt['queue_acknowledged'])
            self.assertEqual((report/'INCREMENTAL_QUEUE.json').read_bytes(),before)

    def test_unavailable_is_hold_not_fake_acquisition(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,_=self.setup_case(td,with_file=False)
            r=build_snapshot_receipt(report,root)
            self.assertEqual(r['held_count'],1)
            self.assertEqual(r['entries'][0]['flags'],['SNAPSHOT_FILE_NOT_FOUND'])

    def test_corrupt_is_hold(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,_=self.setup_case(td,corrupt=True)
            r=build_snapshot_receipt(report,root)
            self.assertEqual(r['held_count'],1)
            self.assertIsNone(r['entries'][0]['snapshot_sha256'])

    def test_child_is_not_treated_as_full_acquisition(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,_=self.setup_case(td,child=True)
            r=build_snapshot_receipt(report,root)
            self.assertIn('CHILD_PAGE_NOT_RECURSIVELY_ACQUIRED',r['entries'][0]['flags'])
            self.assertEqual(r['text_extracted_count'],0)

    def test_claimed_folder_must_match_trusted_root(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,q=self.setup_case(td)
            q[0]['block_snapshot_folder']=str(Path(td)/'other'/'data'/'notion_incremental'/'snapshots'/'test-page-1'/('1'*64))
            with self.assertRaises(InputError): _folder(root,q[0])

    def test_table_cells_and_equation_are_preserved_at_exact_block_anchors(self):
        blocks = [{"id":"table-1","type":"table","table":{},"has_children":True,
                   "_children":[{"id":"row-1","type":"table_row",
                     "table_row":{"cells":[[{"plain_text":"첫 열"}],
                                           [{"plain_text":"둘째 열"}]]},
                     "has_children":False}]},
                  {"id":"equation-1","type":"equation",
                   "equation":{"expression":"a^2+b^2"},"has_children":False}]
        text, count, flags = _extract(blocks)
        self.assertEqual(count,3)
        self.assertEqual([x["text"] for x in text],["첫 열","둘째 열","a^2+b^2"])
        self.assertEqual([x["cell_index"] for x in text if x["field"]=="cells"],[0,1])
        self.assertEqual(text[0]["block_path"],["table-1","row-1"])
        self.assertEqual(flags,[])

    def test_image_only_and_caption_are_not_ocr_claims(self):
        blocks=[{"id":"image-1","type":"image",
                 "image":{"caption":[{"plain_text":"이미지 설명"}],
                          "file":{"url":"https://private.invalid/signed"}},
                 "has_children":False}]
        text, count, flags = _extract(blocks)
        self.assertEqual([x["text"] for x in text],["이미지 설명"])
        self.assertIn("ATTACHMENT_BYTES_NOT_ACQUIRED", flags)
        self.assertIn("IMAGE_CONTENT_NOT_OCR_EXTRACTED", flags)
        self.assertNotIn("https://private.invalid",repr(text))

    def test_child_title_is_metadata_and_unknown_type_must_hold(self):
        blocks=[{"id":"c","type":"child_page","child_page":{"title":"child name"},
                 "has_children":False},
                {"id":"future","type":"novel_notion_content","novel_notion_content":{},
                 "has_children":False}]
        text, _, flags = _extract(blocks)
        self.assertEqual(text[0]["scope"],"NOTION_CHILD_TITLE_METADATA_ONLY")
        self.assertIn("CHILD_PAGE_NOT_RECURSIVELY_ACQUIRED",flags)
        self.assertIn("UNSUPPORTED_NOTION_BLOCK_TYPE:novel_notion_content",flags)

    def test_non_list_table_cells_fail_closed(self):
        with self.assertRaisesRegex(InputError,"SNAPSHOT_TABLE_CELLS_INVALID"):
            _extract([{"id":"bad-row","type":"table_row",
                       "table_row":{"cells":"not cells"},"has_children":False}])

    def test_guard_duplicate_queue(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,q=self.setup_case(td)
            (report/'INCREMENTAL_QUEUE.json').write_text(json.dumps(q+q),encoding='utf8')
            with self.assertRaises(InputError):build_snapshot_receipt(report,root)

if __name__=='__main__':unittest.main()
