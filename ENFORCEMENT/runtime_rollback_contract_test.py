import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("runtime_rollback_contract.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class T(unittest.TestCase):
 def test_failed_candidate_keeps_active(self):
  x=r.plan({"pointer":"v1"},{"pointer":"v2"},{"pass":False,"error":"BAD"})
  self.assertEqual("KEEP_ACTIVE",x["action"]);self.assertEqual("v1",x["rollback_pointer"]);self.assertFalse(x["activation_allowed"])
 def test_valid_candidate_promotes_with_rollback(self):
  x=r.plan({"pointer":"v1"},{"pointer":"v2"},{"pass":True})
  self.assertEqual("PROMOTE_CANDIDATE",x["action"]);self.assertEqual("v1",x["rollback_pointer"])
if __name__=="__main__":unittest.main()
