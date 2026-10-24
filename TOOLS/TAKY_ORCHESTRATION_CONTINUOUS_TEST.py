#!/usr/bin/env python3
"""Continuous TAKY local execution: evidence, recovery, protected scopes."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
import TAKY_ORCHESTRATION_ADVANCE as advance

def fixture():
    return {"tasks":[
        {"id":"CLN-001","status":"IMPLEMENTING","title":"Inventory active Git worktrees",
         "category":"POST_CLEANUP","priority":"P0","dependencies":["filesystem-inventory"]},
        {"id":"MCP-001","status":"NOT_STARTED","title":"Audit connected MCP inventory",
         "category":"MCP","priority":"P1","dependencies":["CLN-001"]},
        {"id":"SKL-001","status":"NOT_STARTED","title":"Catalog Claude and Codex skills",
         "category":"SKILLS","priority":"P1","dependencies":["CLN-001"]},
        {"id":"INT-002","status":"IMPLEMENTING","title":"UI design gallery",
         "category":"INTEGRATION","priority":"P0"},
        {"id":"UPD-002","status":"NOT_STARTED","title":"Remote update write",
         "category":"INTEGRATION","priority":"P0","approval_required":True}]}

class ContinuousLocalTests(TestCase):
    def test_periodic_two_item_tick_continues_without_waiting_for_reason(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            board=root/"board.json"
            board.write_text(json.dumps(fixture()),encoding="utf-8")
            visited=[]
            def worker(task,*args):
                visited.append(task)
                return {"task_id":task,
                        "status":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE",
                        "evidence":"test-only"}
            with patch.object(advance,"run_checks",side_effect=worker):
                a=advance.continue_local(board,root/"proof",max_actions=2)
            self.assertEqual(len(a["actions"]),2)
            self.assertEqual(visited,["CLN-001","MCP-001"])
            self.assertEqual(a["max_actions"],2)
            self.assertFalse(a["portfolio_done_claimed"])
            self.assertTrue(a["no_model_calls"])

    def test_invalid_periodic_limits_fail_closed(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            for n in (0,9,-1,True):
                with self.assertRaisesRegex(ValueError,"BOUNDED_CONTINUATION_LIMIT_INVALID"):
                    advance.continue_local(root/"board.json",root/"proof",max_actions=n)

    def test_three_non_ui_jobs_run_without_repeated_user_input(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            board=root/"board.json";board.write_text(json.dumps(fixture()),encoding="utf-8")
            def execute(tid,*unused):
                return {"status":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE",
                        "task_id":tid,"evidence":str(root/(tid+".json"))}
            with patch.object(advance,"run_checks",side_effect=execute):
                result=advance.continue_local(board,root/"proof")
            self.assertEqual([x["task_id"] for x in result["actions"]],
                             ["CLN-001","MCP-001","SKL-001"])
            self.assertFalse(result["portfolio_done_claimed"])
            self.assertTrue(result["no_model_calls"])
            self.assertTrue(result["no_push_merge_deploy"])
            self.assertEqual(json.loads(board.read_text())["tasks"][0]["status"],"IMPLEMENTING")

    def test_failed_one_does_not_prevent_other_independent_jobs(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            board=root/"board.json";board.write_text(json.dumps(fixture()),encoding="utf-8")
            def execute(tid,*unused):
                if tid=="CLN-001":raise ValueError("SOURCE_CHANGED")
                return {"status":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE",
                        "task_id":tid,"evidence":"dummy"}
            with patch.object(advance,"run_checks",side_effect=execute):
                result=advance.continue_local(board,root/"proof")
            self.assertEqual(len(result["actions"]),3)
            self.assertEqual(result["actions"][0]["status"],"LOCAL_EXECUTION_NEEDS_RECOVERY")
            self.assertEqual([x["task_id"] for x in result["actions"][1:]],["MCP-001","SKL-001"])
            self.assertEqual(result["actions"][0]["error_code"],"SOURCE_CHANGED")

if __name__=="__main__":
    main()
