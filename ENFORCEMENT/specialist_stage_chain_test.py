import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("specialist_stage_chain.py")
s=importlib.util.spec_from_file_location("c",P);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
ORDER=["A","B","C"]
class T(unittest.TestCase):
 def test_resume_from_first_missing(self):
  rs=[{"stage_name":"A","stage_receipt_sha256":"a"*64},{"stage_name":"B","stage_receipt_sha256":"b"*64}]
  x=c.resumable_prefix(rs,ORDER);self.assertTrue(x["pass"]);self.assertEqual("C",x["resume_stage"])
 def test_gap_detected(self):
  rs=[{"stage_name":"A","stage_receipt_sha256":"a"*64},{"stage_name":"C","stage_receipt_sha256":"c"*64}]
  x=c.resumable_prefix(rs,ORDER);self.assertTrue(x["pass"]);self.assertEqual("B",x["resume_stage"])
if __name__=="__main__":unittest.main()
