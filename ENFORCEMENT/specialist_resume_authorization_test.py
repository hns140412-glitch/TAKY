import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("specialist_resume_authorization.py")
s=importlib.util.spec_from_file_location("a",P);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
D={"pass":True,"action":"RESUME","resume_stage":"CUTOUT"}
class T(unittest.TestCase):
 def test_no_auto_authorization(self):
  x=a.authorize(D,{"approved":False});self.assertTrue(x["pass"]);self.assertFalse(x["authorized"])
 def test_authority_ref_required(self):
  self.assertEqual("AUTHORITY_REF_REQUIRED",a.authorize(D,{"approved":True})["error"])
 def test_authorized_still_no_generation_flag(self):
  x=a.authorize(D,{"approved":True,"authority_ref":"USER_APPROVAL"});self.assertTrue(x["authorized"]);self.assertFalse(x["generation_allowed"])
if __name__=="__main__":unittest.main()
