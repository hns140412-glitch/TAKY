#!/usr/bin/env python3
"""No external credentials, no public network, no repository mutation."""
import json
import tempfile
import unittest
from pathlib import Path
from source_vault_handoff_bridge import build_receipt, InputError, safe_url, source_kind, candidate_url

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

    def test_normalized_url_fallback_v22(self):
        with tempfile.TemporaryDirectory() as tmp:
            x=self.sample(); x['url']=''; x['normalized_url']='https://example.org/a?utm_campaign=one&logNo=123'
            self.write(tmp,[x])
            r=build_receipt(Path(tmp))
            self.assertEqual(r['routes'][0]['kind'],'PUBLIC_URL_CANDIDATE')
            self.assertEqual(r['routes'][0]['source_url'],'https://example.org/a?logNo=123')

    def test_conflict_blocks_auto_external_acquisition(self):
        row={'url_conflict':True,'url':'https://example.org/a',
             'normalized_url':'https://example.org/b'}
        self.assertEqual(candidate_url(row),'')
        self.assertEqual(source_kind(row),'HOLD_URL_CONFLICT')

    def test_unflagged_material_url_conflict_holds(self):
        row = self.sample()
        row['normalized_url'] = 'https://example.org/another'
        # Even if an old collector forgot its explicit conflict flag, no URL is chosen.
        self.assertNotIn('url_conflict', row)
        self.assertEqual(candidate_url(row), '')
        self.assertEqual(source_kind(row), 'HOLD_URL_CONFLICT')
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, [row])
            receipt = build_receipt(Path(tmp))
            self.assertEqual(receipt['route_counts'], {'HOLD_URL_CONFLICT': 1})
            self.assertIsNone(receipt['routes'][0]['source_url'])

    def test_sanitized_equivalent_url_does_not_false_conflict(self):
        row = self.sample()
        row['normalized_url'] = 'https://example.org/a?logNo=123'
        self.assertEqual(candidate_url(row), 'https://example.org/a?logNo=123')
        row['url'] = 'https://example.org/a?logNo=123&x=ok'
        row['normalized_url'] = 'https://example.org/a?x=ok&logNo=123'
        self.assertEqual(source_kind(row), 'PUBLIC_URL_CANDIDATE')

    def test_summary_live_total_mismatch_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, [self.sample()])
            (Path(tmp)/'INCREMENTAL_SUMMARY.json').write_text(
                json.dumps({'queue_count': 1, 'notion_total': 2}), encoding='utf8')
            with self.assertRaisesRegex(InputError, 'SUMMARY_NOTION_TOTAL_MISMATCH'):
                build_receipt(Path(tmp))

    def test_body_links_are_review_only(self):
        row={'url':'', 'block_link_candidates':[{'url':'https://example.org/somewhere'}]}
        self.assertEqual(source_kind(row),'REVIEW_BODY_LINK_CANDIDATES')
        self.assertEqual(candidate_url(row),'')

    def test_secret_query_never_enters_router_receipt(self):
        got=safe_url('https://example.org/a?x-amz-signature=secret&api_key=hidden&mcp_token=private&logNo=123')
        self.assertEqual(got,'https://example.org/a?logNo=123')

    def test_actual_v22_attachment_node(self):
        row={'url':'','record_type':'ATTACHMENT_ONLY',
             'material_nodes':[{'kind':'NOTION_ATTACHMENT','block_id':'b1'}]}
        self.assertEqual(source_kind(row),'NOTION_ATTACHMENT_ACQUISITION')

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
