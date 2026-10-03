import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("runtime_eligibility_gate.py")
s=importlib.util.spec_from_file_location("g",P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class T(unittest.TestCase):
  def test_source_lock_not_runtime(self):
    x=g.evaluate({"character_id":"dubi","visual_id":"VID-01","production_state":"SOURCE_LOCK_READY"})
    self.assertTrue(x["source_ready"]);self.assertFalse(x["runtime_eligible"])
  def test_expansion_waiting_not_runtime(self):
    x=g.evaluate({"character_id":"SOLA","visual_id":"VID-07","production_state":"AWAITING_INDEPENDENT_CUTOUT_SHA"})
    self.assertFalse(x["source_ready"]);self.assertFalse(x["runtime_eligible"])
  def test_approved_pointer_is_runtime(self):
    x=g.evaluate({"character_id":"BELO","visual_id":"VID-08","production_state":"APPROVED_RUNTIME_ASSET",
      "approved_asset_pointer":"TAKY-ASSETS:BELO:BODY:sha","approved_asset_sha256":"a"*64,"approval_status":"APPROVED"})
    self.assertTrue(x["runtime_eligible"]);self.assertFalse(x["generation_allowed"])
if __name__=="__main__":unittest.main()
