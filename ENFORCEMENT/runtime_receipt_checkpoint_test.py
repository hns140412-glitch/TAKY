import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("runtime_receipt_checkpoint.py")
s=importlib.util.spec_from_file_location("c",P);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
L=Path(__file__).with_name("runtime_receipt_ledger.py")
ss=importlib.util.spec_from_file_location("l",L);l=importlib.util.module_from_spec(ss);ss.loader.exec_module(l)
class T(unittest.TestCase):
 def build(self,n):
  led={"schema":"TAKY_RUNTIME_RECEIPT_LEDGER_V1","entries":[]}
  for i in range(n):
   led=l.append(led,{"pass":True,"schema":"X","receipt_sha256":f"{i+1:064x}"})["ledger"]
  return led
 def test_checkpoint(self):
  led=self.build(2);cp=c.checkpoint(led,2);self.assertTrue(cp["pass"])
  rec=c.recover(led["entries"],cp);self.assertTrue(rec["pass"]);self.assertEqual(3,rec["resume_from_sequence"])
 def test_interval_not_reached(self):
  self.assertEqual("CHECKPOINT_INTERVAL_NOT_REACHED",c.checkpoint(self.build(1),2)["error"])
 def test_tamper_blocks_recovery(self):
  led=self.build(2);cp=c.checkpoint(led,2);led["entries"][0]["scene_id"]="tamper"
  self.assertEqual("CHECKPOINT_LEDGER_HASH_MISMATCH",c.recover(led["entries"],cp)["error"])
if __name__=="__main__":unittest.main()
