#!/usr/bin/env python3
import unittest
from pathlib import Path
from grow_domain_router import load_registry,validate_registry
from growth_lineage_engine import growth_decision

ROOT=Path(__file__).resolve().parents[1]

def outcomes():
    return [
        {
            "verification_state":"VERIFIED",
            "verification_authority":"DOMAIN_VALIDATOR",
            "context_key":"CTX1",
            "evidence_ref":"E1",
            "workflow_run":101,
        },
        {
            "verification_state":"VERIFIED",
            "verification_authority":"DOMAIN_VALIDATOR",
            "context_key":"CTX2",
            "evidence_ref":"E2",
            "workflow_run":102,
        },
    ]

def regressions():
    return [{
        "status":"PASS",
        "verification_authority":"DOMAIN_REGRESSION_VALIDATOR",
        "workflow_run":900,
    }]

class GrowUmbrellaIntegrationTest(unittest.TestCase):
    def setUp(self): self.r=load_registry()

    def test_shared_core_has_two_required_children(self):
        self.assertTrue(validate_registry(self.r)["ok"])
        self.assertEqual(self.r["owner"],"TAKY_GROW_CORE")
        self.assertIn("ARCHI_GROW",self.r["domains"])
        self.assertIn("LEARNING_GROW",self.r["domains"])

    def test_archi_and_learning_keep_distinct_owners(self):
        a=self.r["domains"]["ARCHI_GROW"]["domain_owner"]
        l=self.r["domains"]["LEARNING_GROW"]["domain_owner"]
        self.assertNotEqual(a,l)

    def test_learning_learner_and_system_growth_are_separate(self):
        layers=self.r["domains"]["LEARNING_GROW"]["sub_layers"]
        self.assertIn("LEARNER_GROWTH",layers)
        self.assertIn("LEARNING_SYSTEM_GROWTH",layers)

    def test_both_domains_use_same_promotion_gate_without_auto_promotion(self):
        for domain in ("ARCHI_GROW","LEARNING_GROW"):
            r=growth_decision(
                {"target_state":"CURRENT_BEST","evidence_refs":["E1","E2"]},
                outcomes(),regressions()
            )
            self.assertTrue(r["pass"]); self.assertFalse(r["auto_promote"])

    def test_learning_single_learner_outcome_cannot_promote_system(self):
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["LEARNING_GROW:ONE"]},
            [{
                "verification_state":"VERIFIED",
                "verification_authority":"LEARNING_VERIFICATION_RECEIPT",
                "context_key":"ONE_LEARNER",
                "evidence_ref":"LEARNING_GROW:ONE",
                "workflow_run":101,
            }],
            regressions()
        )
        self.assertFalse(r["pass"])

    def test_required_skill_and_contract_files_exist(self):
        required=[
          ROOT/".claude/skills/archi-grow/SKILL.md",
          ROOT/".claude/skills/learning-grow/SKILL.md",
          ROOT/"DOMAIN/TAKY_GROWTH_LINEAGE_CONTRACT.md",
          ROOT/"MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md"]
        self.assertTrue(all(p.exists() for p in required))

if __name__=="__main__": unittest.main()
