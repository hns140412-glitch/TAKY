#!/usr/bin/env python3
"""Real failure-pattern regression: similar Drive result is not the requested file.

The original case: Incheon Office of Education 2026-09-01 post lists four
PDF/HWPX attachments; a broad Drive search surfaced unrelated source.html.
This deterministic fixture protects exact-identity lookup; it does not claim
that the four attachment binaries have been downloaded.
"""
import unittest
from mining_index_bridge import query_frontier
from mining_run_orchestrator import orchestrate

MATH="초등 수학과 서논술형 평가 도움자료.pdf"
SCIENCE="초등 과학과 서논술형 평가 도움자료.pdf"
MATH_APPENDIX="[부록] 초등 수학과 서논술형 평가 문항.hwpx"
SCIENCE_APPENDIX="[부록] 초등 과학과 서논술형 평가 문항.hwpx"
WRONG=[{"source_id":"DRIVE-UNRELATED-HTML","canonical_title":"source.html",
        "short_summary":"선생님의 책상 — 교사용 업무 도구",
        "keywords":["초등","평가","서논술형","수학과"],
        "authority_class":"UNKNOWN"}]


class ExactFileRecoveryTests(unittest.TestCase):
    def test_similar_search_hit_cannot_satisfy_exact_filename(self):
        row={"id":"A","kind":"UNKNOWN","question":MATH,
             "expected_source_filename":MATH}
        result=query_frontier([row],WRONG,top_k=5)
        self.assertEqual(result["counts"]["resolved_from_index"],0)
        self.assertEqual(result["counts"]["external_required"],1)
        self.assertEqual(result["trace"][0]["exact_source_filename"],MATH)
        self.assertTrue(result["trace"][0]["exact_identity_match_required"])
        self.assertEqual(result["trace"][0]["qualified_index_hits"],0)
        self.assertIn("SOURCE_IDENTITY_MISMATCH",
                      [r["reason"] for r in result["trace"][0]["rejected_index_candidates"]])

    def test_exact_filename_is_a_candidate_not_retrieved_binary_or_evidence(self):
        row={"id":"A","question":MATH,"expected_source_filename":MATH}
        exact=WRONG+[{"source_id":"FILE-1","canonical_title":"  초등  수학과 서논술형 평가 도움자료.PDF ",
                       "locator":"/somewhere/other-name","authority_class":"OFFICIAL"}]
        out=query_frontier([row],exact,top_k=1)
        self.assertEqual(out["counts"]["resolved_from_index"],1)
        self.assertEqual(out["counts"]["verification_required"],1)
        self.assertFalse(out["trace"][0]["evidence_sufficient"])
        self.assertEqual(out["verification_frontier"][0]["candidate_source_ids"],["FILE-1"])

    def test_orchestrator_preserves_exact_target_and_actionable_gap(self):
        task={"task_family":"ASSESSMENT_SOURCE_ACQUISITION",
              "goal":"recover official math evaluation attachment",
              "unknown":[MATH],"exact_source_targets":[MATH],
              "max_research_depth":"D1"}
        result=orchestrate({"task":task,"memory":{},"index_rows":WRONG})["plan"]
        self.assertEqual(result["search_frontier"][0]["expected_source_filename"],MATH)
        p=result["pending_actions"]["items"][0]
        self.assertEqual(p["classification"],"SOURCE_IDENTITY_MISMATCH")
        self.assertEqual(p["state"],"READY")
        self.assertEqual(p["next_action"]["type"],"SEARCH_EXACT_FILE_ACROSS_PERMITTED_SOURCES")
        self.assertEqual(p["query_plan"]["purpose"],"ACQUIRE_EXACT_FILE")
        self.assertEqual({r["frontier_id"] for r in result["planned_provider_requests"]},{MATH})
        self.assertFalse(result["research_complete_eligible"])
        self.assertFalse(result["operational_research_ready"])

    def test_four_named_attachments_are_not_silently_lost_at_d1_depth(self):
        names=[MATH,SCIENCE,MATH_APPENDIX,SCIENCE_APPENDIX]
        task={"task_family":"ASSESSMENT_SOURCE_ACQUISITION","goal":"acquire four files",
              "unknown":names,"exact_source_targets":names,"max_research_depth":"D1"}
        p=orchestrate({"task":task,"memory":{},"index_rows":WRONG})["plan"]
        self.assertEqual(len(p["search_frontier"]),2)
        self.assertEqual(p["pending_actions"]["counts"]["total"],4)
        self.assertEqual(p["pending_actions"]["counts"]["required_open"],4)
        self.assertEqual(p["pending_actions"]["counts"]["deferred_required"],2)
        self.assertFalse(p["research_complete_eligible"])

    def test_no_filename_target_keeps_normal_general_research(self):
        result=query_frontier([{"id":"Q","question":"초등 평가"}],WRONG)
        self.assertFalse(result["trace"][0]["exact_identity_match_required"])
        self.assertEqual(result["counts"]["resolved_from_index"],1)


if __name__=="__main__": unittest.main()
