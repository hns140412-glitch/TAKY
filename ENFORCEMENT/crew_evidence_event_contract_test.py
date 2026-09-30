import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("crew_evidence_event_contract.py")
s=importlib.util.spec_from_file_location("e",P);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
GOOD={"schema":"TAKY_CREW_EVIDENCE_EVENT_V1","event_id":"1","type":"SHARED_EPISODE","verified":True,
"evidence_ref":"EV","character_id":"C1","source":"READY_SET","at":"2026-09-30T20:00:00+09:00"}
class T(unittest.TestCase):
 def test_valid(self):self.assertEqual([],e.validate(GOOD))
 def test_unverified_blocked(self):self.assertIn("VERIFIED_REQUIRED",e.validate({**GOOD,"verified":False}))
 def test_relation_projection(self):
  x=e.to_relation_event(GOOD);self.assertTrue(x["pass"]);self.assertEqual("READY_SET",x["event"]["source"])
if __name__=="__main__":unittest.main()
