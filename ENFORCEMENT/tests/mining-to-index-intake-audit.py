#!/usr/bin/env python3
"""Actual main reference-intake executor vs reviewed Mining V2 candidate seam.
All source, provider and independent Indexing receipts are synthetic fixtures.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT/"canonical-main"/"ENFORCEMENT",
          ROOT/"mining-v2"/"ENFORCEMENT",ROOT/"ENFORCEMENT"):
    sys.path.insert(0,str(p))
from reference_intake_router import route
from reference_intake_executor import execute,LEDGER_RELATIVE_PATH
from learning_evidence_gap_broker import route_gap
from mining_run_orchestrator import orchestrate
from mining_v2_reference_gap_guard import prepare,screen_response
from mining_to_index_intake_guard import persist_reviewed_candidate

CURRENT=json.loads((ROOT/"canonical-main"/"CURRENT"/"DATA"/
                    "DATA_INDEX_SEARCH_PROJECTION.json").read_text(encoding="utf-8"))
GAP={"owner":"LEARNING_ENGINE_CORE","gap_id":"gap-index-receipt",
     "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
     "resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
     "index_check_required":True,"mining_request_authorized":False,
     "scope":{"member_id":"A","subject":"english","concept_skill_target":"writing"},
     "query_terms":["English","writing","rubric"],
     "acceptable_source_families":["STRUCTURED_WRITING_CORPUS"],
     "acceptable_authority_classes":["OFFICIAL"],
     "required_provenance":["WRITING_CORPUS_SOURCE_REF"]}
ROW={"source_id":"TEST-SRC-INDEX-1","url":"https://example.test/writing",
     "title":"Synthetic reviewed reference only",
     "source_class":"OFFICIAL","source_family":"STRUCTURED_WRITING_CORPUS",
     "provenance":["WRITING_CORPUS_SOURCE_REF"],"claim":"TEST_ONLY_REFERENCE",
     "direct_support":True,"provider_claimed_verified":True}
def reviewed_v2_candidate():
    with tempfile.TemporaryDirectory() as td:
        index=Path(td)/"index.json"
        index.write_text('{"sources":[]}',encoding="utf-8")
        broker=route_gap(GAP,index_path=index)
    plan=orchestrate({"task":{"goal":"English writing rubric",
                "task_family":"REFERENCE_EVIDENCE",
                "unknown":["English writing rubric"],
                "derive_generic_dimensions":False,"implementation_or_action_goal":False,
                "max_research_depth":"D2"},
                "memory":{},"index_rows":[]})
    ready=prepare(broker,GAP,CURRENT,plan)
    assert ready["ok"],ready
    req=ready["requests"][0]
    response={"request_id":req["request_id"],"provider":req["provider"],
              "retrieved_at":"2026-09-28T00:00:00Z","results":[ROW]}
    # Unlike provider_claimed_verified, this registry is independently owned
    # and fixed in the fixture. Real host/source reviewer is still OPEN.
    reviewed={"TEST-SRC-INDEX-1":{"reviewed":True,"source_id":"TEST-SRC-INDEX-1",
        "source_family":"STRUCTURED_WRITING_CORPUS","source_class":"OFFICIAL",
        "evidence_refs":["TEST_INDEPENDENT_METADATA_REVIEW_1"]}}
    result=screen_response(ready,req,response,
        source_metadata_verifier=lambda row,policy:reviewed.get(row.get("source_id")))
    assert result["ok"],result
    return result

def ledger(root):
    path=root/LEDGER_RELATIVE_PATH
    return json.loads(path.read_text(encoding="utf-8"))["entries"] if path.exists() else []

class IntakeContract(unittest.TestCase):
    def test_direct_index_result_flag_is_not_self_authenticating_in_main_executor(self):
        # Source-level diagnostic: actual main executor only checks verified:true.
        # This call occurs in TEMP, not with a canonical user/source path.
        record={"source_id":"TEST-SRC-INDEX-1","source_url":"https://example.test/writing",
            "intent_text":"학습 참고자료로 검토해","reference_intake_intent":True,
            "domain":"learning","reference_intake_execution":{
                "acquisition_state":"ACCESSIBLE_REMOTE_SOURCE",
                "index_result":{"verified":True,"source_id":"WRONG-SOURCE-ID",
                    "source_ref":"INDEX:WRONG-SOURCE-ID","index_version":"UNVERIFIED_CLAIM"}}}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=execute(record,route(record),root)
            self.assertEqual([x["state"] for x in result["emitted"]],
                ["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
            self.assertEqual(result["emitted"][1]["details"]["index_source_id"],
                "WRONG-SOURCE-ID")
            self.assertFalse(result["canonical_promotion"])
        # This demonstrates an unguarded API seam, not real provenance fraud.

    def test_independently_reviewed_mining_candidate_waits_for_real_index_owner(self):
        candidate=reviewed_v2_candidate()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=persist_reviewed_candidate(candidate,"TEST-SRC-INDEX-1",root)
            self.assertTrue(result["ok"],result)
            self.assertEqual(result["recorded_states"],["REGISTERED"])
            self.assertFalse(result["indexed"])
            self.assertEqual(result["next_handoff"],"INDEX_EXISTENCE_DUPLICATE_VERSION_CHECK")
            self.assertEqual([x["state"] for x in ledger(root)],["REGISTERED"])
            self.assertFalse(result["learning_use_authorized"])
            self.assertFalse(result["canonical_promotion"])

    def test_wrong_self_signed_index_attestation_never_reaches_executor(self):
        candidate=reviewed_v2_candidate()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            forged={"proof_id":"PROVIDER_SAYS_VERIFIED","verified":True,
                    "source_id":"TEST-SRC-INDEX-1"}
            no_reviewer=persist_reviewed_candidate(candidate,"TEST-SRC-INDEX-1",
                root,independent_index_receipt=forged)
            self.assertEqual(no_reviewer["reason"],
                "INDEPENDENT_INDEXING_VERIFIER_REQUIRED")
            self.assertEqual(ledger(root),[])
            def rejects(payload):
                return {"verified":True,"owner":"MINING","source_id":"WRONG",
                        "source_ref":"INDEX:WRONG","index_version":"TEST",
                        "review_evidence_ref":"PROVIDER_SELF_CLAIM"}
            wrong=persist_reviewed_candidate(candidate,"TEST-SRC-INDEX-1",root,
                independent_index_receipt=forged,index_verifier=rejects)
            self.assertEqual(wrong["reason"],"INDEPENDENT_INDEXING_RECEIPT_INVALID")
            self.assertEqual(ledger(root),[])

    def test_only_separately_verified_index_receipt_reaches_candidate_not_promotion(self):
        candidate=reviewed_v2_candidate()
        # Fixed reviewer map is not derived from the provider response.
        fixed={"TEST_INDEX_REVIEW_PACKET_1":{
            "verified":True,"owner":"INDEXING","source_id":"TEST-SRC-INDEX-1",
            "source_ref":"INDEX:TEST-SRC-INDEX-1",
            "index_version":"TEST_ONLY_INCREMENTAL_REVIEW_NOT_V26_PROMOTION",
            "review_evidence_ref":"TEST_INDEPENDENT_INDEX_CHECK_1"}}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=persist_reviewed_candidate(candidate,"TEST-SRC-INDEX-1",root,
                independent_index_receipt={"token":"TEST_INDEX_REVIEW_PACKET_1"},
                index_verifier=lambda packet:fixed.get(packet.get("token")))
            self.assertTrue(result["ok"],result)
            self.assertTrue(result["indexed"])
            self.assertEqual(result["recorded_states"],
                ["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
            self.assertEqual(result["next_handoff"],"DOMAIN_CONSUMER_REQUERY")
            self.assertFalse(result["learning_use_authorized"])
            self.assertFalse(result["canonical_promotion"])
            self.assertNotIn("PROMOTED",[x["state"] for x in ledger(root)])
if __name__=="__main__":
    unittest.main(verbosity=2)
