import importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).with_name("explorer_crew_runtime_schema_validate.py")
s=importlib.util.spec_from_file_location("v",P);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
S=v.load_specs()
class T(unittest.TestCase):
 def test_runtime_log(self):
  d={"schema":"TAKY_CHARACTER_RUNTIME_LOG_V1","app_id":"READY_SET","scene_id":"s",
     "runtime_receipt_sha256":"a"*64,"binding_receipt_sha256":"b"*64,"design_gate_state":"BLOCKED",
     "activation_allowed":False,"generation_allowed":False,"production_state_mutation_allowed":False,"log_sha256":"c"*64}
  self.assertEqual([],v.validate(d,S["TAKY_CHARACTER_RUNTIME_LOG_V1"]))
 def test_handoff_state_leak(self):
  d={"schema":"TAKY_SPECIALIST_TO_ASSET_REGISTRY_HANDOFF_V1","pipeline_owner":"P","pipeline_receipt_ref":"R",
     "asset_id":"A","visual_id":"VID-A","approval_status":"APPROVED","binary_sha256":"a"*64,
     "runtime_url":"a.png","handoff_sha256":"b"*64,"pipeline_state":"MASK"}
  self.assertIn("FORBIDDEN_FIELD:pipeline_state",v.validate(d,S["TAKY_SPECIALIST_TO_ASSET_REGISTRY_HANDOFF_V1"]))
 def test_current_release_status_schema(self):
  root=Path(__file__).parents[1]
  d=json.loads((root/"CURRENT"/"EXPLORER_CREW_RELEASE_STATUS_CURRENT_V1.json").read_text(encoding="utf8"))
  self.assertEqual([],v.validate(d,S["TAKY_EXPLORER_CREW_RELEASE_GATE_V1"]))
if __name__=="__main__":unittest.main()
