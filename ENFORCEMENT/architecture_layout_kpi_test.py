#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("m",ROOT/"TOOLS"/"ARCHIGROW_LAYOUT_KPI.py")
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

def obj(i,t="UNIT",level="1F",poly=None,scope="GFA",parking=0):
    x={"object_id":i,"object_type":t,"level":level,"polygon":poly or [[0,0],[2,0],[2,2],[0,2]],"area_scope":scope}
    if t=="PARKING": x["parking_count"]=parking
    return x

class T(unittest.TestCase):
    def test_area_and_kpi(self):
        m={"site_polygon":[[0,0],[10,0],[10,10],[0,10]],"objects":[
          obj("U1",poly=[[1,1],[3,1],[3,3],[1,3]]),
          obj("C1","CORE",poly=[[4,1],[6,1],[6,3],[4,3]]),
          obj("P1","PARKING",poly=[[1,5],[4,5],[4,7],[1,7]],scope="NONE",parking=8)]}
        r=M.evaluate(m); self.assertTrue(r["ok"])
        self.assertEqual(r["kpi"]["gfa_area"],8.0); self.assertEqual(r["kpi"]["parking_count"],8)
        self.assertFalse(r["feasibility_claim_authorized"])
    def test_outside_site_holds(self):
        r=M.evaluate({"site_polygon":[[0,0],[5,0],[5,5],[0,5]],"objects":[obj("U1",poly=[[4,4],[6,4],[6,6],[4,6]])]})
        self.assertFalse(r["ok"]); self.assertIn("U1:OUTSIDE_SITE_BOUNDARY",r["issues"])
    def test_overlap_holds(self):
        r=M.evaluate({"site_polygon":[[0,0],[10,0],[10,10],[0,10]],"objects":[
          obj("A",poly=[[1,1],[4,1],[4,4],[1,4]]),obj("B",poly=[[3,3],[5,3],[5,5],[3,5]])]})
        self.assertFalse(r["ok"]); self.assertTrue(any(x.startswith("OVERLAP:") for x in r["issues"]))
    def test_touching_edges_not_overlap(self):
        r=M.evaluate({"site_polygon":[[0,0],[10,0],[10,10],[0,10]],"objects":[
          obj("A",poly=[[1,1],[3,1],[3,3],[1,3]]),obj("B",poly=[[3,1],[5,1],[5,3],[3,3]])]})
        self.assertTrue(r["ok"])
    def test_self_intersection_rejected(self):
        c=M.validate_object(obj("X",poly=[[1,1],[4,4],[1,4],[4,1]]))
        self.assertFalse(c["ok"]); self.assertIn("POLYGON_INVALID",c["issues"])
    def test_duplicate_id_holds(self):
        r=M.evaluate({"site_polygon":[[0,0],[10,0],[10,10],[0,10]],"objects":[
          obj("A",poly=[[1,1],[2,1],[2,2],[1,2]]),obj("A",level="2F",poly=[[3,1],[4,1],[4,2],[3,2]])]})
        self.assertFalse(r["ok"]); self.assertIn("OBJECT_ID_DUPLICATE",r["issues"])

if __name__=="__main__": unittest.main()
