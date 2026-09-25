#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from reference_intake_executor import execute

ROUTE={
    "pass": True,
    "route_type": "REFERENCE_INTAKE_REVIEW",
    "domain": "learning",
    "consumer": "LEARNING_ENGINE",
}

class ReferenceIntakeExecutorTest(unittest.TestCase):
    def test_register_then_index_then_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=execute({
                "source_id":"SRC-1",
                "source_url":"https://example.test/source",
                "reference_intake_execution":{
                    "acquisition_state":"ACQUIRED_AND_PRESERVED",
                    "recorded_at":"2026-09-25T14:00:00+00:00",
                    "index_result":{
                        "verified":True,
                        "source_id":"SRC-1",
                        "index_version":"V26+DELTA",
                        "source_ref":"INDEX:SRC-1"
                    }
                }
            }, ROUTE, root)
            self.assertTrue(result["pass"])
            self.assertEqual([x["state"] for x in result["emitted"]],["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
            self.assertEqual(result["next_handoff"],"DOMAIN_CONSUMER_REQUERY")
            ledger=json.loads((root/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json").read_text(encoding="utf-8"))
            self.assertEqual(len(ledger["entries"]),3)

    def test_unresolved_binary_is_preserved_not_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=execute({
                "source_url":"https://example.test/resource-page",
                "reference_intake_execution":{
                    "acquisition_state":"RESOURCE_PAGE_VERIFIED__BINARY_URL_UNRESOLVED",
                    "recorded_at":"2026-09-25T14:01:00+00:00"
                }
            }, ROUTE, root)
            self.assertTrue(result["pass"])
            self.assertEqual([x["state"] for x in result["emitted"]],["REGISTERED","NEEDS_MORE_EVIDENCE"])
            self.assertEqual(result["next_handoff"],"MINING_ACQUISITION_REQUIRED")

    def test_access_restricted_is_hold_not_drop(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=execute({
                "source_locator":"drive:restricted",
                "reference_intake_execution":{
                    "acquisition_state":"ACCESS_RESTRICTED",
                    "recorded_at":"2026-09-25T14:02:00+00:00"
                }
            }, ROUTE, root)
            self.assertTrue(result["pass"])
            self.assertEqual(result["emitted"][-1]["state"],"HOLD")

    def test_auto_promotion_forbidden(self):
        with tempfile.TemporaryDirectory() as td:
            result=execute({
                "source_id":"SRC-2",
                "reference_intake_execution":{
                    "acquisition_state":"ACQUIRED_AND_PRESERVED",
                    "requested_disposition":"PROMOTED"
                }
            }, ROUTE, Path(td))
            self.assertFalse(result["pass"])
            self.assertIn("REFERENCE_AUTO_PROMOTION_FORBIDDEN",result["detected"])

    def test_index_not_faked(self):
        with tempfile.TemporaryDirectory() as td:
            result=execute({
                "source_id":"SRC-3",
                "reference_intake_execution":{
                    "acquisition_state":"ACCESSIBLE_REMOTE_SOURCE",
                    "recorded_at":"2026-09-25T14:03:00+00:00"
                }
            }, ROUTE, Path(td))
            self.assertTrue(result["pass"])
            self.assertEqual([x["state"] for x in result["emitted"]],["REGISTERED"])
            self.assertEqual(result["next_handoff"],"INDEX_EXISTENCE_DUPLICATE_VERSION_CHECK")

if __name__=="__main__":
    unittest.main()
