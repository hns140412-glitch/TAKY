import importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).with_name("explorer_crew_contract_registry_validate.py")
s=importlib.util.spec_from_file_location("v",P);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
REG=Path(__file__).parents[1]/"MASTER"/"EXPLORER_CREW_CONTRACT_REGISTRY_V1.json"
class T(unittest.TestCase):
 def test_registry(self):self.assertEqual([],v.validate(json.loads(REG.read_text(encoding="utf8"))))
 def test_duplicate(self):
  d=json.loads(REG.read_text(encoding="utf8"));d["contracts"].append(dict(d["contracts"][0]))
  self.assertTrue(any("DUPLICATE" in x for x in v.validate(d)))
if __name__=="__main__":unittest.main()
