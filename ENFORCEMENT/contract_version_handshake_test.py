import importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).with_name("contract_version_handshake.py")
s=importlib.util.spec_from_file_location("h",P);h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
REG=json.loads((Path(__file__).parents[1]/"MASTER"/"EXPLORER_CREW_CONTRACT_REGISTRY_V1.json").read_text(encoding="utf8"))
class T(unittest.TestCase):
 def test_compatible(self):
  d={"schema":"TAKY_CONTRACT_VERSION_HANDSHAKE_V1","app_id":"READY_SET","requires":{"TAKY_UI_BINDING_CONTRACT_V1":1,"TAKY_APP_SCENE_POLICY_ADAPTER_V1":1}}
  self.assertTrue(h.validate(d,REG)["pass"])
 def test_version_mismatch(self):
  d={"schema":"TAKY_CONTRACT_VERSION_HANDSHAKE_V1","app_id":"READY_SET","requires":{"TAKY_UI_BINDING_CONTRACT_V1":99}}
  self.assertFalse(h.validate(d,REG)["pass"])
 def test_missing_contract(self):
  d={"schema":"TAKY_CONTRACT_VERSION_HANDSHAKE_V1","app_id":"READY_SET","requires":{"UNKNOWN":1}}
  self.assertIn("UNKNOWN",h.validate(d,REG)["missing"])
if __name__=="__main__":unittest.main()
