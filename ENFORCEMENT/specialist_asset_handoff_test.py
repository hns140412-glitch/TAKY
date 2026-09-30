import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("specialist_asset_handoff.py")
s=importlib.util.spec_from_file_location("h",P);h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
GOOD={"pipeline_owner":"GUIDE_CHARACTER_PIPELINE","pipeline_receipt_ref":"R1","asset_id":"A","visual_id":"VID-07",
"approval_status":"APPROVED","binary_sha256":"a"*64,"runtime_url":"assets/a.png","asset_pointer":"TAKY-ASSETS:A"}
class T(unittest.TestCase):
 def test_handoff(self):self.assertTrue(h.create(GOOD)["pass"])
 def test_reject_hold(self):self.assertEqual("NOT_APPROVED",h.create({**GOOD,"approval_status":"HOLD"})["error"])
 def test_no_production_state_leak(self):
  self.assertEqual("PRODUCTION_STATE_LEAK",h.create({**GOOD,"pipeline_state":"MASK_OPEN"})["error"])
if __name__=="__main__":unittest.main()
