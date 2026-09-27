#!/usr/bin/env python3
"""Compose the actual separate PR164 authority-review broker with scoped V2.

No source reclassification, no external dispatch, no hosted principal. A
synthetic V26-schema fixture tests the three real-source policy branches.
"""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"canonical-main"/"ENFORCEMENT"))
sys.path.insert(0,str(ROOT/"mining-v2"/"ENFORCEMENT"))
sys.path.insert(0,str(ROOT/"ENFORCEMENT"))
from data_index_search import load_index
from mining_run_orchestrator import orchestrate
from mining_v2_index_scope_bridge import scope_index_input
from mining_v2_reference_gap_guard import prepare

source=ROOT/"authority-review"/"ENFORCEMENT"/"learning_evidence_gap_broker.py"
spec=importlib.util.spec_from_file_location("pr164_source_review_broker",source)
pr164=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr164)
CURRENT=json.loads((ROOT/"canonical-main"/"CURRENT"/"DATA"/
                    "DATA_INDEX_SEARCH_PROJECTION.json").read_text(encoding="utf-8"))
GAP={"owner":"LEARNING_ENGINE_CORE","gap_id":"audit-authority-review",
    "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
    "resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
    "index_check_required":True,"mining_request_authorized":False,
    "scope":{"member_id":"A","subject":"english",
             "concept_skill_target":"writing"},
    "query_terms":["English","writing","rubric"],
    "acceptable_source_families":["STRUCTURED_WRITING_CORPUS"],
    "acceptable_authority_classes":["OFFICIAL"],
    "required_provenance":["WRITING_CORPUS_SOURCE_REF"]}
ROW={"source_id":"SYNTHETIC-WRITING-1","title":"English writing rubric",
    "path":"TEST_ONLY","source_family":"STRUCTURED_WRITING_CORPUS",
    "authority_level":"AUTHORITY_LAYER",
    "source_review_state":"CONTENT_REVIEWED","review_bucket":"ASSESSED"}
def actual_route(rows,gap=GAP,minimum=1):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"index.json"
        p.write_text(json.dumps({"source_entries":rows}),encoding="utf-8")
        indexed=load_index(p)
        return pr164.route_gap(gap,index_path=p,min_results=minimum),indexed

class Composition(unittest.TestCase):
    def test_descriptive_authority_requires_review_and_no_v2_candidate(self):
        route,records=actual_route([ROW])
        self.assertEqual(route["decision"],"INDEX_AUTHORITY_REVIEW_REQUIRED")
        self.assertIsNone(route["mining_request"])
        self.assertEqual(route["authority_review_request"]["source_candidates"][0][
            "source_authority_literal"],"AUTHORITY_LAYER")
        self.assertEqual(scope_index_input(GAP,route,CURRENT,records)["reason"],
            "MAIN_INDEX_REVIEW_OR_RESULT_NOT_EXTERNAL_MISS")
        self.assertFalse(prepare(route,GAP,CURRENT,{"plan":{}})["ok"])

    def test_literal_official_matches_in_index_not_new_mining(self):
        route,records=actual_route([{**ROW,"authority_level":"OFFICIAL"}])
        self.assertEqual(route["decision"],"INDEX_REQUERY")
        self.assertTrue(route["index_sufficient"])
        self.assertIsNone(route["mining_request"])
        self.assertFalse(scope_index_input(GAP,route,CURRENT,records)["ok"])

    def test_community_missing_reference_still_needs_scoped_v2_not_false_hit(self):
        route,records=actual_route([{**ROW,"source_family":"UNRELATED_COMMUNITY",
                                     "authority_level":"COMMUNITY"}])
        self.assertEqual(route["decision"],"MINING_REQUEST")
        scoped=scope_index_input(GAP,route,CURRENT,records)
        self.assertTrue(scoped["ok"],scoped)
        task={"goal":"English writing rubric","task_family":"REFERENCE_EVIDENCE",
              "unknown":["English writing rubric"],"derive_generic_dimensions":False,
              "implementation_or_action_goal":False,"max_research_depth":"D2"}
        planned=orchestrate({"task":task,"memory":{},
            "index_rows":scoped["scoped_rows"],
            "index_min_results":scoped["index_min_results"]})
        self.assertTrue(planned["plan"]["external_search_required"])
        candidate=prepare(route,GAP,CURRENT,planned)
        self.assertTrue(candidate["ok"],candidate)
        self.assertFalse(candidate["external_dispatch_authorized"])
        self.assertFalse(candidate["learning_promotion_authorized"])

    def test_mixed_one_literal_and_one_descriptive_requires_review_for_two(self):
        other={**ROW,"source_id":"SYNTHETIC-WRITING-2","authority_level":"OFFICIAL"}
        route,records=actual_route([ROW,other],minimum=2)
        self.assertEqual(route["decision"],"INDEX_AUTHORITY_REVIEW_REQUIRED")
        self.assertEqual(len(route["retrieval"]["eligible_results"]),1)
        self.assertEqual(len(route["authority_review_request"]["source_candidates"]),1)
        self.assertFalse(scope_index_input(GAP,route,CURRENT,records)["ok"])

if __name__=="__main__":
    unittest.main(verbosity=2)
