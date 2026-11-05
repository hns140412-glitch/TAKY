#!/usr/bin/env python3
"""Regression of ARCHIGROW_SEMANTIC_PLAN (P7A): explicit-fixture doors/windows on room polygons -> JSON/DXF/HTML, read-back, fail-closed.
Synthetic geometry only (copy of the P6 demo room layout); no statutory, project-data or legal claims. Self-contained, local, no network."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,rel):
    spec=importlib.util.spec_from_file_location(name,ROOT/rel)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
S=load("ARCHIGROW_SEMANTIC_PLAN","TOOLS/ARCHIGROW_SEMANTIC_PLAN.py")
import ezdxf

PID="SYNTHETIC_TOPO_P1"
SRC="384429dcdaa6afddd91e0f0b08745219cc87dfe1a63a06337170c4e0f35f0035"
FLOOR=[[3.0028171,3.0028171],[3.0028171,27.9971829],[36.9971829,27.9971829],[36.9971829,22.0028171],[24.9971829,22.0028171],[24.9971829,8.9971829],[36.9971829,8.9971829],[36.9971829,3.0028171]]
def area(p):
    return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2)
def room(i,p):
    return {"id":i,"polygon":p,"area_m2":area(p)}
def option(strategy,levels,links):
    floors=[{"level":l,"polygon":f} for l,f,_ in levels]
    return {"strategy":strategy,"floors":floors,"program_allocation":{"room_geometry":{"levels":[{"level":l,"rooms":[room(i,p) for i,p in r],"residual":None} for l,_,r in levels],"adjacency":{"links":links}}}}
def lk(a,b,same,m,status):
    return {"a":a,"b":b,"same_level":same,"shared_boundary_m":m,"status":status}
BAL=option("BALANCED",[
    ("L01",FLOOR,[("CORE",[[19.0064238,27.9971829],[3.0028171,27.9971829],[3.0028171,18.6242957],[19.0064238,18.6242957]]),
                  ("LOBBY",[[3.0028171,3.0028171],[9.4042598,3.0028171],[9.4042598,18.6242957],[3.0028171,18.6242957]]),
                  ("RETAIL",[[9.4042598,3.0028171],[19.0064238,3.0028171],[19.0064238,18.6242957],[9.4042598,18.6242957]])]),
    ("L02",FLOOR,[("OFFICE",[[3.0028171,27.9971829],[3.0028171,3.0028171],[15.0055221,3.0028171],[15.0055221,27.9971829]])])],
    [lk("CORE","LOBBY",True,6.401463,"TOUCHING"),lk("CORE","OFFICE",False,0.0,"DIFFERENT_LEVEL_NO_PLAN_CONTACT"),lk("LOBBY","RETAIL",True,15.621499,"TOUCHING")])
SCU=option("SCULPTURAL",[
    ("L01",FLOOR,[("LOBBY",[[13.0050713,3.0028171],[13.0050713,13.0005634],[3.0028171,13.0005634],[3.0028171,3.0028171]]),
                  ("OFFICE",[[36.9971829,22.0028171],[36.9971829,22.0118822],[13.0050713,22.0118822],[13.0050713,3.0028171],[36.9971829,3.0028171],[36.9971829,8.9971829],[24.9971829,8.9971829],[24.9971829,22.0028171]]),
                  ("RETAIL",[[13.0050713,27.9971829],[3.0028171,27.9971829],[3.0028171,13.0005634],[13.0050713,13.0005634]])]),
    ("L02",[[8.4976448,8.1744638],[8.4976448,24.3524949],[21.675676,24.3524949],[21.675676,8.1744638]],
     [("CORE",[[8.4976448,19.5570442],[8.4976448,8.1744638],[21.675676,8.1744638],[21.675676,19.5570442]])])],
    [lk("CORE","LOBBY",False,0.0,"DIFFERENT_LEVEL_NO_PLAN_CONTACT"),lk("CORE","OFFICE",False,0.0,"DIFFERENT_LEVEL_NO_PLAN_CONTACT"),lk("LOBBY","RETAIL",True,10.002274,"TOUCHING")])
MODEL={"schema":"ARCHIGROW_MASSING_RESULT_V1","project_id":PID,"coordinate_units":"m","source_sha256":SRC,"input_source_role":"SYNTHETIC_TEST",
       "rule_source_status":"UNVERIFIED_DEMO","options":[BAL,SCU]}

def fixture(model_sha):
    return {"schema":"ARCHIGROW_SEMANTIC_PLAN_FIXTURE_V1","provenance":{"project_id":PID,"source_sha256":SRC,"model_sha256":model_sha},
     "parameters":{"interior_thickness_m":0.15,"exterior_thickness_m":0.25,"end_margin_m":0.3,"snap_tolerance_m":0.02},
     "strategies":{
      "BALANCED":{"levels":{"L01":{"doors":[{"id":"D_LR","pair":["LOBBY","RETAIL"],"width_m":0.9,"center_offset_m":7.8,"swing_room":"RETAIL","hinge":"start"},
                                            {"id":"D_LC","pair":["CORE","LOBBY"],"width_m":0.9,"center_offset_m":3.2,"swing_room":"CORE","hinge":"end"}],
                                   "windows":[{"id":"W_LW","room":"LOBBY","side":"W","width_m":1.5,"center_offset_m":7.8}]}}},
      "SCULPTURAL":{"levels":{"L01":{"doors":[{"id":"D_LR","pair":["LOBBY","RETAIL"],"width_m":0.9,"center_offset_m":5.0,"swing_room":"RETAIL","hinge":"start"}],
                                     "windows":[{"id":"W_LW","room":"LOBBY","side":"W","width_m":1.5,"center_offset_m":5.0}]}}}}}

class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.dir=Path(cls.tmp.name)
        cls.mpath=cls.write("model.json",MODEL)
        cls.msha=hashlib.sha256(cls.mpath.read_bytes()).hexdigest()
        cls.fx=fixture(cls.msha)
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    @classmethod
    def write(cls,name,obj,raw=None):
        p=cls.dir/name
        p.write_text(raw if raw is not None else json.dumps(obj),encoding="utf-8");return p
    @classmethod
    def go(cls,fx=None,model_path=None,**kw):
        cls.counter=getattr(cls,'counter',0)+1
        fp=cls.write("fx%d.json"%cls.counter,fx if fx is not None else cls.fx)
        out=cls.dir/("out%d"%cls.counter)
        return S.run(str(model_path or cls.mpath),str(fp),str(out),**kw),out

class Happy(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rc,cls.out=cls.go(expect_project=PID)
        cls.plan={s:json.loads((cls.out/("semantic_plan_%s.json"%s)).read_text(encoding="utf-8")) for s in ("BALANCED","SCULPTURAL")}
    def test_pass_and_counts(self):
        self.assertEqual(self.rc["status"],"PASS",self.rc)
        self.assertEqual(self.rc["strategies"]["BALANCED"]["counts"]["doors"],2)
        self.assertEqual(self.rc["strategies"]["SCULPTURAL"]["counts"]["doors"],1)
        self.assertEqual(self.plan["BALANCED"]["metrics"]["windows"],1)
        self.assertEqual(self.rc["dwg"]["status"],"NOT_DONE")
        self.assertEqual(self.rc["html"]["browser_render_verified"],"NOT_CLAIMED_BY_TOOL")
    def test_receipt_shas_match_files(self):
        for s,r in self.rc["strategies"].items():
            for k in ("json","dxf"):
                self.assertEqual(r["outputs"][k]["sha256"],hashlib.sha256((self.out/r["outputs"][k]["file"]).read_bytes()).hexdigest())
        self.assertEqual(self.rc["model"]["sha256"],self.msha)
        self.assertEqual(self.plan["BALANCED"]["source_sha256"],SRC)
    def test_wall_dedup_one_run_per_shared_wall(self):
        L=[x for x in self.plan["BALANCED"]["levels"] if x["level"]=="L01"][0]
        shared=[r for r in L["runs"] if r["class"]=="INTERIOR" and sorted(r["rooms"])==["LOBBY","RETAIL"]]
        self.assertEqual(len(shared),1)
        self.assertAlmostEqual(shared[0]["length_m"],15.6215,3)
        self.assertEqual(len({tuple(map(tuple,s["polygon"])) for s in L["solids"]}),len(L["solids"]))
        for lv in self.plan["BALANCED"]["levels"]:   # no two runs overlap collinearly (checked in the tool; re-derive here)
            keys=[(tuple(r["start"]),tuple(r["end"])) for r in lv["runs"]]
            self.assertEqual(len(keys),len(set(keys)))
    def test_door_gap_width_and_thickness(self):
        L=[x for x in self.plan["BALANCED"]["levels"] if x["level"]=="L01"][0]
        d=[x for x in L["doors"] if x["id"]=="D_LR"][0]
        xs=sorted({p[0] for p in d["gap_polygon"]});ys=sorted({p[1] for p in d["gap_polygon"]})
        self.assertAlmostEqual(ys[-1]-ys[0],0.9,5);self.assertAlmostEqual(xs[-1]-xs[0],0.15,5)   # vertical interior wall
        pieces=sorted([s for s in L["solids"] if s["run"]==d["run"]],key=lambda s:s["polygon"][0][1])
        self.assertEqual(len(pieces),2)
        gap=pieces[1]["polygon"][0][1]-pieces[0]["polygon"][2][1]
        self.assertAlmostEqual(gap,0.9,5)
        self.assertAlmostEqual(pieces[0]["thickness_m"],0.15)
    def test_window_on_exterior_run_only(self):
        L=[x for x in self.plan["BALANCED"]["levels"] if x["level"]=="L01"][0]
        w=L["windows"][0]
        run=[r for r in L["runs"] if r["id"]==w["run"]][0]
        self.assertEqual(run["class"],"EXTERIOR");self.assertEqual(run["thickness_m"],0.25);self.assertEqual(run["rooms"],["LOBBY"])
        self.assertEqual(w["proof"]["run_class"],"EXTERIOR")
    def test_browser_and_dxf_share_geometry(self):
        html=S.html_data((self.out/"semantic_plan_viewer.html").read_text(encoding="utf-8"))
        self.assertEqual(len(html["strategies"]),2)
        for st in html["strategies"]:
            self.assertEqual(st,self.plan[st["strategy"]])
            doc=ezdxf.readfile(str(self.out/("semantic_plan_%s.dxf"%st["strategy"])))
            self.assertEqual(doc.dxfversion,"AC1027");self.assertEqual(doc.header["$INSUNITS"],6)
            dxf={}
            for e in doc.modelspace():
                if e.dxftype()=="LWPOLYLINE" and e.dxf.layer.startswith("WALL_"):
                    dxf[e.get_xdata(S.APPID)[0].value]=[(round(p[0],6),round(p[1],6)) for p in e.get_points("xy")]
            want={s["id"]:[tuple(p) for p in s["polygon"]] for L in st["levels"] for s in L["solids"]}
            self.assertEqual(dxf,want)
            n_open=sum(1 for e in doc.modelspace() if e.dxf.layer.startswith("DOOR_OPENING"))
            self.assertEqual(n_open,st["metrics"]["doors"])
    def test_sculptural_core_stays_unresolved(self):
        c=self.plan["SCULPTURAL"]["connectivity"]
        core=[r for r in c["rooms"] if r["room"]=="CORE"][0]
        self.assertTrue(core["status"].startswith("UNKNOWN"));self.assertEqual(core["accessible"],"NOT_CLAIMED")
        link=[l for l in c["links"] if {l["a"],l["b"]}=={"CORE","LOBBY"}][0]
        self.assertEqual(link["status"],"UNRESOLVED_VERTICAL_LINK_NOT_MODELED")
        self.assertEqual(c["vertical_links"],"NOT_MODELED");self.assertEqual(c["status"],"UNRESOLVED_LINKS_REMAIN")
        self.assertIn(["CORE"],c["door_linked_groups"])
    def test_no_speculative_corridor_or_extra_openings(self):
        for s,p in self.plan.items():
            txt=json.dumps(p).upper()
            self.assertNotIn('"CORRIDOR"',txt)
            for L in p["levels"]:
                if L["level"]!="L01":self.assertEqual((len(L["doors"]),len(L["windows"])),(0,0))
                for r in L["runs"]:
                    if r["class"] in ("ROOM_UNPROGRAMMED","EXTERIOR_UNPROGRAMMED"):self.assertEqual(r["openings"],[])
                if L["unprogrammed"]:self.assertIn("NOT a corridor",L["unprogrammed"]["note"])
    def test_sliver_snap_recorded(self):
        L=[x for x in self.plan["SCULPTURAL"]["levels"] if x["level"]=="L01"][0]
        self.assertEqual(len(L["snaps"]),1);self.assertLess(L["snaps"][0]["distance_m"],0.02)
    def test_fresh_out_dir_required(self):
        with self.assertRaises(S.Hold):
            S.run(str(self.mpath),str(self.dir/"fx1.json"),str(self.out))

class Rejections(Base):
    def mut(self,fn):
        fx=copy.deepcopy(self.fx);fn(fx);return fx
    def reason(self,fx,strategy=None,**kw):
        rc,out=self.go(fx,**kw)
        self.assertEqual(rc["status"],"HOLD")
        if strategy:
            self.assertEqual(rc["strategies"][strategy]["status"],"HOLD");self.assertEqual(rc["strategies"][strategy]["outputs"],{})
            self.assertFalse((out/("semantic_plan_%s.dxf"%strategy)).exists())
            return rc["strategies"][strategy]["reasons"][0]
        return rc["hold_reason"]
    def test_wrong_source_sha(self):
        self.assertEqual(self.reason(self.mut(lambda f:f["provenance"].__setitem__("source_sha256","0"*64))),"FIXTURE_SOURCE_SHA_MISMATCH")
        self.assertEqual(self.reason(self.fx,expect_source_sha="1"*64),"MODEL_SOURCE_SHA_MISMATCH")
    def test_wrong_project_and_tampered_model(self):
        self.assertEqual(self.reason(self.fx,expect_project="OTHER"),"MODEL_PROJECT_MISMATCH")
        m=copy.deepcopy(MODEL);m["rule_source_status"]="TAMPERED_AFTER_FIXTURE"
        p=self.write("tampered.json",m)
        self.assertIn(self.reason(self.fx,model_path=p),("FIXTURE_MODEL_SHA_MISMATCH",))
    def test_false_door_between_non_touching_rooms(self):
        def f(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][0].update(pair=["LOBBY","OFFICE"],swing_room="LOBBY")
        self.assertEqual(self.reason(self.mut(f),"BALANCED"),"DOOR_ROOM_NOT_ON_LEVEL:D_LR:OFFICE")
        def g(x):x["strategies"]["SCULPTURAL"]["levels"]["L01"]["doors"][0].update(pair=["LOBBY","OFFICE"],swing_room="LOBBY")  # touching but no link: allowed only if run exists
        rc,_=self.go(self.mut(g));self.assertEqual(rc["strategies"]["SCULPTURAL"]["status"],"PASS")   # real shared run -> geometry-valid when explicit
        def h(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][0]["pair"]=["CORE","RETAIL"]
        rc,_=self.go(self.mut(h));self.assertEqual(rc["strategies"]["BALANCED"]["status"],"PASS")  # CORE/RETAIL really share y=18.62 (9.6 m)
    def test_nonexistent_room_and_vertical_pair(self):
        def f(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][0].update(pair=["LOBBY","GHOST"],swing_room="LOBBY")
        self.assertEqual(self.reason(self.mut(f),"BALANCED"),"DOOR_ROOM_NOT_ON_LEVEL:D_LR:GHOST")
        def g(x):
            x["strategies"]["SCULPTURAL"]["levels"]["L01"]["doors"][0].update(pair=["CORE","LOBBY"],swing_room="LOBBY")
        self.assertEqual(self.reason(self.mut(g),"SCULPTURAL"),"DOOR_ROOM_NOT_ON_LEVEL:D_LR:CORE")
    def test_invalid_widths_and_overlaps(self):
        def f(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][0]["width_m"]=3.0
        self.assertEqual(self.reason(self.mut(f)),"FIXTURE_DOOR_WIDTH_RANGE:D_LR")
        def g(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][1]["width_m"]=1.5;x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][1]["center_offset_m"]=5.9
        self.assertTrue(self.reason(self.mut(g),"BALANCED").startswith("OPENING_OUTSIDE_SEGMENT"))
    def test_opening_too_close_to_segment_end(self):
        def f(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][1]["center_offset_m"]=0.5
        self.assertTrue(self.reason(self.mut(f),"BALANCED").startswith("OPENING_OUTSIDE_SEGMENT"))
    def test_two_openings_overlap(self):
        def f(x):
            d=x["strategies"]["BALANCED"]["levels"]["L01"]["doors"]
            d.append({"id":"D_LR2","pair":["LOBBY","RETAIL"],"width_m":0.9,"center_offset_m":8.3,"swing_room":"RETAIL","hinge":"end"})
        self.assertTrue(self.reason(self.mut(f),"BALANCED").startswith("OPENING_OVERLAP"))
    def test_window_without_exterior_support(self):
        def f(x):x["strategies"]["BALANCED"]["levels"]["L01"]["windows"][0].update({"room":"LOBBY","side":"E"})
        self.assertEqual(self.reason(self.mut(f),"BALANCED"),"WINDOW_NOT_SUPPORTED:W_LW")
        def g(x):x["strategies"]["BALANCED"]["levels"]["L01"]["windows"][0].update({"room":"RETAIL","side":"E"})  # RETAIL east faces unprogrammed residual, not the outline
        self.assertEqual(self.reason(self.mut(g),"BALANCED"),"WINDOW_NOT_SUPPORTED:W_LW")
    def test_malformed_fixture(self):
        def f(x):x["strategies"]["BALANCED"]["levels"]["L01"]["doors"][0]["extra"]=1
        self.assertEqual(self.reason(self.mut(f)),"FIXTURE_DOOR_KEYS")
        self.assertEqual(self.reason(self.mut(lambda x:x["parameters"].__setitem__("exterior_thickness_m",float("nan")) if False else x["parameters"].__setitem__("exterior_thickness_m",9))),"FIXTURE_PARAMETER_RANGE:exterior_thickness_m")
        self.assertEqual(self.reason(self.mut(lambda x:x["strategies"].__setitem__("GHOST",x["strategies"]["BALANCED"]))),"FIXTURE_STRATEGY_NOT_IN_MODEL:GHOST")
        fp=self.write("dup.json",None,raw='{"schema":"a","schema":"b"}')
        rc=S.run(str(self.mpath),str(fp),str(self.dir/"outdup"));self.assertEqual(rc["hold_reason"],"JSON_DUPLICATE_KEY")
        fp=self.write("nan.json",None,raw='{"schema":NaN}')
        rc=S.run(str(self.mpath),str(fp),str(self.dir/"outnan"));self.assertEqual(rc["hold_reason"],"JSON_NONFINITE")
    def test_missing_strategy_fixture_holds_only_that_strategy(self):
        def f(x):del x["strategies"]["SCULPTURAL"]
        rc,out=self.go(self.mut(f))
        self.assertEqual(rc["strategies"]["BALANCED"]["status"],"PASS");self.assertEqual(rc["strategies"]["SCULPTURAL"]["reasons"],["NO_FIXTURE_FOR_STRATEGY"])
        self.assertEqual(rc["status"],"HOLD")
    def test_readback_detects_tampered_dxf(self):
        rc,out=self.go()
        plan=json.loads((out/"semantic_plan_BALANCED.json").read_text(encoding="utf-8"))
        bad=copy.deepcopy(plan);bad["levels"][0]["doors"].pop()
        checks=S.readback_dxf(str(out/"semantic_plan_BALANCED.dxf"),bad,2,1)
        self.assertTrue(any(not ok for _,ok,_ in checks))
        checks=S.readback_dxf(str(out/"semantic_plan_BALANCED.dxf"),plan,3,1)   # unapproved/missing opening count
        self.assertIn("door_total_equals_fixture",[n for n,ok,_ in checks if not ok])

if __name__=="__main__":
    r=unittest.main(exit=False,verbosity=1).result
    if r.wasSuccessful():print("architecture_semantic_plan: PASS")
    sys.exit(0 if r.wasSuccessful() else 1)
