#!/usr/bin/env python3
import unittest
import hashlib
import tempfile
from pathlib import Path
from ai_execution_guard import validate_ai_execution
from taky_gate import validate_record

class AILearningExecutionGuardTest(unittest.TestCase):
    def test_adoption_requires_capability_and_checks(self):
        r={"ai_tool_or_connector_adoption_planned":True,"ai_adoption_assessment":{
            "capability_gap":"source acquisition",
            "overlap_checked":True,"cost_checked":True,"security_checked":True,
            "upstream_identity_verified":True}}
        self.assertEqual(validate_ai_execution(r),[])
        r["ai_adoption_assessment"]["overlap_checked"]=False
        self.assertIn("AI_ADOPTION_GATE_MISSING",validate_ai_execution(r))

    def test_credentials_add_scope_and_isolation(self):
        r={"ai_tool_or_connector_adoption_planned":True,"ai_adoption_assessment":{
            "capability_gap":"private workspace connector","overlap_checked":True,
            "cost_checked":True,"security_checked":True,"upstream_identity_verified":True,
            "credentials_or_private_access_involved":True,
            "credential_scope_defined":True,"permission_boundary_defined":True,
            "isolated_test_planned":True}}
        self.assertEqual(validate_ai_execution(r),[])
        r["ai_adoption_assessment"]["permission_boundary_defined"]=False
        self.assertIn("AI_ADOPTION_GATE_MISSING",validate_ai_execution(r))

    def test_success_needs_observed_evidence(self):
        self.assertIn("AI_OBSERVABLE_SUCCESS_EVIDENCE_MISSING",
            validate_ai_execution({"ai_success_claimed":True}))
        good={"ai_success_claimed":True,"observable_success_evidence_refs":["runtime:test"]}
        self.assertEqual(validate_ai_execution(good),[])
        good["device_or_ui_observation_required"]=True
        self.assertIn("AI_OBSERVABLE_SUCCESS_EVIDENCE_MISSING",validate_ai_execution(good))
        good["device_or_ui_observation_refs"]=["device:screen-1"]
        self.assertEqual(validate_ai_execution(good),[])

    def test_cost_guard_is_enforceable(self):
        good={"ai_autonomous_cost_exposure":True,"ai_cost_guard":{
            "cost_ceiling":10,"iteration_limit":3,"stop_condition":"stop at ceiling",
            "approval_required_before_exceeding":True}}
        self.assertEqual(validate_ai_execution(good),[])
        good["ai_cost_guard"]["iteration_limit"]=0
        self.assertIn("AI_COST_GUARD_MISSING",validate_ai_execution(good))

    def test_review_budget_never_forces_pass(self):
        bad={"ai_review_loop":True,"review_unresolved_material_issues":True,
             "review_round_limit_reached":True,"review_decision":"PASS"}
        self.assertIn("AI_REVIEW_PASS_UNJUSTIFIED",validate_ai_execution(bad))
        bad["review_decision"]="HOLD"
        self.assertEqual(validate_ai_execution(bad),[])

    def test_computer_use_safe_sequence(self):
        good={"ai_computer_use_action":True,"ai_computer_use_guard":{
            "read_only_diagnosis_completed":True,"change_plan_defined":True,
            "bounded_execution_defined":True,"observable_verification_defined":True,
            "rollback_or_recovery_defined":True,"content_inspection_needed":False,
            "metadata_first_used":True,"sensitive_or_destructive_action":False}}
        self.assertEqual(validate_ai_execution(good),[])
        good["ai_computer_use_guard"]["metadata_first_used"]=False
        self.assertIn("AI_COMPUTER_USE_GUARD_MISSING",validate_ai_execution(good))

    def test_ui_done_rejects_fake_image_and_untrusted_reports(self):
        with tempfile.TemporaryDirectory(prefix="taky-ui-completion-") as root:
            directory = Path(root)
            def artifact(name):
                path = directory / name
                path.write_bytes(("proof:" + name).encode("utf-8"))
                return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            evidence = {
                "viewport": {"width": 390, "height": 844},
                "reference": {
                    "approved_id": "approved-sample",
                    "reference_file": artifact("approved.png"),
                    "approval_record": artifact("approval.json"),
                },
                "visual": {
                    "rendered_screenshot": artifact("rendered.png"),
                    "comparison_report": artifact("visual-diff.json"),
                    "passed": True,
                    "layout_compared": True,
                    "color_compared": True,
                    "approved_assets_compared": True,
                },
                "interaction_report": artifact("interaction.json"),
                "data_binding_report": artifact("data-binding.json"),
                "regression_report": artifact("regression.json"),
                "intent_acceptance_report": artifact("acceptance.json"),
                "interaction_passed": True,
                "data_binding_passed": True,
                "regression_passed": True,
                "intent_acceptance_passed": True,
            }
            claim = {"ui_implementation_done_claimed": True, "ui_completion_evidence": evidence}
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_ai_execution(claim))
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(claim))
            inferred = {"deliverable_type": "UI_SCREEN", "status": "DONE"}
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(inferred))
            inferred["ui_completion_evidence"] = evidence
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(inferred))
            evidence["visual"]["color_compared"] = False
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(claim))
            evidence["visual"]["color_compared"] = True
            path = Path(evidence["visual"]["rendered_screenshot"]["path"])
            path.write_bytes(b"changed after evidence receipt")
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(claim))
            path.write_bytes(b"proof:rendered.png")
            evidence["regression_report"] = evidence["interaction_report"]
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(claim))
            evidence["regression_report"] = artifact("regression.json")
            evidence["data_binding_passed"] = False
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_record(claim))
            evidence["data_binding_passed"] = True
            self.assertIn("AI_UI_COMPLETION_EVIDENCE_MISSING", validate_ai_execution(claim))

if __name__=="__main__":
    unittest.main()
