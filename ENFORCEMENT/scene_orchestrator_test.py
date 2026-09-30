import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("scene_orchestrator.py")
s=importlib.util.spec_from_file_location("so",P);so=importlib.util.module_from_spec(s);s.loader.exec_module(so)

def c(cid,role,dialogue="SHORT",action="IDLE",recent=0,eligible=True):
  return {"character_id":cid,"visual_id":"VID-"+cid,"presence_role":role,"relationship_state":"KNOWN",
          "dialogue_level":dialogue,"action":action,"required_roles":["BODY","FACE"],"recent_count":recent,"runtime_eligible":eligible}

class T(unittest.TestCase):
  def test_priority(self):
    x=so.orchestrate({"scene_id":"s","candidates":[c("A","AMBIENT"),c("M","MAIN"),c("C","CHAPTER_OWNER")]})
    self.assertEqual(["C","M","A"],x["visible_order"])
  def test_only_one_speaker_default(self):
    x=so.orchestrate({"scene_id":"s","candidates":[c("M","MAIN","COACH"),c("G","GUEST","HINT")]})
    self.assertEqual(["M"],x["speaking_order"]);self.assertEqual("SILENT",x["characters"][1]["dialogue_level"])
  def test_intervention_arbitration(self):
    x=so.orchestrate({"scene_id":"s","candidates":[c("M","MAIN","HINT","POINT"),c("G","GUEST","HINT","USE_RADIO")]})
    self.assertEqual("M",x["foreground_character_id"])
    self.assertEqual("IDLE",x["characters"][1]["action"])
  def test_ineligible_excluded(self):
    x=so.orchestrate({"scene_id":"s","candidates":[c("X","CHAPTER_OWNER",eligible=False),c("M","MAIN")]})
    self.assertEqual(["M"],x["visible_order"])
  def test_no_assets_or_generation(self):
    x=so.orchestrate({"scene_id":"s","candidates":[c("M","MAIN")]})
    self.assertFalse(x["generation_allowed"]);self.assertFalse(x["asset_selection_allowed"]);self.assertTrue(x["design_gate_required"])
if __name__=="__main__":unittest.main()
