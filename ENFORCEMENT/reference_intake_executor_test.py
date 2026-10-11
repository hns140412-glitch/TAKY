#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from reference_intake_executor import execute

def independent_test_owner(sid, proposal):
    return {"issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
            "source_id":"SRC-1","source_ref":"INDEX:SRC-1",
            "index_version":"V26+DELTA","review_evidence_refs":["TEST_OWNER_SRC_1"]}

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
                "source_actor":"Example Author",
                "source_actor_class":"INDEPENDENT_PRACTITIONER",
                "source_author_identity_state":"SELF_IDENTIFIED_NOT_INDEPENDENTLY_VERIFIED",
                "source_direction":"PRACTICAL_WORKFLOW_GUIDANCE",
                "source_direction_signals":["HOW_TO","TOOL_RECOMMENDATION"],
                "applicability_scope":["WORKFLOW_CANDIDATE"],
                "authority_ceiling":"REFERENCE_ONLY",
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
            }, ROUTE, root, independent_index_owner_verifier=independent_test_owner)
            self.assertTrue(result["pass"])
            self.assertEqual([x["state"] for x in result["emitted"]],["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
            self.assertEqual(result["next_handoff"],"DOMAIN_CONSUMER_REQUERY")
            ledger=json.loads((root/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json").read_text(encoding="utf-8"))
            self.assertEqual(len(ledger["entries"]),3)
            self.assertEqual(ledger["entries"][0]["details"]["source_actor_class"],"INDEPENDENT_PRACTITIONER")
            self.assertEqual(ledger["entries"][0]["details"]["authority_ceiling"],"REFERENCE_ONLY")
            self.assertEqual(ledger["entries"][2]["details"]["applicability_scope"],["WORKFLOW_CANDIDATE"])
            lineage_path=root/"LEARNING/evidence/grow-lineage.jsonl"
            self.assertTrue(lineage_path.exists())
            lineage=[json.loads(x) for x in lineage_path.read_text(encoding="utf-8").splitlines() if x.strip()]
            self.assertEqual([x["stage"] for x in lineage],["RAW","INDEX","LEARNING"])
            self.assertTrue(all(x["grow_domain"]=="LEARNING_GROW" for x in lineage))
            self.assertTrue(all(x["promotion_authorized"] is False for x in lineage))
            self.assertEqual(len(result["grow_lineage"]),3)

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
