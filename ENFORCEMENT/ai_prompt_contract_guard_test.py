#!/usr/bin/env python3
import unittest
from ai_prompt_contract_guard import validate_ai_prompt_contract

class AIPromptContractGuardTest(unittest.TestCase):
    def base(self):
        return {
          "role":"Focused implementation reviewer",
          "purpose":"Review one bounded artifact against explicit acceptance criteria.",
          "input_refs":["CURRENT/task.json"],
          "constraints":["Do not change unrelated scope"],
          "output_spec":"Return findings and evidence refs.",
          "verification":["Bind findings to artifact revision"],
        }

    def test_base_contract_passes(self):
        self.assertEqual(validate_ai_prompt_contract({
          "ai_prompt_contract_required":True,"ai_prompt_contract":self.base()}),[])

    def test_audience_and_evaluation_are_conditional(self):
        c=self.base(); c.update({"audience_sensitive":True,"quality_request":True})
        f=validate_ai_prompt_contract({"ai_prompt_contract_required":True,"ai_prompt_contract":c})
        self.assertIn("AI_PROMPT_CONTRACT_MISSING",f)
        c["audience"]="beginner user"; c["evaluation_dimensions"]=["accuracy","clarity"]
        self.assertEqual(validate_ai_prompt_contract({"ai_prompt_contract_required":True,"ai_prompt_contract":c}),[])

    def test_role_must_remain_compact(self):
        c=self.base(); c["role"]="x"*241
        self.assertIn("AI_PROMPT_CONTRACT_MISSING",validate_ai_prompt_contract({
          "ai_prompt_contract_required":True,"ai_prompt_contract":c}))

    def test_reusable_skill_needs_specific_triggers(self):
        c=self.base(); c.update({"reusable_skill":True,"trigger_conditions":["*"],"trigger_scope":"BROAD"})
        self.assertIn("AI_PROMPT_CONTRACT_MISSING",validate_ai_prompt_contract({
          "ai_prompt_contract_required":True,"ai_prompt_contract":c}))
        c["trigger_conditions"]=["when a repository repair task has explicit failure evidence"]
        c["trigger_scope"]="SPECIFIC"
        self.assertEqual(validate_ai_prompt_contract({
          "ai_prompt_contract_required":True,"ai_prompt_contract":c}),[])

    def test_install_doc_observability(self):
        good={"command_surface":"terminal","fallback":"manual documented path",
              "observable_verification":"version/status check",
              "prohibited_actions":"no destructive operations",
              "provenance":"official upstream repository",
              "license":"license verified"}
        self.assertEqual(validate_ai_prompt_contract({
          "ai_install_doc_contract_required":True,"ai_install_doc_contract":good}),[])
        bad=dict(good); bad["observable_verification"]=""
        self.assertIn("AI_INSTALL_DOC_OBSERVABILITY_MISSING",validate_ai_prompt_contract({
          "ai_install_doc_contract_required":True,"ai_install_doc_contract":bad}))

if __name__=="__main__":
    unittest.main()
