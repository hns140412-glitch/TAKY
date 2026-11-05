import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("registry_version_contract.py")
s=importlib.util.spec_from_file_location("v",P);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class T(unittest.TestCase):
 def test_upgrade(self):
  x=v.migration_plan({"schema":"X","version":1,"content_sha256":"a"},{"schema":"X","version":2,"content_sha256":"b"})
  self.assertTrue(x["migration_required"]);self.assertTrue(x["rollback_pointer_required"])
 def test_downgrade_block(self):
  self.assertEqual("REGISTRY_DOWNGRADE_FORBIDDEN",v.compare({"schema":"X","version":2},{"schema":"X","version":1})["error"])
 def test_same_version_drift_block(self):
  self.assertEqual("SAME_VERSION_CONTENT_DRIFT",v.compare({"schema":"X","version":1,"content_sha256":"a"},{"schema":"X","version":1,"content_sha256":"b"})["error"])
if __name__=="__main__":unittest.main()
