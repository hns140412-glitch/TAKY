#!/usr/bin/env python3
"""No Mining self-verification, cross-source receipt or guessed Index owner."""
import json
import tempfile
import unittest
from pathlib import Path
from reference_intake_executor import execute
from reference_index_owner_receipt import bind_verified_index_result

ROUTE={"pass":True,"route_type":"REFERENCE_INTAKE_REVIEW",
       "domain":"learning","consumer":"LEARNING_ENGINE"}
PROPOSED={"verified":True,"source_id":"SRC-A",
          "source_ref":"INDEX:SRC-A","index_version":"V26+TEST"}
RECORD={"source_id":"SRC-A","source_url":"https://example.test/a",
        "reference_intake_execution":{"acquisition_state":"ACQUIRED_AND_PRESERVED",
                                      "index_result":PROPOSED}}
REGISTRY={
    "SRC-A":{"issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
             "source_id":"SRC-A","source_ref":"INDEX:SRC-A","index_version":"V26+TEST",
             "review_evidence_refs":["TEST_INDEPENDENT_INDEX_OWNER_REVIEW_A"]},
}
def reviewer(source_id,proposal):
    # Pure FIXTURE registry independent of request/proposed. No live credentials.
    return REGISTRY.get(source_id)

def run(record,verifier=None):
    with tempfile.TemporaryDirectory() as td:
        r=execute(record,ROUTE,Path(td),independent_index_owner_verifier=verifier)
        ledger=json.loads((Path(td)/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json")
                          .read_text(encoding="utf-8"))
        return r,ledger

class OwnerBoundary(unittest.TestCase):
    def test_unconfigured_verifier_cannot_be_replaced_by_payload_verified(self):
        out,ledger=run(RECORD)
        self.assertEqual(out["execution_status"],"REGISTERED_AWAITING_INDEX")
        self.assertEqual(out["index_guard_reason"],"INDEX_OWNER_VERIFIER_NOT_CONFIGURED")
        self.assertEqual([x["state"] for x in ledger["entries"]],["REGISTERED"])
        self.assertFalse(out["canonical_promotion"])

    def test_proposed_source_b_does_not_index_source_a(self):
        altered=json.loads(json.dumps(RECORD))
        altered["reference_intake_execution"]["index_result"]["source_id"]="SRC-B"
        out,ledger=run(altered,reviewer)
        self.assertEqual(out["index_guard_reason"],"INDEX_RESULT_SOURCE_BINDING_INVALID")
        self.assertEqual([x["state"] for x in ledger["entries"]],["REGISTERED"])

    def test_payload_owner_receipt_flag_cannot_be_sole_proof(self):
        altered=json.loads(json.dumps(RECORD))
        altered["reference_intake_execution"]["index_result"].update({
            "issuer":"INDEXING_OWNER","reviewed":True,"review_evidence_refs":["FAKE"]})
        out,ledger=run(altered)
        self.assertEqual([x["state"] for x in ledger["entries"]],["REGISTERED"])

    def test_independent_owner_receipt_requires_matching_identity_and_evidence(self):
        for changed in (
            {"issuer":"MINING_PROVIDER"},
            {"source_ref":"INDEX:SRC-B"},
            {"index_version":"OTHER"},
            {"review_evidence_refs":[]},
            {"source_id":"SRC-B"},
            {"reviewed":False},
            {"decision":"CANDIDATE"},
        ):
            def wrong(source_id,proposal):
                return {**REGISTRY[source_id],**changed}
            out,ledger=run(RECORD,wrong)
            self.assertEqual(out["index_guard_reason"],"INDEPENDENT_INDEX_RECEIPT_INVALID")
            self.assertEqual([x["state"] for x in ledger["entries"]],["REGISTERED"])

    def test_verifier_exception_preserves_registered(self):
        def broken(source_id,proposal):raise RuntimeError("offline")
        out,ledger=run(RECORD,broken)
        self.assertEqual(out["index_guard_reason"],"INDEX_OWNER_REVIEW_UNAVAILABLE")
        self.assertEqual([x["state"] for x in ledger["entries"]],["REGISTERED"])

    def test_independent_test_review_allows_index_candidate_but_not_promotion(self):
        out,ledger=run(RECORD,reviewer)
        self.assertEqual([x["state"] for x in ledger["entries"]],
                         ["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
        indexed=ledger["entries"][1]["details"]
        self.assertEqual(indexed["index_source_id"],"SRC-A")
        self.assertEqual(indexed["index_review_issuer"],"INDEXING_OWNER")
        self.assertEqual(indexed["index_review_evidence_refs"],
                         ["TEST_INDEPENDENT_INDEX_OWNER_REVIEW_A"])
        self.assertFalse(out["canonical_promotion"])

    def test_source_url_only_requires_indexing_owned_id(self):
        record=json.loads(json.dumps(RECORD));record.pop("source_id")
        out,ledger=run(record,reviewer)
        self.assertEqual(out["index_guard_reason"],"INDEX_SOURCE_ID_NOT_YET_ASSIGNED")
        self.assertEqual([x["state"] for x in ledger["entries"]],["REGISTERED"])

    def test_no_accepted_disposition_can_trigger_promotion(self):
        record=json.loads(json.dumps(RECORD))
        record["reference_intake_execution"]["requested_disposition"]="PROMOTED"
        with tempfile.TemporaryDirectory() as td:
            r=execute(record,ROUTE,Path(td),independent_index_owner_verifier=reviewer)
            self.assertFalse(r["pass"])
            self.assertIn("REFERENCE_AUTO_PROMOTION_FORBIDDEN",r["detected"])
            self.assertFalse((Path(td)/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json").exists())

if __name__=="__main__":unittest.main(verbosity=2)
