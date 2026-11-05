#!/usr/bin/env python3
"""Focused tests: no native chat ID may be fabricated from October relay/receipts."""
import json
import tempfile
import unittest
from pathlib import Path
import TAKY_OCTOBER_CONVERSATION_EVIDENCE as m

class EvidenceTests(unittest.TestCase):
    def test_relay_duplicate_seq_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"relay.md"
            p.write_text("# log\n## seq 3 · A\n- ts: 2026-10-04T00:00:00+09:00\n- task_id: TAKY-SHARED-CHAT\n- body: 공용 로그로 대화 연속\n\n## seq 3 · B\n- ts: 2026-10-05T00:00:00+09:00\n- task_id: TAKY-NOTION-COLLECTOR\n- body: 노션 수집기\n",encoding="utf-8")
            rows=m.parse_relay(p)
            self.assertEqual(len(rows),2)
            self.assertNotEqual(rows[0]["record_id"],rows[1]["record_id"])
            self.assertEqual([v["reported_seq"] for v in rows],[3,3])
            self.assertTrue(all(v["native_chat_id"] is None for v in rows))
            self.assertTrue(all(v["is_chat_message"] is False for v in rows))
    def test_duplicate_event_id_different_occurrences_do_not_merge(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"relay.md"
            p.write_text("## seq 3 · ID\n- task_id: A\n\n## seq 3 · ID\n- task_id: B\n",encoding="utf-8")
            a=m.parse_relay(p)
            self.assertEqual(len({v["record_id"] for v in a}),2)
    def test_receipt_source_scope(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t)
            (folder/"TAKY_CHAT_ORCH_alpha.json").write_text(json.dumps({"schema":"TAKY_CHAT_ORCH_V1","id":"alpha","started_utc":"2026-10-15T10:00:00Z","action":"Dispatch","status":"COMPLETE_UNVERIFIED","work_id":"TAKY-CHAT-"+"a"*32}),encoding="utf-8")
            (folder/"TAKY_CHAT_ORCH_old.json").write_text(json.dumps({"schema":"TAKY_CHAT_ORCH_V1","id":"old","started_utc":"2026-09-28T10:00:00Z"}),encoding="utf-8")
            rows=m.parse_receipts(folder)
            self.assertEqual(len(rows),1)
            self.assertFalse(rows[0]["execution_verified"])
            self.assertIsNone(rows[0]["native_chat_id"])
            self.assertEqual(rows[0]["work_id_evidence"],"EXPLICIT_WORK_ID")
    def test_wrong_work_id_kept_unmatched(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t)
            (folder/"TAKY_CHAT_ORCH_bad.json").write_text(json.dumps({"schema":"TAKY_CHAT_ORCH_V1","id":"bad","started_utc":"2026-10-17T10:00:00Z","work_id":"OTHER-99"}),encoding="utf-8")
            self.assertEqual(m.parse_receipts(folder)[0]["work_id_evidence"],"NON_CANONICAL_WORK_ID")
    def test_missing_log_fails(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            with self.assertRaisesRegex(FileNotFoundError,"OCTOBER_RELAY_LOG_NOT_CAPTURED"):
                m.main(log=p/"missing.md",history=p,assign=p/"assign.json",output=p/"out.json")
    def test_independent_topic_keys(self):
        k=m.topics_for("SAVEY 계정 및 PLAY-CAMP 수련 캠프")
        self.assertTrue(any(v["project"]=="SAVEY" for v in k))
        self.assertTrue(any(v["project"]=="PLAY-CAMP" for v in k))
        self.assertFalse(any(v["classification"]!="KEYWORD_CANDIDATE_NOT_SEMANTIC_DECISION" for v in k))
    def test_readback_idempotent_and_distinct_sources(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);logs=root/"log.md";logs.write_text("## seq 1 · R1\n- ts: 2026-10-04T10:00:00+09:00\n- task_id: TAKY-NOTION-COLLECTOR\n",encoding="utf-8")
            hist=root/"hist";hist.mkdir()
            (hist/"TAKY_CHAT_ORCH_1.json").write_text(json.dumps({"schema":"TAKY_CHAT_ORCH_V1","id":"1","started_utc":"2026-10-15T10:00:00Z","action":"Dispatch","work_id":"TAKY-CHAT-"+"a"*32}),encoding="utf-8")
            ass=root/"assign.json";ass.write_text(json.dumps({"tasks":[{"work_id":"TAKY-CHAT-"+"a"*32}]}),encoding="utf-8")
            output=root/"out.json"
            one=m.main(log=logs,history=hist,assign=ass,output=output)
            two=m.main(log=logs,history=hist,assign=ass,output=output)
            self.assertTrue(one["changed"]);self.assertFalse(two["changed"])
            obj=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(obj["work_ids_exact_matched_assignment_registry"],1)
            self.assertEqual(obj["native_chat_transcripts_ingested"],0)
            self.assertFalse(obj["account_wide_chat_coverage_verified"])
            self.assertTrue(all(x["native_chat_id"] is None for x in obj["records"]))
if __name__=="__main__":unittest.main()
