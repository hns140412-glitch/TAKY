"""Trusted local goal signal -> registered TAKY WORK_ID, without model dispatch."""
import json
from pathlib import Path
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch
import uuid

import reason_queue_ingress
import taky_prepared_goal
from reason_queue_ingress import route_message

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "TOOLS"))
import TAKY_ORCHESTRATION_GOAL_ROUTER as router


class PreparedGoalTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)
        self.local=self.repo / ".local"
        self.local.mkdir()
        self.qid="taky"+uuid.uuid4().hex[:14]
        self.mid="01M5NEX"+uuid.uuid4().hex[:23].upper()
        self.raw=(f'<reason-message from="taky-local/local-test" agent="cli" '
                  f'id="{self.mid}">\nTAKY_GOAL_SIGNAL_V1 queue={self.qid}\n'
                  '</reason-message>\n')
        self.intent=self.local / ("taky-goal-intent-"+self.qid+".json")
        self.board=self.repo / "board.json"
        self.board.write_text(json.dumps({"tasks":[
            {"id":"INT-001","title":"Independent model orchestration","status":"IMPLEMENTING",
             "priority":"P0","dependencies":[],"approval_required":False},
            {"id":"MCP-002","title":"Reason network delivery","status":"READY",
             "priority":"P1","dependencies":[],"approval_required":False},
        ]}), encoding="utf-8")
        self.settings=[
            patch.object(router,"DEFAULT_BOARD",self.board),
            patch.object(router,"EVIDENCE",None),
            patch.object(reason_queue_ingress,"_trusted_steering_local_dir",return_value=self.local),
        ]
        for p in self.settings:
            p.start()
            self.addCleanup(p.stop)

    def prepare(self,goal="TAKY 리슨 자동 인계"):
        self.intent.write_text(json.dumps({"schema":"TAKY_GOAL_INTENT_V1",
                                           "queue_id":self.qid,"goal_text":goal},
                                          ensure_ascii=False),encoding="utf-8")

    def dispatch(self):
        return route_message(self.repo,self.raw,execute=True,
                             identity_check=lambda:True,
                             queue_executor=lambda *_:self.fail("GOAL_MUST_NOT_LAUNCH_MODELS"))

    def test_prepared_intent_routes_existing_work_only(self):
        self.prepare()
        data=self.dispatch()
        self.assertEqual(data["status"],"REASON_GOAL_ROUTED_TO_CANONICAL_WORK")
        self.assertEqual(data["next_work_id"],"INT-001")
        self.assertFalse(data["dispatched"])
        receipt=self.repo/data["local_plan_receipt"]
        plan=json.loads(receipt.read_text(encoding="utf-8"))
        self.assertTrue(plan["registered_work_ids_only"])
        self.assertEqual(plan["model_calls"],0)
        self.assertFalse(plan["done_claim"])

    def test_message_replay_reuses_plan(self):
        self.prepare()
        first=self.dispatch()
        second=self.dispatch()
        self.assertEqual(first["status"],"REASON_GOAL_ROUTED_TO_CANONICAL_WORK")
        self.assertEqual(second["status"],"REASON_GOAL_PLAN_REUSED")
        self.assertFalse(second["dispatched"])

    def test_intent_changes_require_explicit_new_plan(self):
        self.prepare()
        self.dispatch()
        self.prepare("TAKY Reason")
        response=self.dispatch()
        self.assertEqual(response["status"],"REASON_GOAL_CHANGED_REPLAN_REQUIRED")

    def test_canonical_board_change_requires_new_plan(self):
        self.prepare()
        self.dispatch()
        source=json.loads(self.board.read_text(encoding="utf-8"))
        source["tasks"][0]["status"]="BLOCKED"
        self.board.write_text(json.dumps(source),encoding="utf-8")
        response=self.dispatch()
        self.assertEqual(response["status"],"REASON_GOAL_CHANGED_REPLAN_REQUIRED")

    def test_unsafe_intent_schema_fails_closed(self):
        self.intent.write_text(json.dumps({
            "schema":"TAKY_GOAL_INTENT_V1","queue_id":self.qid,
            "goal_text":"TAKY 리슨","shell":"powershell -enc ..."
        }),encoding="utf-8")
        self.assertEqual(self.dispatch()["status"],"REASON_PREPARED_GOAL_INVALID")

    def test_no_intent_does_not_invent_goal(self):
        self.assertEqual(self.dispatch()["status"],"REASON_PREPARED_MANIFEST_MISSING")

    def test_oversized_goal_rejected(self):
        self.prepare("x"*600)
        self.assertEqual(self.dispatch()["status"],"REASON_PREPARED_GOAL_INVALID")

    def test_unmatched_goal_does_not_claim_accepted_plan(self):
        self.prepare("오늘 날씨")
        result=self.dispatch()
        self.assertEqual(result["status"],"REASON_GOAL_NO_CANONICAL_MATCH")
        self.assertFalse(result["dispatched"])
        self.assertFalse((self.local / ("taky-goal-plan-"+self.mid+".json")).exists())

    def test_routing_evidence_change_invalidates_cached_goal(self):
        self.prepare()
        from unittest.mock import patch
        original=router.route_goal_to_existing_work
        previous=self.dispatch()
        self.assertEqual(previous["status"],"REASON_GOAL_ROUTED_TO_CANONICAL_WORK")
        def changed_route(goal,board,evidence=None):
            fresh=original(goal,board,evidence)
            fresh["next_internal_action"]="RECHECK_NEW_SIGNED_EVIDENCE"
            return fresh
        with patch.object(router,"route_goal_to_existing_work",side_effect=changed_route):
            refreshed=self.dispatch()
        self.assertEqual(refreshed["status"],"REASON_GOAL_CHANGED_REPLAN_REQUIRED")

    def test_invalid_manifest_does_not_fall_back_to_goal(self):
        self.prepare()
        m=self.local/("taky-intake-"+self.qid+".json")
        m.write_text("{}",encoding="utf-8")
        self.assertEqual(self.dispatch()["status"],"REASON_PREPARED_MANIFEST_INVALID")

    def test_goal_does_not_convert_manual_approval_to_done(self):
        self.prepare("타키 리슨 배포 자동 실행")
        got=self.dispatch()
        plan=json.loads((self.repo/got["local_plan_receipt"]).read_text(encoding="utf-8"))
        self.assertFalse(plan["done_claim"])
        self.assertEqual(plan["model_calls"],0)


if __name__ == "__main__":
    import unittest
    unittest.main()
