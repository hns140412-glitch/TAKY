import importlib.util,json,copy,unittest
from pathlib import Path
P=Path(__file__).with_name("explorer_crew_current_claim_guard.py")
s=importlib.util.spec_from_file_location("g",P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
ROOT=Path(__file__).parents[1]
CUR=json.loads((ROOT/"CURRENT"/"EXPLORER_CREW_RUNTIME_IMPLEMENTATION_CURRENT_V1.json").read_text(encoding="utf8"))
REL=json.loads((ROOT/"CURRENT"/"EXPLORER_CREW_RELEASE_STATUS_CURRENT_V1.json").read_text(encoding="utf8"))
class T(unittest.TestCase):
 def test_current_claims_are_bounded(self):
  self.assertEqual([],g.validate(CUR,REL))
 def test_release_overclaim_is_blocked(self):
  c=copy.deepcopy(CUR);c["fake_status"]="RELEASE_READY"
  self.assertTrue(any("OVERCLAIM" in x for x in g.validate(c,REL)))
 def test_logic_hold_cannot_enable_generation(self):
  c=copy.deepcopy(CUR);c["execution_mode"]["asset_generation_allowed"]=True
  self.assertIn("LOGIC_ONLY_HOLD_GENERATION_MUST_BE_FALSE",g.validate(c,REL))
if __name__=="__main__":unittest.main()
