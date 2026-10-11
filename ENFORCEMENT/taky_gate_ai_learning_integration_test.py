#!/usr/bin/env python3
import unittest
from taky_gate import validate_record

class TAKYAILearningIntegrationTest(unittest.TestCase):
    def test_taky_gate_blocks_unassessed_tool_adoption(self):
        failures=validate_record({"ai_tool_or_connector_adoption_planned":True})
        self.assertIn("AI_ADOPTION_GATE_MISSING",failures)

    def test_taky_gate_blocks_self_report_only_success(self):
        failures=validate_record({"ai_success_claimed":True})
        self.assertIn("AI_OBSERVABLE_SUCCESS_EVIDENCE_MISSING",failures)

    def test_taky_gate_blocks_unbounded_ai_cost(self):
        failures=validate_record({"ai_autonomous_cost_exposure":True})
        self.assertIn("AI_COST_GUARD_MISSING",failures)

    def test_taky_gate_blocks_forced_review_pass(self):
        failures=validate_record({
            "ai_review_loop":True,
            "review_unresolved_material_issues":True,
            "review_round_limit_reached":True,
            "review_decision":"PASS",
        })
        self.assertIn("AI_REVIEW_PASS_UNJUSTIFIED",failures)

    def test_taky_gate_blocks_unsafe_computer_use(self):
        failures=validate_record({"ai_computer_use_action":True})
        self.assertIn("AI_COMPUTER_USE_GUARD_MISSING",failures)

    def test_all_five_profiles_pass_when_satisfied(self):
        record={
          "ai_tool_or_connector_adoption_planned":True,
          "ai_adoption_assessment":{
            "capability_gap":"verified gap","overlap_checked":True,"cost_checked":True,
            "security_checked":True,"upstream_identity_verified":True,
            "credentials_or_private_access_involved":True,"credential_scope_defined":True,
            "permission_boundary_defined":True,"isolated_test_planned":True,
          },
          "ai_success_claimed":True,
          "observable_success_evidence_refs":["runtime:verified"],
          "device_or_ui_observation_required":True,
          "device_or_ui_observation_refs":["device:verified"],
          "ai_autonomous_cost_exposure":True,
          "ai_cost_guard":{"cost_ceiling":1,"iteration_limit":1,"stop_condition":"stop","approval_required_before_exceeding":True},
          "ai_review_loop":True,"review_unresolved_material_issues":True,
          "review_round_limit_reached":True,"review_decision":"HOLD",
          "ai_computer_use_action":True,
          "ai_computer_use_guard":{
            "read_only_diagnosis_completed":True,"change_plan_defined":True,
            "bounded_execution_defined":True,"observable_verification_defined":True,
            "rollback_or_recovery_defined":True,"content_inspection_needed":False,
            "metadata_first_used":True,"sensitive_or_destructive_action":True,
            "explicit_approval_bound":True,
          },
        }
        failures=validate_record(record)
        for code in [
          "AI_ADOPTION_GATE_MISSING","AI_OBSERVABLE_SUCCESS_EVIDENCE_MISSING",
          "AI_COST_GUARD_MISSING","AI_REVIEW_PASS_UNJUSTIFIED","AI_COMPUTER_USE_GUARD_MISSING"
        ]:
            self.assertNotIn(code,failures)

if __name__=="__main__":
    unittest.main()
