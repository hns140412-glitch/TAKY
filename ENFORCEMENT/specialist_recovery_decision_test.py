import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("specialist_recovery_decision.py")
s=importlib.util.spec_from_file_location("d",P);d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class T(unittest.TestCase):
 def test_resume(self):
  x=d.decide({"pass":True,"resume_stage":"CUTOUT","status":"OPEN"},{"pass":True,"resume_stage":"CUTOUT"},"v1")
  self.assertEqual("RESUME",x["action"]);self.assertFalse(x["generation_allowed"])
 def test_disagreement_holds(self):
  x=d.decide({"pass":True,"resume_stage":"CUTOUT","status":"OPEN"},{"pass":True,"resume_stage":"MASK"},"v1")
  self.assertEqual("HOLD",x["action"]);self.assertEqual("v1",x["rollback_pointer"])
 def test_blocked_recovers(self):
  x=d.decide({"pass":True,"resume_stage":"MASK","status":"BLOCKED"},{"pass":True,"resume_stage":"MASK"},"v1")
  self.assertEqual("RECOVER",x["action"])
if __name__=="__main__":unittest.main()
