#!/usr/bin/env python3
import unittest
from grow_review_gate import classify_candidate,evaluate_queue

def candidate(member_count=3,verified=8):
    return {
        "candidate_id":"GRQ-X",
        "grow_domain":"LEARNING_GROW",
        "event_id":"GLE-X",
        "source_ref":"LEARNING_SYSTEM_AGGREGATE:X",
        "authority":"LEARNING_SYSTEM_GROWTH_CANDIDATE_ONLY",
        "promotion_authorized":False,
        "authority_transfer":False,
        "payload":{
            "scope_kind":"SYSTEM_AGGREGATE",
            "subject":"영어",
            "concept_skill_target":"vocabulary",
            "member_count":member_count,
            "verified_outcome_count":verified
        }
    }

def outcome(ref,ctx,run):
    return {
        "verification_state":"VERIFIED",
        "verification_authority":"SYSTEM_VALIDATOR",
        "context_key":ctx,
        "evidence_ref":ref,
        "workflow_run":run,
    }

def regression(status="PASS",run=900):
    return {
        "status":status,
        "verification_authority":"SYSTEM_REGRESSION_VALIDATOR",
        "workflow_run":run,
    }

class GrowReviewGateTest(unittest.TestCase):
    def test_candidate_contract_violations_force_hold(self):
        cases=[
            ("promotion_authorized",True,"PROMOTION_AUTHORITY_MUST_BE_FALSE"),
            ("authority_transfer",True,"AUTHORITY_TRANSFER_MUST_BE_FALSE"),
        ]
        for key,value,issue in cases:
            with self.subTest(key=key):
                c=candidate()
                c[key]=value
                r=classify_candidate(c,{})
                self.assertEqual(r["review_state"],"HOLD")
                self.assertFalse(r["promotion_gate_invoked"])
                self.assertIn(issue,r["issues"])
        c=candidate()
        c["event_id"]=""
        r=classify_candidate(c,{})
        self.assertEqual(r["review_state"],"HOLD")
        self.assertIn("EVENT_ID_MISSING",r["issues"])

    def test_threshold_hold(self):
        r=classify_candidate(candidate(member_count=2,verified=8),{})
        self.assertEqual(r["review_state"],"HOLD")
        self.assertFalse(r["promotion_gate_invoked"])

    def test_aggregate_only_means_experiment_ready_not_promotion(self):
        r=classify_candidate(candidate(),{})
        self.assertEqual(r["review_state"],"STRATEGY_EXPERIMENT_READY")
        self.assertFalse(r["promotion_gate_invoked"])
        self.assertFalse(r["promotion_authorized"])

    def test_single_strategy_outcome_still_hold(self):
        evidence={
            "target_state":"CURRENT_BEST",
            "evidence_refs":["SYS:E1"],
            "strategy_outcomes":[outcome("SYS:E1","CTX1",101)],
            "regressions":[regression()]
        }
        r=classify_candidate(candidate(),evidence)
        self.assertEqual(r["review_state"],"HOLD")
        self.assertTrue(r["promotion_gate_invoked"])
        self.assertIn("CURRENT_BEST_REQUIRES_REPEATED_VERIFIED_OUTCOMES",r["issues"])

    def test_two_context_verified_clean_regression_is_review_ready_not_promoted(self):
        evidence={
            "target_state":"CURRENT_BEST",
            "evidence_refs":["SYS:E1","SYS:E2"],
            "strategy_outcomes":[
                outcome("SYS:E1","CTX1",101),
                outcome("SYS:E2","CTX2",102)
            ],
            "regressions":[regression()]
        }
        r=classify_candidate(candidate(),evidence)
        self.assertEqual(r["review_state"],"PROMOTION_REVIEW_READY")
        self.assertTrue(r["growth_gate"]["pass"])
        self.assertFalse(r["growth_gate"]["auto_promote"])
        self.assertTrue(r["growth_gate"]["human_review_required"])
        self.assertFalse(r["promotion_authorized"])

    def test_regression_failure_blocks(self):
        evidence={
            "target_state":"CURRENT_BEST",
            "evidence_refs":["SYS:E1","SYS:E2"],
            "strategy_outcomes":[
                outcome("SYS:E1","CTX1",101),
                outcome("SYS:E2","CTX2",102)
            ],
            "regressions":[regression("REGRESSION_FAIL")]
        }
        r=classify_candidate(candidate(),evidence)
        self.assertEqual(r["review_state"],"HOLD")
        self.assertIn("CURRENT_BEST_REGRESSION_NOT_CLEAN",r["issues"])

    def test_design_parity_claim_requires_signoff(self):
        evidence={
            "target_state":"CURRENT_BEST",
            "evidence_refs":["SYS:E1","SYS:E2"],
            "strategy_outcomes":[
                outcome("SYS:E1","CTX1",101),
                outcome("SYS:E2","CTX2",102)
            ],
            "regressions":[regression()],
            "design_parity_claim":True,
        }
        r=classify_candidate(candidate(),evidence)
        self.assertEqual(r["review_state"],"HOLD")
        self.assertIn("CURRENT_BEST_DESIGN_PARITY_REQUIRES_USER_SIGNOFF",r["issues"])
        evidence["design_user_signoff_ref"]="USER_SIGNOFF:ABC"
        r=classify_candidate(candidate(),evidence)
        self.assertEqual(r["review_state"],"PROMOTION_REVIEW_READY")

    def test_queue_summary(self):
        q={"candidates":[candidate(),candidate(member_count=2,verified=3)]}
        r=evaluate_queue(q,{})
        self.assertEqual(r["candidate_count"],2)
        self.assertEqual(r["states"]["STRATEGY_EXPERIMENT_READY"],1)
        self.assertEqual(r["states"]["HOLD"],1)
        self.assertFalse(r["promotion_authorized"])

if __name__=="__main__":
    unittest.main()
