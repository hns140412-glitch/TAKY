#!/usr/bin/env python3
import unittest
from ai_prompt_contract import validate_contract

class AIPromptContractTest(unittest.TestCase):
    def good(self):
        return {
          "contract_id":"X","role":"TAKY reference intake executor",
          "purpose":"Process only current semantic delta safely.",
          "audience":"subscription CLI executor",
          "trigger_conditions":["semantic delta count > 0","delta hash changed"],
          "inputs":["delta manifest"],"task_steps":["mine","index","learn"],
          "constraints":["no full queue","no deployment"],
          "output_contract":{"terminal":["PASS","NO_ACTION","HOLD"]},
          "verification":["hash","regression"],
          "bounds":{"max_delta":20},
          "evaluation_dimensions":["authority","scope","duplicates"],
          "required_source_markers":["Hard gates:","PIPELINE_STATUS:"],
        }
    def test_good_contract_and_source(self):
        self.assertEqual(validate_contract(self.good(),"Hard gates:\nPIPELINE_STATUS:"),[])
    def test_broad_trigger_fails(self):
        c=self.good(); c["trigger_conditions"]=["always"]
        self.assertIn("PROMPT_TRIGGER_TOO_BROAD",validate_contract(c,"Hard gates:\nPIPELINE_STATUS:"))
    def test_missing_marker_fails(self):
        self.assertTrue(any(x.startswith("PROMPT_SOURCE_MARKER_MISSING") for x in validate_contract(self.good(),"Hard gates:")))
    def test_role_must_stay_compact(self):
        c=self.good(); c["role"]="x"*181
        self.assertIn("PROMPT_ROLE_MISSING_OR_TOO_BROAD",validate_contract(c,"Hard gates:\nPIPELINE_STATUS:"))

if __name__=="__main__":
    unittest.main()
