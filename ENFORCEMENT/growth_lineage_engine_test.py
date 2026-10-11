#!/usr/bin/env python3
import unittest
from growth_lineage_engine import compile_lineage, growth_decision, relation

def verified(ref,ctx,run):
    return {
        "verification_state":"VERIFIED",
        "verification_authority":"VALIDATOR",
        "context_key":ctx,
        "evidence_ref":ref,
        "workflow_run":run,
    }

def clean_reg(run=900):
    return {
        "status":"PASS",
        "verification_authority":"REGRESSION_VALIDATOR",
        "workflow_run":run,
    }

class GrowthLineageTest(unittest.TestCase):
    def test_complete_loop_and_typed_relations(self):
        stages=["RAW","INDEX","LEARNING","RELATION","EXECUTION","OUTCOME","GROWTH"]
        nodes=[]
        for i,s in enumerate(stages):
            nodes.append({"node_id":f"N{i}","stage":s,"source_ref":f"E:{i}",
                          "parent_refs":[] if i<2 else [f"N{i-1}"],
                          **({"verification_state":"VERIFIED"} if s=="OUTCOME" else {})})
        rels=[relation(f"N{i}",f"N{i+1}","DERIVED_FROM",[f"E:{i}"]) for i in range(6)]
        result=compile_lineage(nodes,rels)
        self.assertTrue(result["pass"]); self.assertTrue(result["complete_loop"])

    def test_current_best_requires_repeated_diverse_verified_outcomes(self):
        one=[verified("E:1","P1",101)]
        self.assertFalse(growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E:1"]},one,[clean_reg()]
        )["pass"])
        two=one+[verified("E:2","P2",102)]
        result=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E:1","E:2"]},two,[clean_reg()]
        )
        self.assertTrue(result["pass"]); self.assertFalse(result["auto_promote"])
        self.assertTrue(result["human_review_required"])

    def test_confirmed_failure_blocks_current_best(self):
        outcomes=[
            verified("E:1","P1",101),
            verified("E:2","P2",102),
            {"verification_state":"FAILED_CONFIRMED","verification_authority":"VALIDATOR","context_key":"P3","evidence_ref":"E:3"}
        ]
        r=growth_decision(
            {"target_state":"CURRENT_BEST","evidence_refs":["E:1","E:2"]},
            outcomes,[clean_reg()]
        )
        self.assertFalse(r["pass"])
        self.assertIn("CURRENT_BEST_HAS_CONFIRMED_FAILURE",r["blockers"])

    def test_dangling_relation_fails(self):
        nodes=[{"node_id":"A","stage":"RAW","source_ref":"E:A","parent_refs":[]}]
        r=compile_lineage(nodes,[{"src":"A","dst":"MISSING","kind":"SUPPORTS","evidence_refs":["E:A"]}])
        self.assertFalse(r["pass"])
        self.assertIn("RELATION_DANGLING_REF",r["errors"])

if __name__=="__main__":
    unittest.main()
