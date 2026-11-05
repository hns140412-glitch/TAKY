#!/usr/bin/env python3
"""Regression for cross-domain idea/case discovery without false verification."""
import unittest
from work_os_productive_router import route, explore_idea, compare_cases, DISCOVERY_LANES, ANALYSIS_FIELDS, METHODS


class IdeaCaseExplorationTests(unittest.TestCase):
    def test_legacy_idea_route_preserved_and_expanded(self):
        r=route({"kind":"IDEA","idea":"dynamic architectural massing","novelty":"candidate",
                 "usefulness":"project alternatives","cost":"unknown","evidence_state":"INFERRED"})
        self.assertTrue(r["pass"])
        self.assertEqual(r["route"]["destination"],"_LAB")
        self.assertFalse(r["route"]["canonical"])
        self.assertEqual(r["route"]["exploration"]["status"],"EXPLORATION_PLANNED_NOT_EXECUTED")

    def test_all_discovery_lanes_and_methods_no_source_claim(self):
        r=explore_idea({"idea":"site law to 3D mass to editable PPT"})
        self.assertTrue(r["pass"])
        self.assertEqual({x["lane"] for x in r["discovery_lanes"]},set(DISCOVERY_LANES))
        self.assertEqual({x["method"] for x in r["method_candidates"]},set(METHODS))
        self.assertTrue(all(x["state"]=="RESEARCH_NOT_EXECUTED" for x in r["discovery_lanes"]))
        self.assertTrue(r["needs_source_execution"])
        self.assertTrue(r["source_analysis_is_separate_from_taky_application"])
        self.assertTrue(r["paid_api_push_merge_deploy_requires_approval"])

    def test_scoped_research_and_source_reuse(self):
        r=explore_idea({"idea":"Improve visual design", "required_lanes":["EXISTING_ASSETS","ADJACENT_DOMAIN"],
                        "known_source_refs":["local:approved_design_01"]})
        self.assertEqual(len(r["discovery_lanes"]),2)
        self.assertEqual(r["known_source_refs"],["local:approved_design_01"])

    def test_invalid_lane_and_empty_idea_fail(self):
        self.assertFalse(explore_idea({"idea":"x","required_lanes":["FAKE"]})["pass"])
        self.assertFalse(explore_idea({"idea":" "})["pass"])

    def test_case_gap_remains_open(self):
        r=compare_cases({"cases":[{"source_ref":"github:example/app","lane":"OPEN_SOURCE","inputs":"polygon"}],
                         "required_lanes":["OPEN_SOURCE","INTERNATIONAL_DIRECT"]})
        self.assertTrue(r["pass"])
        self.assertEqual(r["status"],"EVIDENCE_REVIEW_OPEN")
        self.assertIn("INTERNATIONAL_DIRECT",r["uncovered_requested_lanes"])
        self.assertIn("github:example/app",r["depth_gaps"])
        self.assertEqual(r["cases"][0]["implementation_trace"]["inputs"],"polygon")
        self.assertIsNone(r["cases"][0]["implementation_trace"]["algorithm_or_code"])
        self.assertEqual(r["cross_model_comparison_status"],"NOT_EXECUTED")
        self.assertEqual(r["implementation_quality_status"],"NOT_TESTED")

    def test_complete_metadata_does_not_claim_semantic_verification(self):
        case={k:"evidence-"+k for k in ANALYSIS_FIELDS}
        case["lane"]="OPEN_SOURCE"
        r=compare_cases({"cases":[case],"required_lanes":["OPEN_SOURCE"]})
        self.assertTrue(r["pass"])
        self.assertEqual(r["cases"][0]["review_state"],"READY_FOR_INDEPENDENT_REVIEW")
        self.assertEqual(r["independent_analysis_status"],"NOT_PROVEN_BY_METADATA")
        self.assertEqual(r["candidate_method_status"],"NOT_SELECTED")

    def test_duplicate_sources_cannot_fake_independent_comparison(self):
        r=route({"kind":"CASE_COMPARE","cases":[{"source_ref":"x"},{"source_ref":"x"}]})
        self.assertFalse(r["pass"])
        self.assertIn("DUPLICATE_SOURCE_REF:x",r["detected"])

    def test_pipeline_visual_routes_unchanged(self):
        self.assertEqual(route({"kind":"PIPELINE","stage":"DISCOVER"})["route"]["next_stage"],"BUILD")
        self.assertEqual(route({"kind":"VISUALIZATION","relation_type":"spatial_location"})["route"]["visualization"],"MAP")

    def test_real_runtime_idea_intent_hook_does_not_fake_authorization(self):
        from pathlib import Path
        from runtime_orchestrator import run
        result=run({
            "intent_kind":"IDEA",
            "intent_text":"Address to rule-aware massing and editable A3/PPT",
        },Path(r"D:\Git PWA\TAKY"),None)
        self.assertEqual(
            result["idea_exploration_advisory"]["status"],
            "EXPLORATION_PLANNED_NOT_EXECUTED",
        )
        self.assertFalse(result["pass"])
        self.assertIn("WORKING_MODEL_MISSING",result["detected"])

    def test_real_runtime_case_review_hook_keeps_gaps_visible(self):
        from pathlib import Path
        from runtime_orchestrator import run
        result=run({
            "case_comparison":{
                "cases":[{"source_ref":"github:jglee96/buildit","lane":"OPEN_SOURCE",
                          "inputs":"parcel polygon"}],
                "required_lanes":["OPEN_SOURCE","ADJACENT_DOMAIN"],
            },
        },Path(r"D:\Git PWA\TAKY"),None)
        advisory=result["case_comparison_advisory"]
        self.assertIn("ADJACENT_DOMAIN",advisory["uncovered_requested_lanes"])
        self.assertEqual(advisory["independent_analysis_status"],"NOT_PROVEN_BY_METADATA")
        self.assertFalse(result["external_executor_invocation_verified"])


if __name__=="__main__":
    unittest.main()
