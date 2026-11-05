import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("character_runtime_log.py")
s=importlib.util.spec_from_file_location("l",P);l=importlib.util.module_from_spec(s);s.loader.exec_module(l)
R={"pass":True,"target_app":"READY_SET","scene_id":"s","receipt_sha256":"a"*64,"characters":[],"partial_render":False}
B={"pass":True,"app_id":"READY_SET","scene_id":"s","receipt_sha256":"b"*64,"assignments":[],"partial_binding":False}
G={"pass":True,"app_id":"READY_SET","receipt_sha256":"c"*64}
class T(unittest.TestCase):
 def test_blocked_without_design_gate(self):
  x=l.compose(R,B,None);self.assertTrue(x["pass"]);self.assertFalse(x["activation_allowed"])
 def test_pass_with_design_gate(self):
  x=l.compose(R,B,G);self.assertTrue(x["activation_allowed"]);self.assertEqual("PASS",x["design_gate_state"])
 def test_cross_app_mismatch(self):
  x=l.compose(R,{**B,"app_id":"HIDE_SEEK"},None);self.assertEqual("APP_RECEIPT_MISMATCH",x["error"])
if __name__=="__main__":unittest.main()
