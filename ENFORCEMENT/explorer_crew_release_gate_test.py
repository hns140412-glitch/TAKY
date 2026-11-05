import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("explorer_crew_release_gate.py")
s=importlib.util.spec_from_file_location("g",P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def base():
 return {"schema":"TAKY_EXPLORER_CREW_RELEASE_GATE_V1",
 "gates":{k:{"state":"PASS"} for k in g.REQUIRED},
 "image_generation_hold":False,"main_merge_authorized":True,"release_approval_authorized":True}
class T(unittest.TestCase):
 def test_all_pass(self):
  x=g.evaluate(base());self.assertTrue(x["release_candidate"]);self.assertEqual("RELEASE_CANDIDATE",x["claim_ceiling"])
 def test_design_block(self):
  b=base();b["gates"]["design_gate"]={"state":"BLOCKED"}
  x=g.evaluate(b);self.assertFalse(x["release_candidate"]);self.assertIn("design_gate",x["blocked"])
 def test_image_hold_block(self):
  b=base();b["image_generation_hold"]=True
  x=g.evaluate(b);self.assertFalse(x["pwa_ready"]);self.assertIn("image_generation_hold",x["blocked"])
 def test_no_merge_auth_block(self):
  b=base();b["main_merge_authorized"]=False
  x=g.evaluate(b);self.assertFalse(x["release_candidate"]);self.assertIn("main_merge_authorization",x["blocked"])
if __name__=="__main__":unittest.main()
