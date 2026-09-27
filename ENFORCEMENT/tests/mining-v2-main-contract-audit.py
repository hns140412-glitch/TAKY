#!/usr/bin/env python3
"""Read-only, test-only adapter proof of the CURRENT main Learning-gap -> V2
Mining RUN PLAN seam. Does NOT authorize a provider, modify Index CURRENT,
record user outcomes, or replace either semantic owner. Both code trees must
be checked out at exact pinned SHAs into canonical-main/ and mining-v2/.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT/"canonical-main"/"ENFORCEMENT"
V2=ROOT/"mining-v2"/"ENFORCEMENT"
sys.path.insert(0,str(V2))
sys.path.insert(0,str(MAIN))
from learning_evidence_gap_broker import route_gap
from mining_run_orchestrator import orchestrate

def prepare_v2_candidate_from_main_gap(route):
    if route.get("pass") is not True or route.get("decision")!="MINING_REQUEST" or (
        route.get("index_checked") is not True or route.get("index_sufficient") is not False):
        return {"ok":False,"reason":"CURRENT_INDEX_FIRST_MISSING_OR_NOT_INSUFFICIENT"}
    request=route.get("mining_request") or {}
    check=request.get("index_check") or {}
    mandatory={"MINING_DISCOVERS_AND_ACQUIRES_ONLY","INDEXING_OWNS_PERSISTENT_CLASSIFICATION",
               "LEARNING_OWNS_FINAL_EVIDENCE_USE_DECISION","NO_CANONICAL_PROMOTION"}
    if request.get("request_type")!="DOMAIN_EVIDENCE_GAP_MINING_REQUEST" or (
        request.get("requester")!="LEARNING_ENGINE" or
        not str(request.get("gap_id") or "").strip() or
        check.get("performed") is not True or
        check.get("eligible_result_count",0)>=check.get("minimum_required",1) or
        not mandatory.issubset(set(request.get("constraints") or []))):
        return {"ok":False,"reason":"LEARNING_MINING_REQUEST_CONTRACT_INVALID"}
    terms=[str(x).strip() for x in request.get("query_terms") or [] if str(x).strip()]
    families=request.get("acceptable_source_families") or []
    authorities=request.get("acceptable_authority_classes") or []
    provenance=request.get("required_provenance") or []
    if not terms or not families or not authorities or not provenance:
        return {"ok":False,"reason":"EXPLICIT_REFERENCE_QUERY_AND_SOURCE_CONSTRAINTS_REQUIRED"}
    task={
        "goal":" ".join(terms),"task_family":"REFERENCE_EVIDENCE",
        "unknown":[" ".join(terms)],"requirements":[],
        "derive_generic_dimensions":False,"implementation_or_action_goal":False,
        "freshness_required":False,"max_research_depth":"D2",
        "route_signature":"LEARNING_GAP:"+str(request["gap_id"]),
        "index_source_current_required":True,
        "gap_id":request["gap_id"],
        # V2 orchestrator currently does NOT enforce these fields in provider
        # dispatch. Keep all constraints attached but make dispatch forbidden.
        "reference_source_constraints":{"families":families,"authority":authorities,
            "required_provenance":provenance}
    }
    return {"ok":True,"authority":"AUDIT_TEST_CANDIDATE_ONLY","task":task,
            "source_constraints_require_provider_binding":True,
            "provider_execution_authorized":False,
            "current_index_write_authorized":False,
            "canonical_promotion_authorized":False}

def reference_gap():
    return {
        "owner":"LEARNING_ENGINE_CORE","gap_id":"gap-writing-1",
        "gap_type":"REFERENCE_EVIDENCE_REQUIRED","resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
        "index_check_required":True,"mining_request_authorized":False,
        "scope":{"member_id":"A","subject":"영어","concept_skill_target":"writing"},
        "query_terms":["영어","writing","rubric"],
        "requested_capability":"WRITING_PROCESS_SCAFFOLD",
        "acceptable_source_families":["STRUCTURED_WRITING_CORPUS"],
        "acceptable_authority_classes":["OFFICIAL"],
        "required_provenance":["WRITING_CORPUS_SOURCE_REF"]
    }

class ActualBranchContract(unittest.TestCase):
    def test_actual_main_gap_broker_routes_reference_but_not_student_gap(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"index.json"
            path.write_text(json.dumps({"sources":[]}),encoding="utf-8")
            gap=reference_gap()
            route=route_gap(gap,index_path=path)
            self.assertEqual(route["decision"],"MINING_REQUEST")
            self.assertTrue(route["mining_request"]["index_check"]["performed"])
            candidate=prepare_v2_candidate_from_main_gap(route)
            self.assertTrue(candidate["ok"],candidate)
            self.assertFalse(candidate["provider_execution_authorized"])
            self.assertFalse(candidate["canonical_promotion_authorized"])
            self.assertEqual(candidate["task"]["reference_source_constraints"]["families"],
                             ["STRUCTURED_WRITING_CORPUS"])
            v2=orchestrate({"task":candidate["task"],"memory":{},"index_rows":[]})
            self.assertEqual(v2["schema"],"TAKY_MINING_RUN_ORCHESTRATOR_V1")
            plan=v2["plan"]
            self.assertTrue(plan["index_first"]["guards"]["index_does_not_decide_domain_use"])
            self.assertTrue(plan["external_search_required"])
            self.assertEqual(plan["index_first"]["counts"]["resolved_from_index"],0)
            self.assertEqual(plan["index_first"]["counts"]["external_required"],1)
            self.assertIsNone(v2["memory_learning_proposal"])
            # V2's generic execution_allowed is only route-memory status;
            # it does NOT license provider dispatch from a Learning gap.
            self.assertFalse(candidate["provider_execution_authorized"])
            self.assertFalse(candidate["current_index_write_authorized"])
            student_gap=dict(gap,resolution_path="SPECIALIST_EVIDENCE_ACQUISITION",
                             gap_type="SPARSE_RECALL_EVIDENCE")
            specialist=route_gap(student_gap,index_path=path)
            self.assertEqual(specialist["decision"],"SPECIALIST_EVIDENCE_REQUEST")
            self.assertIsNone(specialist["mining_request"])
            self.assertFalse(prepare_v2_candidate_from_main_gap(specialist)["ok"])
            tampered=json.loads(json.dumps(route))
            tampered["mining_request"]["constraints"]=[]
            self.assertEqual(prepare_v2_candidate_from_main_gap(tampered)["reason"],
                             "LEARNING_MINING_REQUEST_CONTRACT_INVALID")
            tampered=json.loads(json.dumps(route))
            tampered["mining_request"]["required_provenance"]=[]
            self.assertEqual(prepare_v2_candidate_from_main_gap(tampered)["reason"],
                             "EXPLICIT_REFERENCE_QUERY_AND_SOURCE_CONSTRAINTS_REQUIRED")

if __name__=="__main__":
    unittest.main(verbosity=2)
