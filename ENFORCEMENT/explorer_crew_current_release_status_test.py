import importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve()
P=HERE.with_name("explorer_crew_release_gate.py")
s=importlib.util.spec_from_file_location("g",P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
STATUS=HERE.parents[1]/"CURRENT"/"EXPLORER_CREW_RELEASE_STATUS_CURRENT_V1.json"
class T(unittest.TestCase):
 def test_current_must_not_claim_release_ready(self):
  data=json.loads(STATUS.read_text(encoding="utf8"))
  x=g.evaluate(data)
  self.assertTrue(x["pass"])
  self.assertFalse(x["release_candidate"])
  self.assertFalse(x["pwa_ready"])
  self.assertEqual("IMPLEMENTATION_VALIDATED_NOT_RELEASE_READY",x["claim_ceiling"])
  for blocker in ("design_gate","interaction_gate","responsive_gate","device_gate","image_generation_hold","main_merge_authorization","release_approval_authorization"):
   self.assertIn(blocker,x["blocked"])
if __name__=="__main__":unittest.main()
