#!/usr/bin/env python3
import unittest
from ai_reference_projection import classify_ai_record, build_projection, build_learning

class AIReferenceProjectionTest(unittest.TestCase):
    def test_ai_training_notice_only_is_not_ai_operational_reference(self):
        r={"controlled_terms":["AI_TRAINING_PROHIBITION_NOTICE"],"source_family":"OFFICIAL_PUBLIC_EDUCATION_PROVIDER","title":"EBS"}
        self.assertEqual(classify_ai_record(r),[])

    def test_agent_reach_categories(self):
        r={"title":"Agent Reach","source_family":"UPSTREAM_OPEN_SOURCE_TOOL_DOCS","value_statement":"external source acquisition web mining cookie risk agent tool"}
        cats=classify_ai_record(r)
        for x in ("TOOL","AGENT","SOURCE_ACQUISITION","SECURITY"):
            self.assertIn(x,cats)

    def test_prompt_macro_categories(self):
        r={"title":"ChatGPT Astra prompt macro pattern","controlled_terms":["NOT_NATIVE_COMMAND"],"value_statement":"slash prompt command ux cost"}
        cats=classify_ai_record(r)
        self.assertIn("PROMPT",cats); self.assertIn("COST",cats)

    def test_projection_is_non_authoritative(self):
        rows=[{"source_id":"REF-X","title":"Claude plugin workflow","source_family":"AI_TOOL","current_relation":"REFERENCE_ONLY"}]
        from ai_reference_projection import project_record
        p=build_projection([project_record(rows[0])])
        self.assertFalse(p["authoritative"]); self.assertEqual(p["source_count"],1)

    def test_learning_requires_evidence(self):
        from ai_reference_projection import project_record
        rows=[
          project_record({"source_id":"REF-A","title":"AI plugin security","source_family":"AI_TOOL","controlled_terms":["plugin security","supply chain"]}),
          project_record({"source_id":"REF-B","title":"Agent Reach","source_family":"AI_TOOL","value_statement":"source acquisition cookie security"}),
        ]
        p=build_learning(rows)
        self.assertGreaterEqual(p["learning_count"],1)
        self.assertTrue(all(x["evidence_refs"] for x in p["learnings"]))
        self.assertTrue(all(x["canonical_promotion"] is False for x in p["learnings"]))

if __name__=="__main__": unittest.main()


def test_style_signal_taxonomy_projects_as_qa_not_authorship_proof():
    record={
      "source_id":"REF-TEST-STYLE-QA","title":"AI Korean style QA",
      "source_family":"TEST","source_type":"REFERENCE","authority_level":"REFERENCE_ONLY",
      "domain_facets":["ai_orchestration"],
      "controlled_terms":["KOREAN_WRITING_QA","FALSE_POSITIVE_GUARD","NOT_AUTHORSHIP_DETECTOR"],
      "keywords":[],"learning_eligible":True,
      "ai_categories":["ORCHESTRATION"],
    }
    out=build_learning([record])
    row=next(x for x in out["learnings"] if x["learning_id"]=="AI-LRN-STYLE-SIGNAL-NOT-AUTHORSHIP-PROOF")
    assert row["evidence_refs"]==["INDEX:REF-TEST-STYLE-QA"]
    assert row["canonical_promotion"] is False
