import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("character_runtime_coordinator.py")
s=importlib.util.spec_from_file_location("c",P);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

APP={"schema":"TAKY_APP_SCENE_POLICY_ADAPTER_V1","app_id":"HIDE_SEEK","policy_id":"HIDE_SCENE_V1",
"max_visible":2,"max_speaking":1,"role_priority":["CHAPTER_OWNER","MAIN","GUEST","ACTING_CREW","AMBIENT"],
"asset_generation_allowed":False,"unapproved_member_policy":"EXCLUDE","design_gate_required":True,
"runtime_eligibility_required":True,"fallback_scope":"SAME_CHARACTER_APPROVED_ONLY"}

def cand(cid,role="MAIN",eligible=True):
  return {"character_id":cid,"visual_id":"VID-"+cid,"presence_role":role,"relationship_state":"KNOWN",
    "action":"IDLE","dialogue_level":"SHORT","required_roles":["BODY","FACE"],"runtime_eligible":eligible}

def reg(ids):
  return {"characters":[{"character_id":cid,"visual_id":"VID-"+cid,"runtime_source_eligible":True,
    "approved_parts":[
      {"role":"BODY","asset_pointer":f"TAKY-ASSETS:{cid}:BODY:sha","approval_state":"APPROVED","actions":[]},
      {"role":"FACE","asset_pointer":f"TAKY-ASSETS:{cid}:FACE:sha","approval_state":"APPROVED","actions":[]}
    ],
    "fallback":{"character_id":cid,"asset_pointer":f"TAKY-ASSETS:{cid}:BODY:sha"}} for cid in ids]}

class T(unittest.TestCase):
  def test_coordinator_success(self):
    x=c.coordinate(APP,{"scene_id":"s","candidates":[cand("A"),cand("B","GUEST")]},reg(["A","B"]))
    self.assertTrue(x["pass"]);self.assertEqual(2,len(x["render_plans"]))
    self.assertFalse(x["generation_allowed"]);self.assertTrue(x["design_gate_required"])
  def test_partial_when_one_missing_registry(self):
    x=c.coordinate(APP,{"scene_id":"s","candidates":[cand("A"),cand("B","GUEST")]},reg(["A"]))
    self.assertTrue(x["pass"]);self.assertTrue(x["partial_render"]);self.assertEqual(1,len(x["rejected"]))
  def test_all_missing_fails_closed(self):
    x=c.coordinate(APP,{"scene_id":"s","candidates":[cand("A")]},reg([]))
    self.assertFalse(x["pass"]);self.assertEqual("NO_RENDERABLE_CHARACTER",x["error"])
  def test_policy_invalid_blocks(self):
    bad={**APP,"asset_generation_allowed":True}
    x=c.coordinate(bad,{"scene_id":"s","candidates":[cand("A")]},reg(["A"]))
    self.assertFalse(x["pass"]);self.assertEqual("APP_POLICY",x["stage"])
if __name__=="__main__":unittest.main()
