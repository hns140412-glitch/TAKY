#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("m",ROOT/"TOOLS"/"ARCHIGROW_REGULATORY_COMPILER.py")
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

def rule(**kw):
    x=dict(rule_id="R1",rule_class="ABSOLUTE_CONSTRAINT",source_id="LAW_OPEN_DATA",
      evidence_ref="LAW:123:45",source_as_of="2026-10-04",applicability_status="APPLICABLE",
      criterion="Example evidenced criterion",interpretation="Project-specific interpretation under review",
      design_variables=["setback"],target_project_id="P1",
      applicability_evidence={
        "authority":"PROJECT_REGULATORY_REVIEW","evidence_ref":"REVIEW:P1:R1",
        "decided_at":"2026-10-04T12:00:00+09:00","decision":"APPLICABLE",
        "rule_id":"R1","source_id":"LAW_OPEN_DATA","target_project_id":"P1"
      })
    x.update(kw); return x

class T(unittest.TestCase):
    def test_applicable_rule_compiles_without_feasible_claim(self):
        r=M.compile_rules({"project_id":"P1"},[rule()])
        self.assertTrue(r["ok"]); self.assertEqual(r["path_status"],"CONDITIONAL")
        self.assertFalse(r["feasibility_claim_authorized"])
        self.assertTrue(r["compiled_rules"][0]["usable_as_design_constraint"])
    def test_unverified_rule_holds(self):
        x=rule(applicability_status="UNVERIFIED"); x.pop("applicability_evidence")
        r=M.compile_rules({"project_id":"P1"},[x])
        self.assertTrue(r["ok"]); self.assertFalse(r["compiled_rules"][0]["usable_as_design_constraint"])
    def test_applicable_claim_without_bound_evidence_rejected(self):
        x=rule(); x.pop("applicability_evidence")
        c=M.validate_rule(x)
        self.assertFalse(c["ok"]); self.assertIn("APPLICABILITY_EVIDENCE_REQUIRED",c["issues"])
    def test_applicability_evidence_scope_must_match(self):
        x=rule(); x["applicability_evidence"]={**x["applicability_evidence"],"target_project_id":"P2"}
        c=M.validate_rule(x)
        self.assertFalse(c["ok"]); self.assertIn("APPLICABILITY_EVIDENCE_PROJECT_MISMATCH",c["issues"])
    def test_opportunity_needs_approval_route(self):
        r=M.compile_rules({"project_id":"P1"},[rule(rule_class="OPPORTUNITY_RULE",related_rule_ids=["R0"])])
        self.assertFalse(r["ok"]); self.assertIn("OPPORTUNITY_APPROVAL_ROUTE_REQUIRED",r["rejected"][0]["issues"])
    def test_opportunity_needs_explicit_relation_target(self):
        c=M.validate_rule(rule(rule_class="OPPORTUNITY_RULE",approval_route="OFFICIAL_REVIEW"))
        self.assertFalse(c["ok"]); self.assertIn("OPPORTUNITY_RELATION_TARGET_REQUIRED",c["issues"])
    def test_relation_graph_uses_only_explicit_edges(self):
        base=rule(rule_id="R0")
        base["applicability_evidence"]={**base["applicability_evidence"],"rule_id":"R0"}
        opp=rule(rule_id="R2",rule_class="OPPORTUNITY_RULE",approval_route="OFFICIAL_REVIEW",related_rule_ids=["R0"])
        opp["applicability_evidence"]={**opp["applicability_evidence"],"rule_id":"R2"}
        r=M.compile_rules({"project_id":"P1"},[base,opp])
        self.assertTrue(r["ok"])
        g=M.build_relation_graph(r)
        self.assertTrue(g["ok"]); self.assertEqual(len(g["edges"]),1)
        self.assertEqual(g["edges"][0]["relation"],"OPPORTUNITY_RELATES_TO")
        self.assertFalse(g["edges"][0]["inferred"])
        self.assertFalse(g["feasibility_claim_authorized"])
    def test_relation_target_must_be_compiled(self):
        opp=rule(rule_class="OPPORTUNITY_RULE",approval_route="OFFICIAL_REVIEW",related_rule_ids=["MISSING"])
        r=M.compile_rules({"project_id":"P1"},[opp])
        self.assertTrue(r["ok"])
        g=M.build_relation_graph(r)
        self.assertFalse(g["ok"]); self.assertIn("RELATION_TARGET_NOT_COMPILED:R1:MISSING",g["issues"])
    def test_project_mismatch_rejected(self):
        r=M.compile_rules({"project_id":"P2"},[rule()])
        self.assertFalse(r["ok"]); self.assertIn("TARGET_PROJECT_MISMATCH",r["rejected"][0]["issues"])
    def test_automatic_feasible_forbidden(self):
        c=M.validate_rule(rule(feasible=True))
        self.assertFalse(c["ok"]); self.assertIn("AUTOMATIC_FEASIBLE_FORBIDDEN",c["issues"])
    def test_unregistered_source_rejected(self):
        c=M.validate_rule(rule(source_id="UNKNOWN_SOURCE"))
        self.assertFalse(c["ok"]); self.assertIn("SOURCE_NOT_REGISTERED",c["issues"])
    def test_vworld_not_legal_fact_authority(self):
        c=M.validate_rule(rule(source_id="VWORLD_SPATIAL"))
        self.assertFalse(c["ok"]); self.assertIn("SOURCE_NOT_TARGET_FACT_ELIGIBLE",c["issues"])

if __name__=="__main__": unittest.main()
