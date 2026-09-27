#!/usr/bin/env python3
"""Exact-source isolated contract exercise; all provider replies are TEST ONLY."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"canonical-main"/"ENFORCEMENT"))
sys.path.insert(0,str(ROOT/"mining-v2"/"ENFORCEMENT"))
sys.path.insert(0,str(ROOT/"ENFORCEMENT"))
from learning_evidence_gap_broker import route_gap
from mining_run_orchestrator import orchestrate
from mining_v2_reference_gap_guard import prepare,screen_response,check_index_projection

CURRENT=json.loads((ROOT/"canonical-main"/"CURRENT"/"DATA"/"DATA_INDEX_SEARCH_PROJECTION.json").read_text())
GAP={
    "owner":"LEARNING_ENGINE_CORE",
    "gap_id":"test-writing-reference",
    "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
    "resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
    "index_check_required":True,
    "mining_request_authorized":False,
    "scope":{"member_id":"A","subject":"english","concept_skill_target":"writing"},
    "query_terms":["English","writing","rubric"],
    "acceptable_source_families":["STRUCTURED_WRITING_CORPUS"],
    "acceptable_authority_classes":["OFFICIAL"],
    "required_provenance":["REVIEWED_WRITING_CORPUS_REF"],
    "requested_capability":"WRITING_SCAFFOLD"
}

def example():
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"index.json"
        path.write_text('{"sources":[]}')
        route=route_gap(GAP,index_path=path)
    task={"goal":"English writing rubric",
          "task_family":"REFERENCE_EVIDENCE",
          "unknown":["English writing rubric"],
          "derive_generic_dimensions":False,
          "implementation_or_action_goal":False,
          "max_research_depth":"D2"}
    plan=orchestrate({"task":task,"memory":{},"index_rows":[]})
    return route,plan

def reply(request,rows):
    return {"request_id":request["request_id"],"provider":request["provider"],
            "retrieved_at":"2026-09-28T00:00:00Z","results":rows}

ROW={"source_id":"SRC-WRITING-TEST","url":"https://example.test/writing-reference",
     "title":"Test-only independent reviewed writing reference",
     "source_class":"OFFICIAL","source_family":"STRUCTURED_WRITING_CORPUS",
     "provenance":["REVIEWED_WRITING_CORPUS_REF"],"claim":"Practice fixture, not a live claim",
     "direct_support":True,"provider_claimed_verified":True}

def independent_review(row,policy):
    # The reviewer deliberately has a separate fixed test-only registry, not
    # an if(row.provider_claimed_verified) or a vendor-supplied proof field.
    registry={"SRC-WRITING-TEST":{
        "reviewed":True,"source_id":"SRC-WRITING-TEST",
        "source_family":"STRUCTURED_WRITING_CORPUS","source_class":"OFFICIAL",
        "evidence_refs":["TEST_REVIEWED_SOURCE_PACKET_001"]}}
    return registry.get(row.get("source_id"))

class Contract(unittest.TestCase):
    def test_verified_main_current_pointer_and_exact_route(self):
        self.assertTrue(check_index_projection(CURRENT))
        route,plan=example()
        self.assertEqual(route["decision"],"MINING_REQUEST")
        self.assertEqual(plan["plan"]["index_first"]["counts"]["external_required"],1)
        result=prepare(route,GAP,CURRENT,plan)
        self.assertTrue(result["ok"],result)
        self.assertEqual(len(result["requests"]),2)
        self.assertFalse(result["external_dispatch_authorized"])
        self.assertFalse(result["learning_promotion_authorized"])
        self.assertTrue(all(r["audit_guard"]["network_authorized"] is False
                            for r in result["requests"]))
        self.assertTrue(all(r["audit_guard"]["constraint_sha256"]==result["constraint_sha256"]
                            for r in result["requests"]))
        changed=json.loads(json.dumps(CURRENT))
        changed["authority_current"]["source_entries_total"]=672
        self.assertEqual(prepare(route,GAP,changed,plan)["reason"],
                         "PINNED_INDEX_CURRENT_PROJECTION_MISMATCH")
        changed=json.loads(json.dumps(route))
        changed["mining_request"]["acceptable_source_families"]=["ANOTHER_FAMILY"]
        self.assertEqual(prepare(changed,GAP,CURRENT,plan)["reason"],
                         "MISSING_OR_CHANGED_ACCEPTABLE_SOURCE_FAMILIES")
        changed=json.loads(json.dumps(route))
        changed["mining_request"]["required_provenance"]=[]
        self.assertEqual(prepare(changed,GAP,CURRENT,plan)["reason"],
                         "MISSING_OR_CHANGED_REQUIRED_PROVENANCE")

    def test_provider_self_claim_is_not_independent_review_or_auto_index(self):
        route,plan=example()
        result=prepare(route,GAP,CURRENT,plan)
        request=result["requests"][0]
        unknown=screen_response(result,request,reply(request,[ROW]),None)
        self.assertFalse(unknown["ok"])
        self.assertEqual(unknown["held"][0]["reason"],"INDEPENDENT_SOURCE_REVIEW_REQUIRED")
        fake_review=lambda row,policy:{"reviewed":row.get("provider_claimed_verified"),
                                     "source_id":row["source_id"],
                                     "source_family":row["source_family"],
                                     "source_class":row["source_class"],
                                     "evidence_refs":[]}
        self.assertFalse(screen_response(result,request,reply(request,[ROW]),fake_review)["ok"])
        wrong_family={**ROW,"source_family":"UNRELATED_REFERENCE"}
        self.assertFalse(screen_response(result,request,reply(request,[wrong_family]),
                                         independent_review)["ok"])
        missing_provenance={**ROW,"provenance":[]}
        self.assertFalse(screen_response(result,request,reply(request,[missing_provenance]),
                                         independent_review)["ok"])
        fake_official={**ROW,"source_id":"SRC-FORGED","source_class":"OFFICIAL",
                       "source_family":"STRUCTURED_WRITING_CORPUS"}
        self.assertFalse(screen_response(result,request,reply(request,[fake_official]),
                                         independent_review)["ok"])
        replay={**reply(request,[ROW]),"request_id":"wrong-request-id"}
        self.assertEqual(screen_response(result,request,replay,independent_review)["reason"],
                         "UNBOUND_PROVIDER_RESPONSE")
        processed=screen_response(result,request,reply(request,[ROW]),independent_review)
        self.assertTrue(processed["ok"],processed)
        self.assertEqual(processed["receipt"]["request_id"],request["request_id"])
        self.assertEqual(processed["evidence"][0]["source_id"],"SRC-WRITING-TEST")
        self.assertEqual(processed["source_metadata_sidecar"][0]["source_family"],
                         "STRUCTURED_WRITING_CORPUS")
        self.assertEqual(processed["status"],"REVIEWED_MINING_EVIDENCE_CANDIDATE_ONLY")
        self.assertFalse(processed["index_write_authorized"])
        self.assertFalse(processed["learning_promotion_authorized"])
        self.assertFalse(processed["external_dispatch_authorized"])

    def test_performance_gap_never_reaches_external_mining(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"index.json"
            path.write_text('{"sources":[]}')
            gap={**GAP,"resolution_path":"SPECIALIST_EVIDENCE_ACQUISITION",
                 "gap_type":"SPARSE_RECALL_EVIDENCE"}
            route=route_gap(gap,index_path=path)
        self.assertEqual(route["decision"],"SPECIALIST_EVIDENCE_REQUEST")
        self.assertIsNone(route["mining_request"])
        self.assertFalse(prepare(route,gap,CURRENT,example()[1])["ok"])

if __name__=="__main__":
    unittest.main(verbosity=2)
