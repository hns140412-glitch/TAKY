#!/usr/bin/env python3
"""Future-source ingestion tests use synthetic exports; no account data mutated."""
from __future__ import annotations
import json
import tempfile
import unittest
import zipfile
from datetime import datetime,timezone
from pathlib import Path
import TAKY_CONVERSATION_FUTURE_SYNC as sync

def make_export():
    oct1=datetime(2026,10,18,12,tzinfo=timezone.utc).timestamp()
    sep=datetime(2026,9,30,12,tzinfo=timezone.utc).timestamp()
    return [{"id":"native-chat-test-123","current_node":"m3",
        "mapping":{
            "m1":{"parent":None,"message":{"id":"m1","author":{"role":"user"},"content":{"parts":["웹앱 설치와 관리자 인증"]},"create_time":sep}},
            "m2":{"parent":"m1","message":{"id":"m2","author":{"role":"user"},"content":{"parts":["구글드라이브 용량 및 운영 서버 관리"]},"create_time":oct1}},
            "m3":{"parent":"m2","message":{"id":"m3","author":{"role":"user"},"content":{"parts":["주제별 아이디 부여"]},"create_time":oct1+60}}
        }}]
class FutureSyncTests(unittest.TestCase):
    def prepare(self,temp):
        root=Path(temp); inbox=root/"inbox"; inbox.mkdir()
        assign=root/"assign.json";assign.write_text('{"tasks":[]}',encoding="utf-8")
        return inbox,assign,root/"out.json"
    def test_empty_inbox_reports_gap_not_success(self):
        with tempfile.TemporaryDirectory() as t:
            inbox,ass,out=self.prepare(t)
            r=sync.main(inbox,out,ass)
            self.assertEqual(r["chats_with_proven_native_id"],0)
            self.assertFalse(r["account_wide_verified"])
            self.assertEqual(r["source_files"],0)
    def test_october_and_later_filter_preserves_native(self):
        with tempfile.TemporaryDirectory() as t:
            inbox,ass,out=self.prepare(t)
            (inbox/"conversations.json").write_text(json.dumps(make_export(),ensure_ascii=False),encoding="utf-8")
            r=sync.main(inbox,out,ass)
            self.assertEqual(r["messages"],2)
            self.assertEqual(r["chats_with_proven_native_id"],1)
            self.assertEqual(r["topic_switches"],2)
            v=json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(v["chats"][0]["native_chat_ref"].startswith("chatgpt:backing:"))
            self.assertEqual(v["parsed_messages_outside_date_range"],1)
            self.assertTrue(all(x["work_ids"]==[] for x in v["chats"][0]["links"]))
            self.assertFalse(sync.main(inbox,out,ass)["changed"])
    def test_native_zip_support(self):
        with tempfile.TemporaryDirectory() as t:
            inbox,ass,out=self.prepare(t)
            with zipfile.ZipFile(inbox/"chat_export.zip","w") as z:
                z.writestr("conversations.json",json.dumps(make_export(),ensure_ascii=False))
            r=sync.main(inbox,out,ass)
            self.assertEqual(r["messages"],2)
            self.assertEqual(r["chats_with_proven_native_id"],1)
    def test_broken_export_holds_not_promotes(self):
        with tempfile.TemporaryDirectory() as t:
            inbox,ass,out=self.prepare(t)
            (inbox/"conversations.json").write_text('{"not":"a list"}',encoding="utf-8")
            r=sync.main(inbox,out,ass)
            self.assertEqual(r["source_holds"],1)
            self.assertEqual(r["chats_with_proven_native_id"],0)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["source_holds"][0]["source"],str(inbox/"conversations.json"))
    def test_zip_path_without_export_holds(self):
        with tempfile.TemporaryDirectory() as t:
            inbox,ass,out=self.prepare(t)
            with zipfile.ZipFile(inbox/"unrelated.zip","w") as z:
                z.writestr("document.txt","no transcript")
            r=sync.main(inbox,out,ass)
            self.assertEqual(r["source_holds"],1)
            self.assertEqual(r["messages"],0)
if __name__=="__main__":unittest.main()
