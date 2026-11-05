#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
import TAKY_CONVERSATION_PROGRESS_BOARD as b

class ProgressBoardTests(unittest.TestCase):
    def fixture(self):
        wid="TAKY-CHAT-"+"a"*32
        bad="TAKY-CHAT-"+"b"*32
        projects={"TAKY":{"source_repo":"D:/Git PWA/TAKY","status":"IDLE","workbench_path":"10_PROJECTS/TAKY"},
                  "PLAY-CAMP":{"source_repo":"D:/Git PWA/Play Camp","status":"IDLE","workbench_path":"10_PROJECTS/PLAY-CAMP"}}
        reg={"work_id":wid,"task_id":"a"*32,"project":"D:/Git PWA/TAKY",
             "status":"BLOCKED","reviewer":"UNASSIGNED","executor":"Claude",
             "input_refs":[],"output_refs":[],"evidence_refs":[],"execution_verified":False}
        receipt={"source":"TAKY_CHAT_ORCH_V1","record_id":"ORCH-one","work_id":wid,
                 "work_id_evidence":"EXPLICIT_WORK_ID","when":"2026-10-18T10:00Z",
                 "reported_status":"PASS","action":"Dispatch","model_called":False,
                 "source_ref":"source#1"}
        outside={**receipt,"record_id":"ORCH-outside","work_id":bad}
        return {"projects":{"projects":projects},"assignments":{"tasks":[reg]},
          "september":{"archive_source_count":25,"chats":[{"chat_id":"CHAT-test",
               "titles":["Play Camp 대화"],"topics":["topic-a"],"messages":8,
               "source_urls":["https://drive.google.com/file/d/test/view"]}],
               "topics":[{"topic_id":"topic-a","project":"PLAY-CAMP","name":"Play Camp"}]},
          "october":{"account_wide_chat_coverage_verified":False,"records":[receipt,outside],
                     "log_entries":0,"execution_receipts":2,"relay_duplicate_sequence_numbers":[3]},
          "oct_native":{"account_wide_coverage_verified":False,"chats":[]}},wid,bad
    def test_no_verified_completion_from_pass(self):
        inputs,wid,bad=self.fixture()
        result=b.derive(inputs,{"TAKY":{"status":"IDLE"},"PLAY-CAMP":{"status":"IDLE"}},
                        task_titles={wid:{"title":"실제 준비 지시","prepared_state":"PREPARED_NOT_EXECUTED"}},
                        repo_metadata={"PLAY-CAMP":{"probe":"READ_ONLY_GIT_METADATA","head_date":"2026-10-15"}})
        self.assertEqual(result["counts"]["independently_verified_completion"],0)
        task=result["work_items"][0]
        self.assertEqual(task["registry_status"],"BLOCKED")
        self.assertEqual(task["latest_receipt"],"PASS")
        self.assertFalse(task["execution_verified"])
        self.assertIn("REVIEWER_UNASSIGNED",task["issues"])
        self.assertIsNone(result["projects"][0]["progress_percent"])
        self.assertEqual(result["source_scope"]["oct_native_chat_count"],0)
        self.assertEqual(result["unregistered_receipt_work_ids"],[bad])
    def test_registry_verified_claim_not_independent_completion(self):
        inp,wid,_=self.fixture()
        inp["assignments"]["tasks"][0]["execution_verified"]=True
        result=b.derive(inp,{},task_titles={wid:{"title":"원본 작업"}})
        self.assertEqual(result["counts"]["independently_verified_completion"],0)
        self.assertTrue(result["work_items"][0]["registry_verification_claim"])
        self.assertFalse(result["work_items"][0]["execution_verified"])
        self.assertIn("REGISTRY_VERIFICATION_CLAIM_REQUIRES_PROOF",result["work_items"][0]["issues"])
    def test_historical_chat_not_assigned_to_ai_work(self):
        d,wid,_=self.fixture()
        r=b.derive(d,{},task_titles={wid:{"title":"작업"}})
        play=next(p for p in r["projects"] if p["project"]=="PLAY-CAMP")
        self.assertEqual(len(play["historical_chats"]),1)
        self.assertEqual(play["work_count"],0)
        self.assertEqual(play["progress_signal"],"NO_VERIFIED_PROGRESS_SIGNAL")
        self.assertEqual(r["work_items"][0]["chat_source_link"],"NOT_PROVEN")
    def test_local_worktree_wip_is_visible_without_fabricated_progress(self):
        inputs,_,_=self.fixture()
        metadata={"PLAY-CAMP":{"probe":"READ_ONLY_GIT_METADATA",
                    "tracked_changes":4,"head_date":"2026-10-19T00:00:00Z"},
                  "TAKY":{"probe":"READ_ONLY_GIT_METADATA",
                    "tracked_changes":2,"head_date":"2026-10-19T00:00:00Z"}}
        result=b.derive(inputs,{"TAKY":{"status":"IDLE"},
                                "PLAY-CAMP":{"status":"IDLE"}},
                        repo_metadata=metadata)
        play=next(p for p in result["projects"] if p["project"]=="PLAY-CAMP")
        self.assertEqual(play["current_status"], "IDLE")
        self.assertEqual(play["progress_signal"],
                         "LOCAL_TRACKED_WIP_OBSERVED_NOT_TASK_COMPLETION")
        self.assertTrue(play["work_registration_gap"])
        self.assertTrue(play["local_activity"]["tracked_wip_observed"])
        self.assertEqual(play["local_activity"]["tracked_changed_files"],4)
        self.assertIn("LOCAL_CODE_WIP_WITHOUT_REGISTERED_AI_WORK",play["flags"])
        self.assertIsNone(play["progress_percent"])
        self.assertEqual(result["counts"]["projects_with_local_tracked_wip"],2)
        self.assertEqual(result["counts"]["projects_with_unbound_local_tracked_wip"],1)
        self.assertEqual(result["counts"]["independently_verified_completion"],0)
        self.assertTrue(any(a["type"]=="PROJECT_LOCAL_WIP_UNBOUND_TO_AI_WORK"
                            and a.get("project")=="PLAY-CAMP" for a in result["alerts"]))
        html=b.build_page(result)
        self.assertIn("로컬 코드 변경 감지",html)
        self.assertIn("로컬 변경 미연결",html)

    def test_explicit_project_current_work_id_is_visible_not_registered(self):
        inp,_,_=self.fixture()
        currents={"PLAY-CAMP":{"project":"PLAY-CAMP",
                               "status":"EVALUATION",
                               "current_work_id":"MCP-REA-20261016",
                               "result_scope":"59-slide candidate, not approved",
                               "output_refs":["D:/protected/no-access"],
                               "pending_gates":["VISUAL_APPROVAL_BY_USER"]}}
        r=b.derive(inp,currents)
        play=next(p for p in r["projects"] if p["project"]=="PLAY-CAMP")
        link=play["current_work_link"]
        self.assertEqual(link["id"],"MCP-REA-20261016")
        self.assertEqual(link["registration"],"CURRENT_DECLARED_UNREGISTERED")
        self.assertEqual(link["declared_output_count"],1)
        self.assertEqual(link["pending_gate_count"],1)
        self.assertFalse(link["outcome_verified"])
        self.assertEqual(play["work_count"],0)
        self.assertIn("CURRENT_WORK_NOT_IN_AI_ASSIGNMENTS",play["flags"])
        self.assertEqual(r["counts"]["projects_with_explicit_current_unregistered_work"],1)
        self.assertEqual(r["counts"]["independently_verified_completion"],0)
        self.assertTrue(any(x.get("work_id")=="MCP-REA-20261016" and
                            x.get("type")=="EXPLICIT_PROJECT_CURRENT_WORK_NOT_REGISTERED"
                            for x in r["alerts"]))
        page=b.build_page(r)
        self.assertIn("프로젝트 CURRENT 작업",page)
        self.assertIn("AI 작업 등록부 미연결",page)
        self.assertNotIn("D:/protected/no-access",page)
        currents["PLAY-CAMP"]["project"]="OTHER-PROJECT"
        invalid=b.derive(inp,currents)
        play2=next(p for p in invalid["projects"] if p["project"]=="PLAY-CAMP")
        self.assertIsNone(play2["current_work_link"]["id"])

    def test_cross_registry_current_id_in_portfolio_not_false_positive(self):
        inp,_,_=self.fixture()
        pf={"ids":{"PORT-1","PORT-2"},"count":2,"path":"x","sha256":"0"*64,"statuses":{}}
        currents={"PLAY-CAMP":{"project":"PLAY-CAMP","current_work_id":"PORT-1"},
                  "TAKY":{"project":"TAKY","current_work_id":"GHOST-9"}}
        r=b.derive(inp,currents,portfolio=pf)
        play=next(p for p in r["projects"] if p["project"]=="PLAY-CAMP")
        link=play["current_work_link"]
        self.assertEqual(link["registration"],"CURRENT_DECLARED_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED")
        self.assertTrue(link["portfolio_registered"])
        self.assertFalse(link["ai_assigned"])
        self.assertIn("not AI-assigned",link["registration_note"])
        self.assertFalse(link["outcome_verified"])
        self.assertEqual(play["work_count"],0)
        self.assertNotIn("CURRENT_WORK_NOT_IN_AI_ASSIGNMENTS",play["flags"])
        self.assertFalse(any(x.get("work_id")=="PORT-1" and x["type"].startswith("EXPLICIT_PROJECT_CURRENT")
                             for x in r["alerts"]))
        # Truly unregistered (absent from both) still alerts.
        self.assertTrue(any(x.get("work_id")=="GHOST-9" for x in r["alerts"]))
        c=r["counts"]
        self.assertEqual((c["portfolio_tasks"],c["ai_assignments"],c["project_current_in_portfolio"],
                          c["global_missing_current_work"],c["current_not_ai_assigned"]),(2,1,1,1,2))
        self.assertEqual(c["projects_with_explicit_current_unregistered_work"],1)
        self.assertEqual(len(r["work_items"]),1)  # portfolio rows are not turned into AI tasks
        self.assertIn("포트폴리오 등록됨",b.build_page(r))
    def test_without_portfolio_original_logic_and_unknown_annotation(self):
        inp,_,_=self.fixture()
        r=b.derive(inp,{"PLAY-CAMP":{"project":"PLAY-CAMP","current_work_id":"PORT-1"}})
        link=next(p for p in r["projects"] if p["project"]=="PLAY-CAMP")["current_work_link"]
        self.assertEqual(link["registration"],"CURRENT_DECLARED_UNREGISTERED")
        self.assertEqual(link["portfolio_registered"],"UNKNOWN")
        self.assertIsNone(r["counts"]["portfolio_tasks"])
    def test_portfolio_loader_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            with self.assertRaisesRegex(ValueError,"PORTFOLIO_REGISTRY_UNREADABLE"):
                b.load_portfolio(d/"missing.json")
            for name,text,err in (("bad.json","{not json","UNREADABLE"),
                                  ("empty.json",'{"tasks":[]}',"INVALID"),
                                  ("dup.json",'{"tasks":[{"id":"A"},{"id":"A"}]}',"INVALID_IDS"),
                                  ("noid.json",'{"tasks":[{"title":"x"}]}',"INVALID_IDS")):
                (d/name).write_text(text,encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"PORTFOLIO_REGISTRY_"+err):
                    b.load_portfolio(d/name)
            (d/"ok.json").write_text('{"tasks":[{"id":"A","status":"IMPLEMENTING"},{"id":"B"}]}',encoding="utf-8")
            ok=b.load_portfolio(d/"ok.json")
            self.assertEqual((ok["count"],ok["ids"]),(2,{"A","B"}))
            self.assertEqual(len(ok["sha256"]),64)
    def test_no_invented_scope(self):
        inp,_,_=self.fixture()
        inp["oct_native"]["account_wide_coverage_verified"]=True
        with self.assertRaisesRegex(ValueError,"INVALID_FULL_COVERAGE"):
            b.derive(inp,{})
    def test_duplicate_task_id_rejected(self):
        inp,_,_=self.fixture()
        inp["assignments"]["tasks"].append(dict(inp["assignments"]["tasks"][0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_MISSING_WORK_ID"):
            b.derive(inp,{})
    def test_html_safe_and_structured(self):
        inp,wid,_=self.fixture()
        r=b.derive(inp,{},task_titles={wid:{"title":"</script><script>alert(1)</script>"}})
        h=b.build_page(r)
        doc=BeautifulSoup(h,"html.parser")
        self.assertEqual(len(doc.select("script")),2)
        self.assertIn("\\u003c/script\\u003e",h)
        self.assertIn("TAKY_CONVERSATION_UNIFIED_VIEW.html",h)
        self.assertTrue(doc.select_one("#projects"))
        self.assertTrue(doc.select_one("#work"))
        self.assertTrue(doc.select_one("#source-data"))
        self.assertFalse(r["safe_to_publish_to_public_app"])
    def test_same_payload_idempotent(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"board.json"
            self.assertTrue(b.write_if_changed(p,'{"v":1}\n'))
            self.assertFalse(b.write_if_changed(p,'{"v":1}\n'))
            self.assertEqual(p.read_text(encoding="utf-8"),'{"v":1}\n')
    def test_actual_integrated_sources(self):
        result=b.run()
        self.assertEqual(result["readback"],"PASS")
        artifact=json.loads(Path(result["progress_index"]).read_text(encoding="utf-8"))
        self.assertEqual(len(artifact["projects"]),9)
        self.assertEqual(len(artifact["work_items"]),10)
        self.assertEqual(artifact["counts"]["blocked"],2)
        self.assertEqual(artifact["counts"]["review"],6)
        self.assertEqual(artifact["counts"]["open"],2)
        self.assertEqual(artifact["counts"]["unregistered_work_ids_in_receipts"],2)
        self.assertEqual(artifact["source_scope"]["oct_native_chat_count"],0)
        c=artifact["counts"]
        registry_path=Path(artifact["portfolio_registry"]["path"])
        registered_tasks=json.loads(registry_path.read_text(encoding="utf-8-sig"))["tasks"]
        registered_count=len(registered_tasks)
        self.assertEqual((c["portfolio_tasks"],c["ai_assignments"],c["project_current_in_portfolio"],
                          c["global_missing_current_work"],c["current_not_ai_assigned"],
                          c["projects_with_explicit_current_unregistered_work"]),(registered_count,10,9,0,9,0))
        self.assertEqual(artifact["portfolio_registry"]["count"],registered_count)
        self.assertTrue(any(m["sha256"]==artifact["portfolio_registry"]["sha256"]
                            and m["path"]==artifact["portfolio_registry"]["path"]
                            for m in artifact["source_manifest"]))
        self.assertFalse(any(x["type"]=="EXPLICIT_PROJECT_CURRENT_WORK_NOT_REGISTERED"
                             for x in artifact["alerts"]))
        self.assertTrue(all(p["progress_percent"] is None for p in artifact["projects"]))
if __name__=="__main__":unittest.main()
