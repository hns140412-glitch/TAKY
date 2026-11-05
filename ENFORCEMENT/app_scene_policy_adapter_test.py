import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("app_scene_policy_adapter.py")
s=importlib.util.spec_from_file_location("a",P);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
BASE={"schema":"TAKY_APP_SCENE_POLICY_ADAPTER_V1","app_id":"READY_SET","policy_id":"READY_SCENE_V1",
"max_visible":2,"max_speaking":1,"role_priority":["CHAPTER_OWNER","MAIN","GUEST","ACTING_CREW","AMBIENT"],
"asset_generation_allowed":False,"unapproved_member_policy":"EXCLUDE","design_gate_required":True,
"runtime_eligibility_required":True,"fallback_scope":"SAME_CHARACTER_APPROVED_ONLY"}
class T(unittest.TestCase):
  def test_valid(self):self.assertEqual([],a.validate(BASE))
  def test_no_generation(self):
    x=dict(BASE);x["asset_generation_allowed"]=True
    self.assertIn("ASSET_GENERATION_MUST_BE_FALSE",a.validate(x))
  def test_adapter_output(self):
    x=a.to_scene_policy(BASE);self.assertTrue(x["pass"]);self.assertEqual(2,x["policy"]["max_visible"])
if __name__=="__main__":unittest.main()
