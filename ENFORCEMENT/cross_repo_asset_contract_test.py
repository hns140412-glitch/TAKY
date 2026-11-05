import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("cross_repo_asset_contract.py")
s=importlib.util.spec_from_file_location("c",P);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
class T(unittest.TestCase):
 def test_e2e_contract(self):
  x=c.end_to_end();self.assertTrue(x["pass"]);self.assertFalse(x["production_state_crossed_boundary"]);self.assertFalse(x["generation_allowed"])
  self.assertEqual(x["handoff"]["visual_id"],x["resolved"]["visual_id"])
 def test_state_leak_fails(self):
  h=c.specialist_handoff();h["pipeline_state"]="MASK_OPEN"
  self.assertEqual("PRODUCTION_STATE_LEAK",c.to_asset_export(h)["error"])
 def test_visual_id_mismatch_fails(self):
  h=c.specialist_handoff();e=c.to_asset_export(h)
  self.assertEqual("VISUAL_ID_MISMATCH",c.app_resolve(h["asset_pointer"],{"assets":[e["asset"]]},"VID-99")["error"])
if __name__=="__main__":unittest.main()
