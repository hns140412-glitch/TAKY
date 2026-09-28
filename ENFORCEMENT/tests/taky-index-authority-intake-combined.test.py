#!/usr/bin/env python3
"""Cross-owner invariant on exact combined code: Indexing receipt != Learning policy."""
import json
import tempfile
import unittest
from pathlib import Path
from reference_intake_executor import execute
from learning_evidence_gap_broker import route_gap

SOURCE="1nUpgPyHDd0fWfwrw0jcSgd7fa__TczXq"
ROW={"source_id":SOURCE,
     "title":"2022_개정_교육과정에_따른_초등학교_학생평가_톺아보기(2026).pdf",
     "path":"DATA","source_family":"KICE_ELEMENTARY_ASSESSMENT_2026",
     "authority_level":"AUTHORITY_LAYER","source_review_state":"CONTENT_REVIEWED"}
GAP={"gap_id":"KICE-TEST","owner":"LEARNING_ENGINE_CORE",
     "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
     "scope":{"member_id":"A","subject":"국어","concept_skill_target":"assessment"},
     "resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
     "index_check_required":True,"mining_request_authorized":False,
     "query_terms":["초등학교","학생평가"],
     "acceptable_source_families":["KICE_ELEMENTARY_ASSESSMENT_2026"],
     "acceptable_authority_classes":["OFFICIAL"],
     "required_provenance":["OFFICIAL_STANDARD_REF"]}
ROUTE={"pass":True,"route_type":"REFERENCE_INTAKE_REVIEW",
       "consumer":"LEARNING_ENGINE","domain":"learning"}
RECORD={"source_id":SOURCE,"source_url":"https://example.test/kice",
        "reference_intake_execution":{"acquisition_state":"ACQUIRED_AND_PRESERVED",
        "index_result":{"verified":True,"source_id":SOURCE,
                        "index_version":"V26+FIXTURE","source_ref":"INDEX:"+SOURCE}}}

def fixed_index_owner(sid,proposal):
    if sid!=SOURCE:return None
    return {"issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
            "source_id":SOURCE,"source_ref":"INDEX:"+SOURCE,
            "index_version":"V26+FIXTURE",
            "review_evidence_refs":["FIXTURE_OWNER_PACKET_KICE"]}

class NoOwnerPromotion(unittest.TestCase):
    def test_index_owner_receipt_does_not_turn_descriptive_authority_into_official(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            indexed=root/"sources.json"
            indexed.write_text(json.dumps({"source_entries":[ROW]},ensure_ascii=False))
            before=route_gap(GAP,index_path=indexed)
            self.assertEqual(before["decision"],"INDEX_AUTHORITY_REVIEW_REQUIRED")
            self.assertIsNone(before["mining_request"])
            no_owner=execute(RECORD,ROUTE,root)
            self.assertEqual(no_owner["execution_status"],"REGISTERED_AWAITING_INDEX")
            with_owner=execute(RECORD,ROUTE,root,independent_index_owner_verifier=fixed_index_owner)
            self.assertEqual([x["state"] for x in with_owner["emitted"]],
                             ["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
            self.assertFalse(with_owner["canonical_promotion"])
            after=route_gap(GAP,index_path=indexed)
            self.assertEqual(after["decision"],"INDEX_AUTHORITY_REVIEW_REQUIRED")
            self.assertIsNone(after["mining_request"])
            self.assertFalse(after["index_sufficient"])
            ledger=json.loads((root/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json").read_text())
            self.assertEqual(ledger["entries"][0]["source_key"],SOURCE)
            self.assertEqual(ledger["entries"][-1]["state"],"EVIDENCE_CANDIDATE")
            self.assertEqual(ledger["entries"][-2]["details"]["index_review_issuer"],"INDEXING_OWNER")

if __name__=="__main__":unittest.main(verbosity=2)
