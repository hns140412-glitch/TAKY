import importlib.util, unittest
from pathlib import Path
P=Path(__file__).with_name("character_behavior_engine.py")
s=importlib.util.spec_from_file_location("cbe",P); cbe=importlib.util.module_from_spec(s); s.loader.exec_module(cbe)
class T(unittest.TestCase):
  def state(self):
    return {"main_character_id":"BELO","mode":"TRACE","characters":[
      {"character_id":"BELO","visual_id":"VID-08","relationship_state":"FAMILIAR","available":True,"recent_count":2},
      {"character_id":"MOCA","visual_id":"VID-09","relationship_state":"KNOWN","available":True,"recent_count":0}
    ]}
  def test_behavior_outputs_semantics_not_asset(self):
    x=cbe.run(self.state());self.assertTrue(x["pass"]);self.assertEqual("READ_BOOK",x["action"])
    self.assertIsNone(x["asset_path"]);self.assertFalse(x["generation_allowed"]);self.assertEqual([],cbe.validate_command(x))
  def test_ambient_is_silent(self):
    st=self.state();st["main_character_id"]=None
    x=cbe.run(st);self.assertEqual("MOCA",x["character_id"]);self.assertEqual("AMBIENT",x["presence_role"]);self.assertEqual("SILENT",x["dialogue_level"])
  def test_chapter_owner_precedes_main(self):
    st=self.state();st["chapter_owner"]="MOCA"
    x=cbe.run(st);self.assertEqual("MOCA",x["character_id"]);self.assertEqual("CHAPTER_OWNER",x["presence_role"])
  def test_asset_leak_is_rejected(self):
    x=cbe.run(self.state());x["asset_path"]="assets/belo.png"
    self.assertIn("BEHAVIOR_ENGINE_SELECTED_ASSET",cbe.validate_command(x))
if __name__=="__main__":unittest.main()
