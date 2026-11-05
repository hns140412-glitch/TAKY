import importlib.util,unittest
from pathlib import Path

def load(name,file):
  p=Path(__file__).with_name(file)
  s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

so=load("so","scene_orchestrator.py")
ace=load("ace","asset_composition_contract.py")
rr=load("rr","runtime_renderer_contract.py")

class MultiScene(unittest.TestCase):
  def registry(self):
    chars=[]
    for cid,vid in [("C","VID-C"),("M","VID-M"),("G","VID-G")]:
      chars.append({"character_id":cid,"visual_id":vid,"runtime_source_eligible":True,
        "approved_parts":[
          {"role":"BODY","asset_pointer":f"TAKY-ASSETS:{cid}:BODY:sha","approval_state":"APPROVED","actions":[]},
          {"role":"FACE","asset_pointer":f"TAKY-ASSETS:{cid}:FACE:sha","approval_state":"APPROVED","actions":[]},
          {"role":"ARM","asset_pointer":f"TAKY-ASSETS:{cid}:ARM:sha","approval_state":"APPROVED","actions":["POINT"]},
          {"role":"HAND","asset_pointer":f"TAKY-ASSETS:{cid}:HAND:sha","approval_state":"APPROVED","actions":["POINT"]}
        ],
        "fallback":{"character_id":cid,"asset_pointer":f"TAKY-ASSETS:{cid}:BODY:sha"}})
    return {"characters":chars}
  def candidate(self,cid,vid,role,dialogue,action):
    return {"character_id":cid,"visual_id":vid,"presence_role":role,"relationship_state":"KNOWN",
      "dialogue_level":dialogue,"action":action,
      "required_roles":["BODY","FACE","ARM","HAND"] if action=="POINT" else ["BODY","FACE"],
      "runtime_eligible":True,"recent_count":0}
  def test_scene_to_three_render_plans(self):
    scene=so.orchestrate({"scene_id":"lesson",
      "candidates":[
        self.candidate("C","VID-C","CHAPTER_OWNER","HINT","POINT"),
        self.candidate("M","VID-M","MAIN","COACH","POINT"),
        self.candidate("G","VID-G","GUEST","SHORT","IDLE")
      ]})
    self.assertTrue(scene["pass"])
    self.assertEqual(["C","M","G"],scene["visible_order"])
    self.assertEqual(["C"],scene["speaking_order"])
    self.assertEqual("C",scene["foreground_character_id"])

    plans=[]
    for cmd in scene["characters"]:
      command={**cmd,"pass":True,"generation_allowed":False,"asset_selection_forbidden":True,"asset_path":None}
      comp=ace.resolve(command,self.registry())
      self.assertTrue(comp["pass"])
      plan=rr.render_plan(command,comp)
      self.assertTrue(plan["pass"]);plans.append(plan)
    self.assertEqual(3,len(plans))
    self.assertTrue(all(p["design_gate_required"] for p in plans))
    self.assertTrue(all(not p["asset_generation_allowed"] for p in plans))
  def test_missing_approved_asset_blocks_one_character(self):
    reg=self.registry()
    reg["characters"][2]["runtime_source_eligible"]=False
    scene=so.orchestrate({"scene_id":"lesson","candidates":[self.candidate("G","VID-G","GUEST","SHORT","IDLE")]})
    command={**scene["characters"][0],"pass":True,"generation_allowed":False}
    comp=ace.resolve(command,reg)
    self.assertFalse(comp["pass"]);self.assertEqual("SOURCE_NOT_RUNTIME_ELIGIBLE",comp["error"])
if __name__=="__main__":unittest.main()
