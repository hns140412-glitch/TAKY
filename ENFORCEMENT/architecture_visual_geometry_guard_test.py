#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("m",ROOT/"TOOLS"/"ARCHIGROW_VISUAL_GEOMETRY_GUARD.py")
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
def snap(**kw):
    x={"project_id":"P1","model_revision":"R1","objects":[{"object_id":"M1","object_type":"MASS","level":"ALL","polygon":[[0,0],[10,0],[10,5],[0,5]],"height":30,"openings":["O1"],"floor_count":10}],"camera":{"eye":[1,2,3]},"material":"white"}
    x.update(kw); return x
class T(unittest.TestCase):
    def test_visual_only_change_passes(self):
        a=snap(); b=snap(camera={"eye":[9,8,7]},material="brick",lighting="sunset")
        r=M.compare(a,b); self.assertTrue(r["ok"]); self.assertEqual(r["base_geometry_sha256"],r["candidate_geometry_sha256"])
    def test_mass_polygon_drift_holds(self):
        b=snap(); b["objects"][0]["polygon"]=[[0,0],[11,0],[11,5],[0,5]]
        r=M.compare(snap(),b); self.assertFalse(r["ok"]); self.assertIn("GEOMETRY_DRIFT:M1:polygon",r["issues"])
    def test_floor_count_drift_holds(self):
        b=snap(); b["objects"][0]["floor_count"]=11
        self.assertFalse(M.compare(snap(),b)["ok"])
    def test_opening_drift_holds(self):
        b=snap(); b["objects"][0]["openings"]=["O2"]
        self.assertFalse(M.compare(snap(),b)["ok"])
    def test_object_set_drift_holds(self):
        b=snap(); b["objects"].append({"object_id":"M2","object_type":"CORE","level":"ALL","polygon":[[1,1],[2,1],[2,2],[1,2]],"height":30,"openings":[],"floor_count":10})
        self.assertIn("OBJECT_SET_DRIFT",M.compare(snap(),b)["issues"])
    def test_project_drift_holds(self):
        self.assertIn("PROJECT_ID_DRIFT",M.compare(snap(),snap(project_id="P2"))["issues"])
if __name__=="__main__": unittest.main()
