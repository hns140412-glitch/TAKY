#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
from growth_lineage_engine import growth_decision

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_REAL_OUTCOME_EVIDENCE_2026-10-04_R2.json"

class GrowRealOutcomeEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(P.read_text(encoding="utf-8"))

    def test_real_outcomes_are_review_eligible_not_auto_promoted(self):
        self.assertFalse(self.d["source_boundary"]["synthetic"])
        self.assertFalse(self.d["source_boundary"]["promotion_authorized"])
        r=growth_decision(self.d["candidate"],self.d["outcomes"],self.d["regressions"])
        self.assertTrue(r["pass"])
        self.assertEqual(r["decision"],"PROMOTION_ELIGIBLE")
        self.assertEqual(r["metrics"]["verified_outcomes"],2)
        self.assertEqual(r["metrics"]["context_diversity"],2)
        self.assertEqual(r["metrics"]["bound_evidence_refs"],2)
        self.assertEqual(r["metrics"]["regression_passes"],1)
        self.assertEqual(self.d["unresolved_confirmed_failures"],[])
        self.assertEqual(r["metrics"]["regression_failures"],0)
        self.assertFalse(r["auto_promote"])
        self.assertTrue(r["human_review_required"])

    def test_regression_run_is_distinct_from_outcome_runs(self):
        outcome_runs={o["workflow_run"] for o in self.d["outcomes"]}
        for regression in self.d["regressions"]:
            self.assertNotIn(regression["workflow_run"],outcome_runs)
            self.assertTrue(regression["distinct_from_outcome_run"])

    def test_design_review_failure_guard_is_preserved(self):
        g=self.d["review_feedback_guard"]
        self.assertEqual(g["classification"],"VISUAL_QA_FAIL_DESPITE_LOGIC_CI_PASS")
        self.assertEqual(g["effect"],"BLOCK_DESIGN_PARITY_PROMOTION_UNTIL_USER_SIGNOFF")
        self.assertTrue(g["correction_ref"])
        self.assertTrue(g["logic_correction_receipt_present"])
        self.assertFalse(g["design_correction_verified"])

if __name__=="__main__":
    unittest.main()
