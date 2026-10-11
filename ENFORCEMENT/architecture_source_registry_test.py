#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("src",ROOT/"TOOLS"/"ARCHIGROW_SOURCE_REGISTRY.py")
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

class TestArchitectureSourceRegistry(unittest.TestCase):
    def test_registry_valid_and_secret_free(self):
        r=M.load_registry(); self.assertTrue(M.validate(r)["ok"])
        self.assertGreaterEqual(len(r["sources"]),4)
    def test_law_and_building_hub_are_registered_official(self):
        self.assertEqual(M.source("LAW_OPEN_DATA")["authority_status"],"VERIFIED_OFFICIAL")
        self.assertEqual(M.source("BUILDING_HUB_LEDGER")["cost_status"],"FREE")
    def test_vworld_stays_hold_until_direct_spec_recheck(self):
        s=M.source("VWORLD_SPATIAL")
        self.assertFalse(s["target_fact_eligible"])
        self.assertIn("HOLD_",s["adapter_status"])
    def test_target_fact_requires_identity_evidence_effective_date_applicability(self):
        bad=M.qualify_target_fact("BUILDING_HUB_LEDGER")
        self.assertFalse(bad["ok"])
        self.assertIn("TARGET_PROJECT_ID_REQUIRED",bad["blockers"])
        good=M.qualify_target_fact("BUILDING_HUB_LEDGER",target_project_id="P-1",
            evidence_ref="BUILDING_HUB:LEDGER:REV1",observed_as_of="2026-10-04",
            applicability_status="TARGET_IDENTITY_MATCHED")
        self.assertTrue(good["ok"])
    def test_official_web_view_can_be_evidence_but_not_api_claim(self):
        s=M.source("LAND_USE_EUM")
        self.assertEqual(s["adapter_status"],"MANUAL_OR_BROWSER_EVIDENCE_ONLY")
        good=M.qualify_target_fact("LAND_USE_EUM",target_project_id="P-1",
            evidence_ref="EUM:PNU:REV1",observed_as_of="2026-10-04",applicability_status="APPLICABLE")
        self.assertTrue(good["ok"])

if __name__=="__main__": unittest.main()
