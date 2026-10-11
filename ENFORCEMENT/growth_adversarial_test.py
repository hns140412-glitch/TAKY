#!/usr/bin/env python3
import unittest
from growth_lineage_engine import compile_lineage,growth_decision

def verified(ref,ctx,run,synthetic=False):
    return {
        "verification_state":"VERIFIED",
        "verification_authority":"VALIDATOR",
        "context_key":ctx,
        "evidence_ref":ref,
        "workflow_run":run,
        "synthetic":synthetic,
    }

def reg(status="PASS",run=900,authority="REGRESSION_VALIDATOR",synthetic=False):
    return {
        "status":status,
        "verification_authority":authority,
        "workflow_run":run,
        "synthetic":synthetic,
    }

def base():
    return [verified("E1","A",101),verified("E2","B",102)]

class GrowthAdversarialTest(unittest.TestCase):
    def test_relation_without_evidence_is_rejected(self):
        nodes=[
          {"node_id":"A","stage":"RAW","source_ref":"SRC:A","parent_refs":[]},
          {"node_id":"B","stage":"INDEX","source_ref":"SRC:B","parent_refs":[]}
        ]
        r=compile_lineage(nodes,[{"src":"A","dst":"B","kind":"SUPPORTS","evidence_refs":[]}])
        self.assertFalse(r["pass"]); self.assertIn("RELATION_EVIDENCE_MISSING",r["errors"])

    def test_single_success_cannot_be_current_best(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1"]},
            [verified("E1","ONE",101)],[reg()]
        )
        self.assertFalse(r["pass"])

    def test_regression_failure_blocks_promotion(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg("REGRESSION_FAIL")]
        )
        self.assertFalse(r["pass"]); self.assertIn("CURRENT_BEST_REGRESSION_NOT_CLEAN",r["blockers"])

    def test_github_failure_conclusion_blocks_promotion(self):
        for status in ("FAILURE","ERROR","CANCELLED","TIMED_OUT"):
            with self.subTest(status=status):
                r=growth_decision(
                    {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
                    base(),[reg(status)]
                )
                self.assertFalse(r["pass"])
                self.assertIn("CURRENT_BEST_REGRESSION_NOT_CLEAN",r["blockers"])

    def test_unrecognized_regression_status_blocks(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg("MYSTERY")]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_REGRESSION_STATUS_UNRECOGNIZED",r["blockers"])

    def test_missing_regression_status_blocks(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg(None)]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_REGRESSION_STATUS_MISSING",r["blockers"])

    def test_current_best_requires_positive_regression_evidence(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_REQUIRES_CLEAN_REGRESSION_EVIDENCE",r["blockers"])

    def test_duplicate_workflow_run_does_not_count_twice(self):
        outcomes=[
          verified("E1","A",101),
          verified("E2","B",101)]
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            outcomes,[reg()]
        )
        self.assertFalse(r["pass"])
        self.assertEqual(r["metrics"]["verified_outcomes"],1)

    def test_truthy_synthetic_outcome_does_not_count(self):
        for value in ("true","mock",1,True):
            with self.subTest(value=value):
                outcomes=[verified("E1","A",101,value),verified("E2","B",102)]
                r=growth_decision(
                    {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
                    outcomes,[reg()]
                )
                self.assertFalse(r["pass"])
                self.assertEqual(r["metrics"]["verified_outcomes"],1)

    def test_missing_outcome_evidence_ref_blocks(self):
        outcomes=[
          {"verification_state":"VERIFIED","verification_authority":"VALIDATOR","context_key":"A","workflow_run":101},
          verified("E2","B",102)]
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E2"]},
            outcomes,[reg()]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_OUTCOME_EVIDENCE_REF_MISSING",r["blockers"])

    def test_bound_evidence_refs_must_cover_candidate_refs(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","MISSING"]},
            base(),[reg()]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_EVIDENCE_REFS_UNBOUND",r["blockers"])

    def test_regression_requires_verification_authority(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg(authority="")]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_REGRESSION_AUTHORITY_MISSING",r["blockers"])

    def test_truthy_synthetic_regression_does_not_count(self):
        for value in ("true","mock",1,True):
            with self.subTest(value=value):
                r=growth_decision(
                    {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
                    base(),[reg(synthetic=value)]
                )
                self.assertFalse(r["pass"])
                self.assertEqual(r["metrics"]["regression_passes"],0)

    def test_regression_requires_workflow_run(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg(run=None)]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_REGRESSION_WORKFLOW_RUN_MISSING",r["blockers"])

    def test_regression_run_cannot_overlap_outcome_run(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg(run=101)]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_REGRESSION_NOT_INDEPENDENT",r["blockers"])

    def test_duplicate_regression_workflow_run_counts_once(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg(run=900),reg(run=900)]
        )
        self.assertTrue(r["pass"])
        self.assertEqual(r["metrics"]["regression_passes"],1)

    def test_conflicting_duplicate_regression_status_blocks(self):
        for regressions in ([reg("PASS",900),reg("FAIL",900)],[reg("FAIL",900),reg("PASS",900)]):
            with self.subTest(regressions=regressions):
                r=growth_decision(
                    {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
                    base(),regressions
                )
                self.assertFalse(r["pass"])
                self.assertIn("CURRENT_BEST_REGRESSION_STATUS_CONFLICT",r["blockers"])
                self.assertEqual(r["metrics"]["regression_status_conflict"],1)

    def test_design_parity_claim_requires_user_signoff(self):
        candidate={
            "target_state":"CURRENT_BEST",
            "evidence_refs":["E1","E2"],
            "design_parity_claim":True,
        }
        r=growth_decision(candidate,base(),[reg()])
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_DESIGN_PARITY_REQUIRES_USER_SIGNOFF",r["blockers"])
        candidate["design_user_signoff_ref"]="USER_SIGNOFF:123"
        self.assertTrue(growth_decision(candidate,base(),[reg()])["pass"])

    def test_unverified_external_claim_cannot_frontier(self):
        r=growth_decision({"target_state":"FRONTIER","evidence_refs":["WEB:X"],"external_evidence_verified":False},[],[])
        self.assertFalse(r["pass"])

    def test_growth_never_auto_promotes(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
            base(),[reg()]
        )
        self.assertTrue(r["pass"]); self.assertFalse(r["auto_promote"])

if __name__=="__main__":
    unittest.main()
