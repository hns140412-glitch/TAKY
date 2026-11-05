import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("surface_scene_policy_contract.py")
s=importlib.util.spec_from_file_location("p",P);p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
REG={"app_id":"READY_SET","slots":[
 {"slot_id":"a","surface":"home","allowed_presence_roles":["MAIN"]},
 {"slot_id":"b","surface":"result","allowed_presence_roles":["MAIN"]},
 {"slot_id":"c","surface":"result","allowed_presence_roles":["GUEST"]}
]}
class T(unittest.TestCase):
 def test_derive_from_real_slot_count(self):
  x=p.derive(REG);self.assertTrue(x["pass"]);self.assertEqual(1,x["surfaces"]["home"]["max_visible"]);self.assertEqual(2,x["surfaces"]["result"]["max_visible"])
 def test_cannot_claim_extra_slots(self):
  pol=p.derive(REG)["surfaces"]["home"];pol={**pol,"max_visible":2}
  self.assertIn("MAX_VISIBLE_SLOT_COUNT_MISMATCH",p.validate(pol,REG))
 def test_no_generation_or_slot_creation(self):
  pol=p.derive(REG)["surfaces"]["home"];self.assertFalse(pol["asset_generation_allowed"]);self.assertFalse(pol["creates_ui_slots"])
if __name__=="__main__":unittest.main()
