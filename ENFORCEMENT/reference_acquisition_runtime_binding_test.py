#!/usr/bin/env python3
import pathlib
import unittest

class AcquisitionRuntimeBindingTest(unittest.TestCase):
    def test_orchestrator_binding_contract(self):
        text=pathlib.Path("runtime_orchestrator.py").read_text(encoding="utf-8")
        required=[
            "from reference_acquisition_adapter import acquire as acquire_reference",
            'reference_acquisition_execute") is True',
            '"DATA/INBOX/ACQUIRED"',
            '"REFERENCE_ACQUISITION_SOURCE_URL_REQUIRED"',
            '"reference_acquisition_result": reference_acquisition_result',
            '"reference_intake_fetch_verified": bool(',
        ]
        for token in required:
            self.assertIn(token,text,token)
        self.assertIn('effective_record["reference_intake_execution"]',text)
        self.assertIn('execute_reference_intake(',text)

if __name__=="__main__":
    unittest.main()
