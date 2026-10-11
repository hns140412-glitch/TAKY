#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
from evidence_digest import canonical_json_sha256
from growth_lineage_engine import growth_decision

ROOT=Path(__file__).resolve().parents[1]
BEST=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_CURRENT_BEST_LOCALIZED_FAILURE_BOUNDED_RECOVERY_2026-10-04_R2.json"
EVIDENCE=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_REAL_OUTCOME_EVIDENCE_2026-10-04_R2.json"
APPROVAL=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_HUMAN_PROMOTION_APPROVAL_2026-10-04_R2.json"

class GrowCurrentBestPromotionTest(unittest.TestCase):
    def setUp(self):
        self.best=json.loads(BEST.read_text(encoding="utf-8"))
        self.evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.approval=json.loads(APPROVAL.read_text(encoding="utf-8"))

    def test_human_reviewed_promotion_matches_verified_evidence(self):
        result=growth_decision(self.evidence["candidate"],self.evidence["outcomes"],self.evidence["regressions"])
        self.assertEqual(self.best["status"],"CURRENT_BEST")
        self.assertTrue(self.best["promotion"]["human_approval_observed"])
        self.assertFalse(self.best["promotion"]["automatic_promotion"])
        self.assertEqual(self.best["promotion"]["human_approval_ref"],
                         "CURRENT/TAKY/TAKY_GROW_HUMAN_PROMOTION_APPROVAL_2026-10-04_R2.json")
        self.assertEqual(self.approval["approver_role"],"USER")
        self.assertEqual(self.approval["approval_source"],"CHAT_EXPLICIT_REAFFIRMATION_AFTER_EXACT_R2_EVIDENCE_REF_AND_SHA_DISCLOSURE")
        self.assertEqual(self.approval["strategy_id"],self.best["strategy_id"])
        self.assertEqual(self.approval["target_state"],self.best["promotion"]["target_state"])
        self.assertEqual(
            self.approval["approved_evidence_ref"],
            "CURRENT/TAKY/TAKY_GROW_REAL_OUTCOME_EVIDENCE_2026-10-04_R2.json"
        )
        self.assertEqual(self.approval["approved_evidence_hash_method"],"TAKY_CANONICAL_JSON_DIGEST_V1")
        evidence_sha=canonical_json_sha256(EVIDENCE)
        self.assertEqual(self.approval["approved_evidence_canonical_sha256"],evidence_sha)
        self.assertTrue(self.approval["observed_at"])
        self.assertFalse(self.approval["automatic"])
        self.assertTrue(result["pass"])
        self.assertEqual(result["decision"],"PROMOTION_ELIGIBLE")
        self.assertEqual(result["metrics"]["verified_outcomes"],2)
        self.assertEqual(result["metrics"]["context_diversity"],2)
        self.assertEqual(result["metrics"]["bound_evidence_refs"],2)
        self.assertEqual(result["metrics"]["regression_passes"],1)
        self.assertEqual(result["metrics"]["regression_failures"],0)
        self.assertFalse(result["auto_promote"])
        self.assertTrue(result["human_review_required"])

    def test_evidence_refs_are_bound_to_real_outcomes(self):
        refs=set(self.evidence["candidate"]["evidence_refs"])
        outcome_refs={o["evidence_ref"] for o in self.evidence["outcomes"]}
        self.assertEqual(refs,outcome_refs)
        for outcome in self.evidence["outcomes"]:
            self.assertFalse(outcome["synthetic"])
            self.assertTrue(outcome["run_url"].startswith("https://github.com/"))
            self.assertEqual(len(outcome["head_sha"]),40)
            self.assertTrue(outcome["failure_refs"])

    def test_bounded_policy_and_scope_guards_remain_active(self):
        policy=self.best["bounded_policy"]
        self.assertEqual(policy["max_recovery_attempts"],3)
        self.assertEqual(policy["default_for_unmatched_failures"],"FAIL_FAST")
        self.assertFalse(policy["broad_exception_swallowing"])
        self.assertTrue(self.best["guards"]["hide_visual_qa_counterexample_preserved"])
        self.assertFalse(self.best["guards"]["hide_design_correction_verified"])
        self.assertTrue(self.best["guards"]["functional_ci_does_not_certify_design_parity"])
        for key in ("push","merge","deploy","netlify"):
            self.assertEqual(self.best["guards"][key],"HOLD")

if __name__=="__main__":
    unittest.main()
