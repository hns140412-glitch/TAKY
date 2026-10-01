#!/usr/bin/env python3
import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"HANDOFF/INDEX_OWNER_PROMOTION_APPROVAL_PACKET_2026-10-02_V1.json"

class TestPromotionApprovalPacket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))

    def test_packet_is_not_execution(self):
        d=self.d
        self.assertEqual(d["status"],"READY_FOR_HUMAN_APPROVAL__NO_PROMOTION_EXECUTED")
        self.assertEqual(d["authority"],"PROMOTION_APPROVAL_PACKET_ONLY")
        self.assertFalse(d["promotion_executed"])
        self.assertIn("APPROVAL_PACKET != APPROVAL",d["global_guards"])
        self.assertIn("HUMAN_APPROVAL_REQUIRED_FOR_INDEX_AUTHORITY_PROMOTION",
                      d["global_guards"])

    def test_only_two_candidates_are_ready_for_formal_decision(self):
        rows={x["decision_id"]:x for x in self.d["decisions"]}
        self.assertEqual(rows["PROMOTE_CURRICULUM_177_TO_CENTRAL_INDEX"]["readiness"],
                         "READY_FOR_FORMAL_INDEX_OWNER_PROMOTION_DECISION")
        self.assertTrue(rows["PROMOTE_CURRICULUM_177_TO_CENTRAL_INDEX"]
                        ["human_approval_required"])
        self.assertEqual(rows["PROMOTE_OEWN_2025_TO_CENTRAL_INDEX"]["readiness"],
                         "READY_FOR_FORMAL_INDEX_OWNER_PROMOTION_DECISION")
        self.assertTrue(rows["PROMOTE_OEWN_2025_TO_CENTRAL_INDEX"]
                        ["human_approval_required"])
        self.assertEqual(rows["HOLD_UD_EWT_LANGUAGE_USAGE"]["readiness"],
                         "NOT_READY_FOR_RUNTIME_PROMOTION")

    def test_promotion_plan_never_claims_canonical_or_deploy(self):
        for row in self.d["decisions"]:
            proposed=row.get("proposed_promotion") or {}
            self.assertNotEqual(proposed.get("canonical_promotion"),True)
        self.assertIn("NO_MAIN_MERGE",self.d["global_guards"])
        self.assertIn("NO_CURRENT_PROMOTION",self.d["global_guards"])
        self.assertIn("NO_NETLIFY_DEPLOYMENT",self.d["global_guards"])

if __name__=="__main__":
    unittest.main()
