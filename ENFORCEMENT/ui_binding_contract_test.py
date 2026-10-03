import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("ui_binding_contract.py")
s=importlib.util.spec_from_file_location("b",P);b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
REG={"schema":"TAKY_UI_BINDING_CONTRACT_V1","app_id":"HIDE_SEEK","slots":[
 {"slot_id":"primary","surface":"partnerBar","allowed_presence_roles":["MAIN","CHAPTER_OWNER"],"approved_only":True,"design_gate_required":True,"allow_generation":False},
 {"slot_id":"secondary","surface":"scene","allowed_presence_roles":["GUEST","AMBIENT","ACTING_CREW"],"approved_only":True,"design_gate_required":True,"allow_generation":False}
]}
VM={"ok":True,"app_id":"HIDE_SEEK","scene_id":"s","asset_generation_allowed":False,
"characters":[{"character_id":"A","visual_id":"VID-A","presence_role":"MAIN","action":"IDLE","dialogue_level":"SHORT","runtime_eligible":True}]}
class T(unittest.TestCase):
  def test_valid_registry(self):self.assertEqual([],b.validate_registry(REG))
  def test_bind(self):
    x=b.bind(REG,VM);self.assertTrue(x["pass"]);self.assertEqual("primary",x["assignments"][0]["slot_id"]);self.assertFalse(x["dom_mutation_allowed"])
  def test_cross_app_block(self):
    x=b.bind(REG,{**VM,"app_id":"READY_SET"});self.assertEqual("APP_BINDING_MISMATCH",x["error"])
  def test_generation_block(self):
    x=b.bind(REG,{**VM,"asset_generation_allowed":True});self.assertEqual("GENERATION_PATH_FORBIDDEN",x["error"])
if __name__=="__main__":unittest.main()
