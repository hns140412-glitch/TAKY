#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from source_vault_external_acquisition import execute, InputError, OUTPUT

class SourceVaultExternalAcquisitionTest(unittest.TestCase):
    def setup_case(self, td, count=1, duplicate=False, hold=False):
        root=Path(td); report=root/'reports'; report.mkdir()
        q=[]
        for i in range(count):
            url=('https://example.org/a?fbclid=secret&logNo=123' if duplicate else f'https://example.org/{i}')
            q.append({'notion_page_id':f'id-{i}', 'mining_status':'PENDING_NOT_PROMOTED',
                      'block_status':'OK', 'url':url, 'url_conflict': hold and i==0})
        for name, data in (('INCREMENTAL_QUEUE.json',q),('MINING_INBOX_HANDOFF.json',{'items':q}),
                           ('INCREMENTAL_SUMMARY.json',{'queue_count':len(q)})):
            (report/name).write_text(json.dumps(data),encoding='utf8')
        return root,report

    def fake(self):
        calls=[]
        def fn(url, *, destination_dir, max_bytes, timeout_seconds, max_redirects):
            calls.append(url)
            destination_dir.mkdir(parents=True,exist_ok=True)
            b=b'<html>controlled offline fixture</html>'
            p=destination_dir/'fixture.html'; p.write_bytes(b)
            return {'pass':True,'acquisition_state':'ACQUIRED_AND_PRESERVED',
                    'preserved_path':str(p),'sha256':hashlib.sha256(b).hexdigest(),
                    'content_type':'text/html'}
        return calls,fn

    def test_dry_run_never_calls_network_or_writes_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td,count=2)
            calls,fn=self.fake()
            before=(report/'INCREMENTAL_QUEUE.json').read_bytes()
            r=execute(report,root,acquire_fn=fn)
            self.assertEqual(r['run']['candidate_count'],2)
            self.assertEqual(r['run']['new_events'],0)
            self.assertEqual(calls,[])
            self.assertFalse((report/OUTPUT).exists())
            self.assertEqual((report/'INCREMENTAL_QUEUE.json').read_bytes(),before)

    def test_bounded_actual_adapter_offline_fixture_and_idempotency(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td,count=2)
            calls,fn=self.fake()
            before=(report/'INCREMENTAL_QUEUE.json').read_bytes()
            first=execute(report,root,execute_public=True,max_fetches=1,acquire_fn=fn)
            self.assertEqual(first['run']['new_files'],1)
            self.assertEqual(first['run']['deferred'],1)
            second=execute(report,root,execute_public=True,max_fetches=1,acquire_fn=fn)
            self.assertEqual(second['run']['new_files'],1)
            third=execute(report,root,execute_public=True,max_fetches=1,acquire_fn=fn)
            self.assertEqual(third['run']['new_events'],0)
            self.assertEqual(len(calls),2)
            self.assertEqual(len(third['entries']),2)
            self.assertEqual((report/'INCREMENTAL_QUEUE.json').read_bytes(),before)
            self.assertFalse(third['canonical_promotion'])
            self.assertFalse(third['queue_acknowledged'])

    def test_same_url_reuses_one_fetch_without_ack(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td,count=2,duplicate=True)
            calls,fn=self.fake()
            r=execute(report,root,execute_public=True,acquire_fn=fn)
            self.assertEqual(len(calls),1)
            self.assertEqual(r['run']['new_events'],2)
            self.assertEqual(r['run']['reused_existing'],1)
            self.assertTrue(all(e['state']=='ACQUIRED_AND_PRESERVED' for e in r['entries']))

    def test_conflict_never_auto_fetched(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td,hold=True)
            calls,fn=self.fake()
            r=execute(report,root,execute_public=True,acquire_fn=fn)
            self.assertEqual(calls,[])
            self.assertEqual(r['run']['candidate_count'],0)
            self.assertEqual(r['run']['deferred'],1)

    def test_missing_acquired_bytes_retries_not_fake_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td)
            calls,fn=self.fake()
            execute(report,root,execute_public=True,acquire_fn=fn)
            p=next((root/'data'/'notion_incremental'/'acquired_external').rglob('fixture.html'))
            p.unlink()
            result=execute(report,root,execute_public=True,acquire_fn=fn)
            self.assertEqual(len(calls),2)
            self.assertEqual(len(result['entries']),2)

    def test_nonapproved_ledger_is_not_silently_recreated(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td)
            (report/OUTPUT).write_text(json.dumps({'schema':'unknown','entries':[]}))
            with self.assertRaises(InputError):execute(report,root)

    def test_limit_enforced_before_any_network(self):
        with tempfile.TemporaryDirectory() as td:
            root,report=self.setup_case(td)
            for n in (0,4,100):
                with self.assertRaises(InputError):execute(report,root,execute_public=True,max_fetches=n)

if __name__=='__main__':unittest.main()
