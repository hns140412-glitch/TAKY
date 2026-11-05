import importlib.util,unittest,copy
from pathlib import Path
def load(name,file):
 p=Path(__file__).with_name(file);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rg=load("rg","explorer_crew_release_gate.py")
rl=load("rl","runtime_receipt_ledger.py")
cv=load("cv","explorer_crew_contract_registry_validate.py")

class Adversarial(unittest.TestCase):
 def base_release(self):
  return {"schema":"TAKY_EXPLORER_CREW_RELEASE_GATE_V1",
    "gates":{k:{"state":"PASS"} for k in rg.REQUIRED},
    "image_generation_hold":False,"main_merge_authorized":True,"release_approval_authorized":True}

 def test_any_missing_gate_blocks_release(self):
  for gate in rg.REQUIRED:
   x=self.base_release();del x["gates"][gate]
   out=rg.evaluate(x)
   self.assertFalse(out["release_candidate"],gate)
   self.assertIn(gate,out["missing"])

 def test_hold_open_blocked_all_block(self):
  for state in ("HOLD","OPEN","BLOCKED"):
   x=self.base_release();x["gates"]["device_gate"]={"state":state}
   out=rg.evaluate(x)
   self.assertFalse(out["release_candidate"])
   self.assertIn("device_gate",out["blocked"])

 def test_failed_gate_blocks(self):
  x=self.base_release();x["gates"]["interaction_gate"]={"state":"FAIL"}
  out=rg.evaluate(x);self.assertFalse(out["release_candidate"]);self.assertIn("interaction_gate",out["failed"])

 def test_receipt_reorder_breaks_chain(self):
  ledger={"schema":"TAKY_RUNTIME_RECEIPT_LEDGER_V1","entries":[]}
  for i,ch in enumerate(("a","b","c"),1):
   r={"pass":True,"schema":"X","receipt_sha256":ch*64,"scene_id":f"s{i}"}
   ledger=rl.append(ledger,r)["ledger"]
  ledger["entries"][0],ledger["entries"][1]=ledger["entries"][1],ledger["entries"][0]
  self.assertTrue(rl.verify(ledger))

 def test_receipt_delete_middle_breaks_chain(self):
  ledger={"schema":"TAKY_RUNTIME_RECEIPT_LEDGER_V1","entries":[]}
  for ch in ("a","b","c"):
   ledger=rl.append(ledger,{"pass":True,"schema":"X","receipt_sha256":ch*64})["ledger"]
  del ledger["entries"][1]
  self.assertTrue(rl.verify(ledger))

 def test_contract_registry_owner_missing_fails(self):
  import json
  p=Path(__file__).parents[1]/"MASTER"/"EXPLORER_CREW_CONTRACT_REGISTRY_V1.json"
  d=json.loads(p.read_text(encoding="utf8"))
  bad=copy.deepcopy(d);bad["contracts"][0]["owner"]=""
  self.assertTrue(any("OWNER_MISSING" in x for x in cv.validate(bad)))

 def test_contract_registry_consumer_missing_fails(self):
  import json
  p=Path(__file__).parents[1]/"MASTER"/"EXPLORER_CREW_CONTRACT_REGISTRY_V1.json"
  d=json.loads(p.read_text(encoding="utf8"))
  bad=copy.deepcopy(d);bad["contracts"][0]["consumers"]=[]
  self.assertTrue(any("CONSUMERS_MISSING" in x for x in cv.validate(bad)))

if __name__=="__main__":unittest.main()
