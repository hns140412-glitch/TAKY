import importlib.util, json, tempfile, unittest
from pathlib import Path

SPEC=importlib.util.spec_from_file_location("dg",Path(__file__).with_name("design_gate_manifest_validate.py"))
dg=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(dg)

class DesignGateManifestTest(unittest.TestCase):
    def base(self):
        return {
          "schema":"TAKY_DESIGN_GATE_V1","rule_id":"TKY-ASSET-001","project":"X",
          "policy":{"current_runtime_must_not_auto_become_golden":True,"approved_reference_required":True,"hash_pin_required":True,"visual_diff_required":True},
          "screens":[{"id":"home","authority_ref":"APPROVED_X_HOME","approved_reference":"design/golden/home.png","approved_sha256":"","snapshot_name":"home.png"}]
        }
    def test_missing_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            e=dg.validate(self.base(),Path(td))
            self.assertTrue(any("APPROVED_REFERENCE_MISSING" in x for x in e))
    def test_pinned_reference_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/"design/golden/home.png"; p.parent.mkdir(parents=True); p.write_bytes(b"approved")
            c=self.base(); c["screens"][0]["approved_sha256"]=dg.sha256(p)
            self.assertEqual([],dg.validate(c,root))
    def test_runtime_cannot_soften_policy(self):
        with tempfile.TemporaryDirectory() as td:
            c=self.base(); c["policy"]["current_runtime_must_not_auto_become_golden"]=False
            e=dg.validate(c,Path(td))
            self.assertTrue(any("CURRENT_RUNTIME_MUST_NOT_AUTO_BECOME_GOLDEN" in x for x in e))
if __name__=="__main__": unittest.main()
