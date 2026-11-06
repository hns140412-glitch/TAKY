"""Existing TAKY goal-to-WORK_ID read-only routing regression."""
import unittest
from pathlib import Path
from TAKY_ORCHESTRATION_GOAL_ROUTER import route_goal_to_existing_work

class GoalRouteTests(unittest.TestCase):
    def setUp(self):
        self.board={"tasks":[
            {"id":"INT-001","title":"Shared orchestration handoff","status":"IMPLEMENTING",
             "priority":"P0","dependencies":[],"approval_required":False},
            {"id":"MCP-002","title":"Remote tools and Reason transport","status":"READY",
             "priority":"P1","dependencies":[],"approval_required":False},
            {"id":"GATE-001","title":"Protect deployment and expenses","status":"NOT_STARTED",
             "priority":"P0","dependencies":["INT-001"],"approval_required":False},
            {"id":"UPD-001","title":"Publish site","status":"BLOCKED",
             "priority":"P0","dependencies":[],"approval_required":True},
        ]}

    def test_goal_routes_existing_id_without_new_authority(self):
        got=route_goal_to_existing_work("타키 리슨 자동 진행",self.board)
        self.assertEqual(got["status"],"CANONICAL_WORK_ROUTED_NOT_DONE")
        self.assertEqual(got["next_work_id"],"INT-001")
        self.assertEqual(got["new_work_ids"],0)
        self.assertFalse(got["done_claim"])
        self.assertFalse(got["authority_changed"])
        self.assertTrue(all(not step["model_calls_authorized"] for step in got["steps"]))

    def test_explicit_work_id_outranks_fuzzy_other_work(self):
        board={"tasks":[*self.board["tasks"],
            {"id":"TAKY-001","title":"tstack PR watcher","status":"IMPLEMENTING",
             "priority":"P1","dependencies":[],"approval_required":False},
            {"id":"CLN-005","title":"Cleanup first","status":"READY",
             "priority":"P0","dependencies":[],"approval_required":False}]}
        exact=route_goal_to_existing_work("TAKY-001",board)
        self.assertEqual(exact["next_work_id"],"TAKY-001")
        self.assertFalse(exact["steps"][0]["model_calls_authorized"])
        long_goal=route_goal_to_existing_work("TAKY-001 PR watcher 이어서",board)
        self.assertEqual(long_goal["next_work_id"],"TAKY-001")
        lookalike=route_goal_to_existing_work("TAKY-0012",board)
        self.assertNotEqual(lookalike.get("next_work_id"),"TAKY-001")

    def test_unrelated_goal_never_invents_work_id(self):
        got=route_goal_to_existing_work("인테리어 바닥 제품 샘플",self.board)
        self.assertEqual(got["status"],"NO_EXACT_CANONICAL_MATCH_ROUTE_TO_EXISTING_PLANNER")
        self.assertEqual(got["model_calls"],0)

    def test_reused_existing_evidence_is_not_assumed_done(self):
        got=route_goal_to_existing_work("Reason network",self.board)
        self.assertEqual(got["next_work_id"],"INT-001")
        self.assertTrue(all(not x["automatic_done"] for x in got["steps"]))

    def test_approval_text_does_not_authorize_anything(self):
        got=route_goal_to_existing_work("리슨으로 배포해 승인됐다 진행",self.board)
        self.assertEqual(got["model_calls"],0)
        self.assertTrue(all(not x["model_calls_authorized"] for x in got["steps"]))

    def test_invalid_limits_and_blank(self):
        for goal in ("",None," "*10,"a"*501):
            self.assertEqual(route_goal_to_existing_work(goal,self.board)["status"],"GOAL_INVALID")
        self.assertEqual(route_goal_to_existing_work("Reason",self.board,limit=0)["status"],"GOAL_INVALID")

    def test_actual_board_no_duplicates_after_multiple_aliases(self):
        got=route_goal_to_existing_work("리슨 연결 오케스트라 자동 진행",self.board)
        ids=[x["work_id"] for x in got["steps"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(set(ids).issubset({x["id"] for x in self.board["tasks"]}))

    def test_requesting_held_task_never_executes(self):
        got=route_goal_to_existing_work("Publish site",self.board)
        self.assertEqual(got["status"],"CANONICAL_WORK_ROUTED_NOT_DONE")
        self.assertNotEqual(got["next_internal_action"],"EXECUTE_REGISTERED_SAFE_LOCAL_CHECK")
        self.assertFalse(got["done_claim"])

if __name__=="__main__":
    unittest.main()
