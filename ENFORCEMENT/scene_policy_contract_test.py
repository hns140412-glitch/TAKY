import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("scene_policy_contract.py")
s=importlib.util.spec_from_file_location("p",P);p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

BASE={"schema":"TAKY_SCENE_POLICY_V1","policy_id":"APP_POLICY","max_visible":3,"max_speaking":1,
"role_priority":["CHAPTER_OWNER","MAIN","GUEST","ACTING_CREW","AMBIENT"],
"allow_asset_generation":False,"design_gate_required":True,
"unapproved_runtime_member_policy":"EXCLUDE","multiple_intervention_policy":"ONE_FOREGROUND_REST_IDLE"}

class T(unittest.TestCase):
  def test_valid(self):self.assertEqual([],p.validate(BASE))
  def test_generation_cannot_be_enabled(self):
    x=dict(BASE);x["allow_asset_generation"]=True
    self.assertIn("ASSET_GENERATION_MUST_BE_FALSE",p.validate(x))
  def test_speakers_cannot_exceed_visible(self):
    x=dict(BASE);x["max_visible"]=1;x["max_speaking"]=2
    self.assertIn("MAX_SPEAKING_INVALID",p.validate(x))
  def test_apply_does_not_choose_creative_values(self):
    r=p.apply({"scene_id":"x","candidates":[]},BASE)
    self.assertTrue(r["pass"]);self.assertEqual(3,r["scene"]["max_visible"]);self.assertEqual(1,r["scene"]["max_speaking"])
if __name__=="__main__":unittest.main()
