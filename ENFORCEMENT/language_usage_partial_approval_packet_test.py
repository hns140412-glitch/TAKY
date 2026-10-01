#!/usr/bin/env python3
import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"HANDOFF/LANGUAGE_USAGE_PARTIAL_INDEX_APPROVAL_PACKET_2026-10-02_V1.json"

class TestLanguageUsageApprovalPacket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))

    def test_packet_never_executes_promotion(self):
        d=self.d
        self.assertEqual(d["status"],"READY_FOR_HUMAN_APPROVAL__NO_PROMOTION_EXECUTED")
        self.assertEqual(d["authority"],"PROMOTION_APPROVAL_PACKET_ONLY")
        self.assertFalse(d["promotion_executed"])
        self.assertIn("APPROVAL_PACKET != APPROVAL",d["guards"])
        self.assertIn("INDEXED != CURRENT",d["guards"])
        self.assertIn("INDEXED != CANONICAL",d["guards"])

    def test_tatoeba_scope_is_example_only(self):
        p=self.d["proposal"]
        self.assertEqual(p["learning_evidence_kind"],"EXAMPLE_SENTENCE")
        self.assertEqual(p["runtime_authority_scope"],"EXAMPLE_SENTENCE_ONLY")
        self.assertTrue(p["attribution_required"])
        self.assertIn("CONTEXT_EXAMPLE_CANDIDATE",self.d["closes_only"])
        self.assertIn("COLLOCATION_CANDIDATE",self.d["remains_open"])
        self.assertIn("FREQUENCY_AUTHORITY",self.d["remains_open"])
        self.assertIn("UNIVERSAL_NATURALNESS",self.d["remains_open"])

if __name__=="__main__":
    unittest.main()
