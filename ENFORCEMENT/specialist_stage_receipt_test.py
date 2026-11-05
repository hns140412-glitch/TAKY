import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("specialist_stage_receipt.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class T(unittest.TestCase):
 def test_issue(self):
  x=r.issue("SOURCE_LOCK","GUIDE_PIPE",["manifest"],["a"*64],["b"*64]);self.assertTrue(x["pass"]);self.assertEqual(64,len(x["stage_receipt_sha256"]))
 def test_nonpass_block(self):
  self.assertEqual("ONLY_PASS_CAN_ISSUE_RECEIPT",r.issue("X","P",["e"],[],[],"OPEN")["error"])
 def test_evidence_required(self):
  self.assertEqual("EVIDENCE_REQUIRED",r.issue("X","P",[],[],[])["error"])
if __name__=="__main__":unittest.main()
