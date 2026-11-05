import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("approved_asset_pointer_resolver.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
REG={"assets":[{"asset_pointer":"TAKY-ASSETS:A:BODY:sha","asset_id":"A_BODY","visual_id":"VID-A",
"approval_status":"APPROVED","sha256":"a"*64,"runtime_url":"assets/a.png","producer_pointer":"PIPE:1"}]}
class T(unittest.TestCase):
  def test_resolve(self):
    x=r.resolve("TAKY-ASSETS:A:BODY:sha",REG,"VID-A");self.assertTrue(x["pass"]);self.assertFalse(x["generation_allowed"])
  def test_visual_mismatch(self):
    self.assertEqual("VISUAL_ID_MISMATCH",r.resolve("TAKY-ASSETS:A:BODY:sha",REG,"VID-B")["error"])
  def test_unapproved(self):
    bad={"assets":[{**REG["assets"][0],"approval_status":"HOLD"}]}
    self.assertEqual("ASSET_NOT_APPROVED",r.resolve("TAKY-ASSETS:A:BODY:sha",bad,"VID-A")["error"])
if __name__=="__main__":unittest.main()
