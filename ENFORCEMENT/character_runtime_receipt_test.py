import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("character_runtime_receipt.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
GOOD={"pass":True,"target_app":"READY_SET","policy_id":"READY","scene_id":"s",
"foreground_character_id":"A","visible_order":["A"],"speaking_order":["A"],"rejected":[],"partial_render":False,
"render_plans":[{"character_id":"A","visual_id":"VID-A","presence_role":"MAIN","relationship_state":"KNOWN",
"action":"IDLE","dialogue_level":"SHORT","asset_pointers":["TAKY-ASSETS:A:BODY:sha"],"fallback_used":False}]}
class T(unittest.TestCase):
  def test_receipt_stable(self):
    a=r.create(GOOD);b=r.create(GOOD);self.assertTrue(a["pass"]);self.assertEqual(a["receipt_sha256"],b["receipt_sha256"])
  def test_pointer_recorded(self):
    x=r.create(GOOD);self.assertEqual(["TAKY-ASSETS:A:BODY:sha"],x["characters"][0]["asset_pointers"])
  def test_generation_never_enabled(self):
    x=r.create(GOOD);self.assertFalse(x["generation_allowed"]);self.assertFalse(x["production_state_mutation_allowed"])
if __name__=="__main__":unittest.main()
