#!/usr/bin/env python3
"""Regression: V2 raw primary count must not close a main Learning evidence gap.

Imports *actual* independently pinned main index/broker and V2 run orchestrator.
Fixture is a tiny V26-compatible schema, NOT a fetched/canonical V26 corpus.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
for directory in (ROOT/"canonical-main"/"ENFORCEMENT",
                  ROOT/"mining-v2"/"ENFORCEMENT",ROOT/"ENFORCEMENT"):
    sys.path.insert(0,str(directory))
from data_index_search import load_index
from learning_evidence_gap_broker import route_gap
from mining_run_orchestrator import orchestrate
from mining_v2_index_scope_bridge import scope_index_input
from mining_v2_reference_gap_guard import prepare

CURRENT=json.loads((ROOT/"canonical-main"/"CURRENT"/"DATA"/
                   "DATA_INDEX_SEARCH_PROJECTION.json").read_text(encoding="utf-8"))
QUERY="English writing rubric"
GAP={
    "owner":"LEARNING_ENGINE_CORE","gap_id":"audited-writing-reference",
    "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
    "resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
    "index_check_required":True,"mining_request_authorized":False,
    "scope":{"member_id":"A","subject":"english","concept_skill_target":"writing"},
    "query_terms":["English","writing","rubric"],
    "acceptable_source_families":["STRUCTURED_WRITING_CORPUS"],
    "acceptable_authority_classes":["OFFICIAL"],
    "required_provenance":["WRITING_CORPUS_SOURCE_REF"]
}
UNRELATED={
    "source_id":"SRC-UNRELATED-COMMUNITY",
    "title":"English writing rubric conversation","path":"test/community",
    "source_family":"UNRELATED_COMMUNITY",
    "source_type":"DISCUSSION","authority_level":"COMMUNITY",
    "source_review_state":"CONTENT_REVIEWED","review_bucket":"ASSESSED",
    "value_statement":"English writing rubric",
}
ELIGIBLE={
    "source_id":"SRC-ELIGIBLE-REVIEWED",
    "title":"English writing rubric documented","path":"test/official",
    "source_family":"STRUCTURED_WRITING_CORPUS",
    "source_type":"OFFICIAL_GUIDANCE","authority_level":"OFFICIAL",
    "source_review_state":"CONTENT_REVIEWED","review_bucket":"ASSESSED",
    "value_statement":"English writing rubric",
}
def run_both(source_rows,minimum):
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/"index.json"
        file.write_text(json.dumps({"source_entries":source_rows}),encoding="utf-8")
        rows=load_index(file)
        route=route_gap(GAP,index_path=file,min_results=minimum)
        assert route["decision"]=="MINING_REQUEST",route
        task={"goal":QUERY,"task_family":"REFERENCE_EVIDENCE",
              "unknown":[QUERY],"derive_generic_dimensions":False,
              "implementation_or_action_goal":False,"max_research_depth":"D2"}
        unscoped=orchestrate({"task":task,"memory":{},"index_rows":rows})
        guarded=scope_index_input(GAP,route,CURRENT,rows)
        assert guarded["ok"],guarded
        safe=orchestrate({"task":task,"memory":{},
                         "index_rows":guarded["scoped_rows"],
                         "index_min_results":guarded["index_min_results"]})
        return route,rows,unscoped,guarded,safe
class SourceCountSafety(unittest.TestCase):
    def test_unrelated_primary_is_v2_false_sufficiency_but_guard_keeps_gap_open(self):
        route,rows,raw,guarded,safe=run_both([UNRELATED],1)
        self.assertEqual(route["retrieval"]["result_count"],1)
        self.assertEqual(route["mining_request"]["index_check"]["eligible_result_count"],0)
        # Reproduce the actual previously missed cross-layer compatibility bug:
        self.assertEqual(raw["plan"]["index_first"]["counts"]["resolved_from_index"],1)
        self.assertFalse(raw["plan"]["external_search_required"])
        # Actual V2 engine after current-main eligibility scoping:
        self.assertEqual(guarded["ineligible_rows_excluded"],1)
        self.assertEqual(guarded["eligible_source_ids"],[])
        self.assertEqual(safe["plan"]["index_first"]["counts"]["resolved_from_index"],0)
        self.assertTrue(safe["plan"]["external_search_required"])
        prepared=prepare(route,GAP,CURRENT,safe)
        self.assertTrue(prepared["ok"],prepared)
        self.assertFalse(prepared["external_dispatch_authorized"])
        self.assertFalse(prepared["index_write_authorized"])

    def test_minimum_two_cannot_be_satisfied_by_one_eligible_and_unrelated_hit(self):
        route,rows,raw,guarded,safe=run_both([ELIGIBLE,UNRELATED],2)
        self.assertEqual(route["mining_request"]["index_check"]["eligible_result_count"],1)
        self.assertFalse(raw["plan"]["external_search_required"])
        self.assertEqual(guarded["eligible_source_ids"],["SRC-ELIGIBLE-REVIEWED"])
        self.assertEqual(guarded["index_min_results"],2)
        self.assertEqual(safe["plan"]["index_first"]["counts"]["resolved_from_index"],0)
        self.assertTrue(safe["plan"]["external_search_required"])
        self.assertTrue(prepare(route,GAP,CURRENT,safe)["ok"])

    def test_changed_source_receipt_and_held_review_fail_closed(self):
        route,rows,raw,guarded,safe=run_both([ELIGIBLE,UNRELATED],2)
        forged=copy.deepcopy(route)
        forged["retrieval"]["eligible_results"][0]["source_id"]="SRC-UNRELATED-COMMUNITY"
        self.assertEqual(scope_index_input(GAP,forged,CURRENT,rows)["reason"],
                         "MAIN_INDEX_ELIGIBLE_PROVENANCE_CHANGED")
        stale=copy.deepcopy(CURRENT)
        stale["authority_current"]["source_entries_total"]=666
        self.assertEqual(scope_index_input(GAP,route,stale,rows)["reason"],
                         "CURRENT_INDEX_POINTER_INVALID")
        held=copy.deepcopy(rows)
        held[0]["review_state"]="HOLD"
        self.assertEqual(scope_index_input(GAP,route,CURRENT,held)["reason"],
                         "SOURCE_REVIEW_NOT_CLEARED")
        duplicate=copy.deepcopy(rows)+[copy.deepcopy(rows[0])]
        self.assertEqual(scope_index_input(GAP,route,CURRENT,duplicate)["reason"],
                         "SOURCE_PROJECTION_ID_MISSING_OR_DUPLICATE")
        need_review=copy.deepcopy(route)
        need_review["decision"]="INDEX_AUTHORITY_REVIEW_REQUIRED"
        self.assertEqual(scope_index_input(GAP,need_review,CURRENT,rows)["reason"],
                         "MAIN_INDEX_REVIEW_OR_RESULT_NOT_EXTERNAL_MISS")
        performance=copy.deepcopy(GAP)
        performance["resolution_path"]="SPECIALIST_EVIDENCE_ACQUISITION"
        self.assertEqual(scope_index_input(performance,route,CURRENT,rows)["reason"],
                         "REFERENCE_GAP_POLICY_REQUIRED")
if __name__=="__main__":
    unittest.main(verbosity=2)
