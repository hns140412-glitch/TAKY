import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("runtime_receipt_ledger.py")
s=importlib.util.spec_from_file_location("l",P);l=importlib.util.module_from_spec(s);s.loader.exec_module(l)
class T(unittest.TestCase):
 def test_append_chain(self):
  ledger={"schema":"TAKY_RUNTIME_RECEIPT_LEDGER_V1","entries":[]}
  r1={"pass":True,"schema":"TAKY_CHARACTER_RUNTIME_LOG_V1","log_sha256":"a"*64,"app_id":"READY_SET","scene_id":"s1"}
  r2={"pass":True,"schema":"TAKY_CHARACTER_RUNTIME_LOG_V1","log_sha256":"b"*64,"app_id":"READY_SET","scene_id":"s2"}
  ledger=l.append(ledger,r1)["ledger"];ledger=l.append(ledger,r2)["ledger"]
  self.assertEqual([],l.verify(ledger));self.assertEqual(2,len(ledger["entries"]))
 def test_duplicate_block(self):
  ledger={"schema":"TAKY_RUNTIME_RECEIPT_LEDGER_V1","entries":[]}
  r={"pass":True,"schema":"X","receipt_sha256":"a"*64}
  ledger=l.append(ledger,r)["ledger"]
  self.assertEqual("DUPLICATE_RECEIPT",l.append(ledger,r)["error"])
 def test_tamper_detected(self):
  ledger={"schema":"TAKY_RUNTIME_RECEIPT_LEDGER_V1","entries":[]}
  r={"pass":True,"schema":"X","receipt_sha256":"a"*64}
  ledger=l.append(ledger,r)["ledger"];ledger["entries"][0]["scene_id"]="tampered"
  self.assertTrue(any("ENTRY_HASH_MISMATCH" in x for x in l.verify(ledger)))
if __name__=="__main__":unittest.main()
