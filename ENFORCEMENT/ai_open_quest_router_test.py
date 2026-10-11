#!/usr/bin/env python3
import unittest
from ai_open_quest_router import route

class AIOpenQuestRouterTest(unittest.TestCase):
    def test_closed_artifact_quests_are_not_reopened(self):
        r=route({
          "artifact_production":True,"existing_artifact_or_source":True,
          "small_correction":True,"editable_output_required":True,
          "visual_design":True,"approved_source_asset":True,
        })
        ids={x["learning_id"] for x in r["selected"]}
        for closed in {
          "AI-LRN-HUMAN-EDITABLE-OUTPUT",
          "AI-LRN-LOCAL-EDIT-BEFORE-REGENERATION",
          "AI-LRN-TRANSFORM-EXISTING-ASSET-BEFORE-RECREATE",
          "AI-LRN-DESIGN-TASTE-AS-EXPLICIT-CONSTRAINT",
          "AI-LRN-SOURCE-ASSET-QUALITY-SETS-OUTPUT-CEILING",
          "AI-LRN-STAGED-ARTIFACT-WORKFLOW",
        }:
            self.assertNotIn(closed,ids)

    def test_learning_routes_only_with_observable_response(self):
        no=route({"learning_flow":True,"ai_literacy_topic":True})
        self.assertEqual(no["selected_count"],0)
        yes=route({"learning_flow":True,"ai_literacy_topic":True,"learner_response_available":True})
        ids={x["learning_id"] for x in yes["selected"]}
        self.assertIn("AI-LRN-LITERACY-BEFORE-TOOL-SPEED",ids)
        self.assertIn("AI-LRN-MENTAL-MODEL-OF-CAPABILITIES-AND-LIMITS",ids)

    def test_adopted_quests_are_not_reopened(self):
        r=route({"artifact_production":True,"visual_design":True,"representative_baseline_available":True})
        ids={x["learning_id"] for x in r["selected"]}
        self.assertNotIn("AI-LRN-DESIGN-PIPELINE-NOT-PROMPT-ONLY",ids)
        self.assertNotIn("AI-LRN-DESIGN-REFERENCE-PLUS-REVIEW",ids)

    def test_verify_on_need_requires_dependency(self):
        self.assertEqual(route({})["selected_count"],0)
        r=route({"current_product_fact_dependency":True})
        self.assertEqual(len([x for x in r["selected"] if x["learning_id"].startswith("AI-LRN-")]),5)

if __name__=="__main__":
    unittest.main()
