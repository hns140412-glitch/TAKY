import importlib.util,unittest
from pathlib import Path
def load(n,f):
 p=Path(__file__).with_name(f);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load("r","approved_asset_pointer_resolver.py")
g=load("g","design_gate_receipt.py")

class T(unittest.TestCase):
  def test_approved_pointer_and_gate_receipt_chain(self):
    reg={"assets":[{"asset_pointer":"TAKY-ASSETS:A:BODY:sha","asset_id":"A_BODY","visual_id":"VID-A",
      "approval_status":"APPROVED","sha256":"a"*64,"runtime_url":"assets/a.png","producer_pointer":"GUIDE_PIPE:receipt-1"}]}
    asset=r.resolve("TAKY-ASSETS:A:BODY:sha",reg,"VID-A")
    self.assertTrue(asset["pass"])
    gate=g.issue({"app_id":"READY_SET","screen_id":"home","approved_reference_sha256":"b"*64,
      "runtime_render_sha256":"c"*64,"comparison_pass":True,"interaction_gate_pass":True,
      "responsive_gate_pass":True,"asset_integrity_gate_pass":True})
    self.assertTrue(gate["pass"])
    self.assertFalse(asset["generation_allowed"])
  def test_unapproved_pointer_never_reaches_gate_chain(self):
    reg={"assets":[{"asset_pointer":"P","asset_id":"A","visual_id":"VID-A","approval_status":"HOLD",
      "sha256":"a"*64,"runtime_url":"assets/a.png"}]}
    self.assertFalse(r.resolve("P",reg,"VID-A")["pass"])
if __name__=="__main__":unittest.main()
