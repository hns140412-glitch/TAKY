#!/usr/bin/env python3
"""Resume must not duplicate an observed external callback or silently repeat ambiguity."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mining_attempt_journal import LocalAttemptJournal
from mining_operation_runner import run_with_providers
from mining_core import normalize_goal


def task(*questions):
    return {"task_family":"GENERAL_RESEARCH","goal":"retrieve research originals",
            "unknown":list(questions or ["first source"]),"max_research_depth":"D1"}


def finding(request):
    return {"state":"SUCCESS","response":{"results":[{
        "source_id":"S-"+request["frontier_id"],
        "url":"https://publisher.example/"+request["frontier_id"],
        "source_class":"PRIMARY","claim":"Candidate source",
        "direct_support":True,"excerpt_ref":"page:1#p:1",
    }]}}


def journal(path, selected_task):
    return LocalAttemptJournal(path,goal_id=normalize_goal(selected_task)["goal_id"])


class LocalAttemptJournalTest(unittest.TestCase):
    def test_success_receipt_is_replayed_without_repeating_callback_or_budget(self):
        with tempfile.TemporaryDirectory() as td:
            t=task("A");j=journal(Path(td),t);calls=[]
            def getter(req):
                calls.append(req["request_id"]);return finding(req)
            first=run_with_providers({"task":t,"memory":{}},{"WEB":getter},
                                     journal=j,max_calls=1)
            self.assertEqual(first["invocations"],1)
            self.assertEqual(len(calls),1)
            second=run_with_providers({"task":t,"memory":{}},{"WEB":getter},
                                      journal=j,max_calls=1)
            self.assertEqual(second["invocations"],0)
            self.assertEqual(second["attempt_records"],1)
            self.assertTrue(second["events"][0]["replayed_from_local_journal"])
            self.assertEqual(len(calls),1)
            self.assertEqual(first["checkpoint"]["resume_key"],second["checkpoint"]["resume_key"])
            self.assertFalse(second["real_user_outcome_countable"])

    def test_failure_then_changed_provider_results_replay_without_new_calls(self):
        with tempfile.TemporaryDirectory() as td:
            t=task("A");j=journal(Path(td),t);calls=[]
            def web(req):
                calls.append("WEB")
                return {"state":"FAILED","error":"TIMEOUT"}
            def public(req):
                calls.append("PUBLIC_DATA")
                return finding(req)
            providers={"WEB":web,"PUBLIC_DATA":public,"GITHUB":finding}
            first=run_with_providers({"task":t,"memory":{}},providers,
                                     journal=j,max_calls=2)
            second=run_with_providers({"task":t,"memory":{}},providers,
                                      journal=j,max_calls=2)
            self.assertEqual(calls,["WEB","PUBLIC_DATA"])
            self.assertEqual(first["invocations"],2)
            self.assertEqual(second["invocations"],0)
            self.assertEqual([x["provider"] for x in second["events"]],
                             ["WEB","PUBLIC_DATA"])
            self.assertEqual(len(second["checkpoint"]["evidence"]),1)

    def test_interruption_after_durable_intent_blocks_unobservable_retry(self):
        with tempfile.TemporaryDirectory() as td:
            t=task("A");j=journal(Path(td),t);calls=[]
            def interrupted(req):
                calls.append("called")
                raise KeyboardInterrupt("simulate process interruption before receipt")
            with self.assertRaises(KeyboardInterrupt):
                run_with_providers({"task":t,"memory":{}},{"WEB":interrupted},
                                   journal=j)
            self.assertEqual(calls,["called"])
            on_disk=list(Path(td).glob("*.json"))
            self.assertEqual(len(on_disk),1)
            self.assertEqual(json.loads(on_disk[0].read_text())["state"],"INTENT")
            resumed=run_with_providers({"task":t,"memory":{}},{"WEB":interrupted},
                                       journal=j)
            self.assertEqual(calls,["called"])
            self.assertEqual(resumed["invocations"],0)
            self.assertEqual(resumed["state"],"HOLD_IN_FLIGHT_UNCERTAIN")
            self.assertEqual(resumed["plan"]["pending_actions"]["items"][0]["classification"],
                             "IN_FLIGHT_HOLD")
            self.assertFalse(resumed["operational_research_ready"])

    def test_corrupt_existing_journal_does_not_reinvoke_provider(self):
        with tempfile.TemporaryDirectory() as td:
            t=task("A");j=journal(Path(td),t)
            def interrupted(req):raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                run_with_providers({"task":t,"memory":{}},{"WEB":interrupted},
                                   journal=j)
            file=next(Path(td).glob("*.json"));file.write_text("{broken",encoding="utf-8")
            called=[]
            out=run_with_providers({"task":t,"memory":{}},
                                   {"WEB":lambda req:called.append(req) or finding(req)},
                                   journal=j)
            self.assertEqual(called,[])
            self.assertEqual(out["state"],"HOLD_IN_FLIGHT_UNCERTAIN")
            self.assertEqual(out["events"][0]["error"],"CORRUPT_ATTEMPT_JOURNAL")

    def test_cached_acquired_source_must_still_exist_and_match_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            t=task("A");j=journal(Path(td)/"journal",t)
            original=Path(td)/"original.pdf";data=b"%PDF-1.7\n%%EOF"
            original.write_bytes(data)
            calls=[]
            def getter(req):
                calls.append(req["request_id"])
                return {**finding(req),"source_acquisition":{
                    "state":"ACQUIRED_AND_PRESERVED","preserved_path":str(original),
                    "size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
                    "final_url":"https://publisher.example/original.pdf",
                    "canonical_promotion":False,
                }}
            first=run_with_providers({"task":t,"memory":{}},{"WEB":getter},
                                     journal=j)
            self.assertEqual(first["source_files_preserved"],1)
            second=run_with_providers({"task":t,"memory":{}},{"WEB":getter},
                                      journal=j)
            self.assertEqual(second["invocations"],0)
            self.assertEqual(second["source_files_preserved"],1)
            original.write_bytes(b"changed")
            third=run_with_providers({"task":t,"memory":{}},{"WEB":getter},
                                     journal=j)
            self.assertEqual(third["state"],"HOLD_IN_FLIGHT_UNCERTAIN")
            self.assertEqual(third["events"][0]["error"],"SOURCE_RECEIPT_STALE")
            self.assertEqual(len(calls),1)

    def test_mismatched_goal_cannot_replay_same_request_id(self):
        with tempfile.TemporaryDirectory() as td:
            j=journal(Path(td),task("A"));calls=[]
            other={**task("A"),"goal":"different task"}
            out=run_with_providers({"task":other,"memory":{}},
                                   {"WEB":lambda req:calls.append(req) or finding(req)},
                                   journal=j)
            self.assertEqual(out["state"],"HOLD_RUN_STATE")
            self.assertEqual(out["reason"],"JOURNAL_GOAL_MISMATCH")
            self.assertEqual(calls,[])

    def test_receipt_allowlist_excludes_auth_and_raw_source_content(self):
        with tempfile.TemporaryDirectory() as td:
            t=task("A");j=journal(Path(td),t)
            def leaked(req):
                response=finding(req)
                response["api_key"]="TOP-SECRET-PROVIDER-KEY"
                response["response"]["results"][0]["raw_content"]="CONFIDENTIAL-BODY"
                return response
            run_with_providers({"task":t,"memory":{}},{"WEB":leaked},journal=j)
            raw=next(Path(td).glob("*.json")).read_text(encoding="utf-8")
            self.assertNotIn("TOP-SECRET-PROVIDER-KEY",raw)
            self.assertNotIn("CONFIDENTIAL-BODY",raw)
            self.assertIn("RECEIPT",raw)


if __name__=="__main__":unittest.main()
