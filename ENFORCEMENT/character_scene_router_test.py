import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("character_scene_router.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
GOOD={"pass":True,"generation_allowed":False,"asset_selection_allowed":False,"scene_id":"x","characters":[]}
class T(unittest.TestCase):
  def test_route(self):
    x=r.route("HIDE_SEEK",GOOD);self.assertTrue(x["pass"]);self.assertEqual("HIDE_SEEK",x["scene_plan"]["target_app"]);self.assertFalse(x["cross_app_broadcast"])
  def test_unknown_app(self):self.assertFalse(r.route("OTHER",GOOD)["pass"])
  def test_generation_block(self):
    x=r.route("READY_SET",{**GOOD,"generation_allowed":True});self.assertEqual("GENERATION_PATH_FORBIDDEN",x["error"])
if __name__=="__main__":unittest.main()
