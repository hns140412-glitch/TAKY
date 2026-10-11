#!/usr/bin/env python3
import unittest
from installation_doc_contract import validate_install_doc

class InstallationDocContractTest(unittest.TestCase):
    def good(self):
        return {
          "guide_id":"T","tool_name":"Example","execution_surface":"TERMINAL",
          "primary_action":"documented install command from upstream",
          "fallbacks":["use documented manual package path"],
          "observable_verification":["query installed version","run a harmless capability check"],
          "prohibited_actions":["do not paste secrets into commands"],
          "provenance_refs":["upstream repository","official documentation"],
          "license":{"status":"VERIFIED_AT_SOURCE","source_ref":"upstream license"},
          "credentials_required":False,"success_claim":"READY_TO_VERIFY"
        }
    def test_good(self):
        self.assertEqual(validate_install_doc(self.good()),[])
    def test_surface_required(self):
        x=self.good();x["execution_surface"]="UNKNOWN"
        self.assertIn("INSTALL_EXECUTION_SURFACE_INVALID",validate_install_doc(x))
    def test_license_required(self):
        x=self.good();x["license"]={}
        self.assertIn("INSTALL_LICENSE_EVIDENCE_MISSING",validate_install_doc(x))
    def test_credentials_require_scope_and_no_logging(self):
        x=self.good();x.update({"credentials_required":True})
        f=validate_install_doc(x)
        self.assertIn("INSTALL_CREDENTIAL_SCOPE_MISSING",f)
        self.assertIn("INSTALL_SECRET_LOGGING_GUARD_MISSING",f)

if __name__=="__main__":
    unittest.main()
