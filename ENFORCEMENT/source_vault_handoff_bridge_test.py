#!/usr/bin/env python3
"""No external credentials, no public network, no repository mutation."""
import json
import tempfile
import unittest
from pathlib import Path
from source_vault_handoff_bridge import build_receipt, InputError, safe_url, source_kind

class SourceVaultBridgeTest(unittest.TestCase):
    def write(self, directory, items):
        p = Path(directory)
        (p/'INCREMENTAL_QUEUE.json').write_text(json.dumps(items), encoding='utf8')
        (p/'MINING_INBOX_HANDOFF.json').write_text(json.dumps({'items': items}), encoding='utf8')
        (p/'INCREMENTAL_SUMMARY.json').write_text(json.dumps({'queue_count': len(items)}), encoding='utf8')

    def sample(self, i='id-1'):
        return {'notion_page_id':i,'mining_status':'PENDING_NOT_PROMOTED','url':'https://example.org/a?fbclid=abc&logNo=123', 'block_snapshot_folder':r'D:\vault\snapshots\abc123'}

    def test_router_actual_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            x=self.sample(); self.write(tmp,[x]); before=(Path(tmp)/'INCREMENTAL_QUEUE.json').read_bytes()
            r=build_receipt(Path(tmp))
            self.assertEqual(r['route_counts'],{'PUBLIC_URL_CANDIDATE':1})
            self.assertEqual(r['routes'][0]['source_url'],'https://example.org/a?logNo=123')
            self.assertTrue(r['central_router_executed'])
            self.assertFalse(r['semantic_mining_executed'])
            self.assertFalse(r['queue_acknowledged'])
            self.assertEqual((Path(tmp)/'INCREMENTAL_QUEUE.json').read_bytes(),before)

    def test_no_url_material_types(self):
        self.assertEqual(source_kind({'record_type':'ATTACHMENT_ONLY'}),'NOTION_ATTACHMENT_ACQUISITION')
        self.assertEqual(source_kind({'record_type':'NOTION_CONTAINER'}),'NOTION_CHILD_DISCOVERY')
        self.assertEqual(source_kind({'url_conflict':True,'url':'https://example.org'}),'HOLD_URL_CONFLICT')

    def test_bad_urls(self):
        for u in ('file:///C:/secret','http://user:password@example.org','javascript:alert(1)'):
            self.assertEqual(safe_url(u),'')

    def test_fail_closed_missing_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'INCREMENTAL_QUEUE.json').write_text('[]')
            with self.assertRaises(InputError): build_receipt(Path(tmp))

    def test_fail_closed_duplicated_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp,[self.sample(),self.sample()])
            with self.assertRaises(InputError): build_receipt(Path(tmp))

    def test_fail_closed_ack(self):
        with tempfile.TemporaryDirectory() as tmp:
            x=self.sample();x['mining_status']='ANALYZED';self.write(tmp,[x])
            with self.assertRaises(InputError): build_receipt(Path(tmp))

    def test_fail_closed_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp,[self.sample()]);(Path(tmp)/'MINING_INBOX_HANDOFF.json').write_text(json.dumps({'items':[]}))
            with self.assertRaises(InputError): build_receipt(Path(tmp))

if __name__=='__main__': unittest.main()
