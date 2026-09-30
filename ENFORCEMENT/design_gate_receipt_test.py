import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("design_gate_receipt.py")
s=importlib.util.spec_from_file_location("g",P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
GOOD={"app_id":"READY_SET","screen_id":"home","approved_reference_sha256":"a"*64,"runtime_render_sha256":"b"*64,
"comparison_pass":True,"interaction_gate_pass":True,"responsive_gate_pass":True,"asset_integrity_gate_pass":True,
"comparison_score":0.1,"threshold":0.18}
class T(unittest.TestCase):
  def test_issue(self):
    x=g.issue(GOOD);self.assertTrue(x["pass"]);self.assertEqual(64,len(x["receipt_sha256"]))
  def test_visual_fail(self):
    x=g.issue({**GOOD,"comparison_pass":False});self.assertEqual("VISUAL_COMPARISON_FAILED",x["error"])
  def test_subgate_fail(self):
    x=g.issue({**GOOD,"responsive_gate_pass":False});self.assertEqual("SUBGATE_NOT_PASS",x["error"])
if __name__=="__main__":unittest.main()
