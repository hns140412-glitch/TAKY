import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("ui_binding_receipt.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
PLAN={"pass":True,"app_id":"READY_SET","scene_id":"s","surface":"home","assignments":[
 {"slot_id":"home-primary","surface":"home","selector":"#homeGuidePortrait","name_selector":"#homeGuideName","text_selector":"#homeGuideLine",
 "character_id":"A","visual_id":"VID-A","presence_role":"MAIN","action":"IDLE","dialogue_level":"SHORT"}
],"rejected":[],"partial_binding":False}
class T(unittest.TestCase):
  def test_stable_receipt(self):
    a=r.create(PLAN);b=r.create(PLAN);self.assertTrue(a["pass"]);self.assertEqual(a["receipt_sha256"],b["receipt_sha256"])
  def test_selector_recorded(self):
    x=r.create(PLAN);self.assertEqual("#homeGuidePortrait",x["assignments"][0]["selector"])
  def test_no_dom_or_generation_authority(self):
    x=r.create(PLAN);self.assertFalse(x["dom_mutation_allowed"]);self.assertFalse(x["asset_generation_allowed"])
  def test_unstable_selector_blocked(self):
    bad={**PLAN,"assignments":[{**PLAN["assignments"][0],"selector":".dynamic"}]}
    self.assertEqual("UNSTABLE_SELECTOR",r.create(bad)["error"])
if __name__=="__main__":unittest.main()
