#!/usr/bin/env python3
"""Regression of ARCHIGROW_MASSING_DXF: massing room_geometry -> native DXF, read-back and area-consumer roundtrip.
Synthetic geometry only; no statutory, project-data or legal claims. Self-contained, local, no network."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,rel):
    spec=importlib.util.spec_from_file_location(name,ROOT/rel)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
D=load("ARCHIGROW_MASSING_DXF","TOOLS/ARCHIGROW_MASSING_DXF.py")
TOOL=ROOT/"TOOLS"/"ARCHIGROW_MASSING_DXF.py"
PID="SYNTHETIC_MASSING_DXF_TEST"
GEO_PYTHON=ROOT.parent/"TAKY_AI_WORKBENCH"/".venv_archigrow_geo"/"Scripts"/"python.exe"

def rect(x0,y0,x1,y1):
    return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
def area(p):
    return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2)
def room(rid,poly):
    return {"id":rid,"polygon":poly,"area_m2":area(poly)}
def level(name,floor,rooms,residual=None):
    row={"level":name,"floor_area_m2":area(floor),"rooms":[room(i,p) for i,p in rooms],"residual":None}
    if residual:row["residual"]={"kind":"UNPROGRAMMED_NOT_CORRIDOR","polygon":residual,"area_m2":area(residual)}
    return row
def option(strategy,floors):
    """floors: [(level, floor_polygon, rooms, residual)] -> option with program_allocation.room_geometry."""
    return {"strategy":strategy,"floors":[{"level":l,"polygon":f,"area_m2":area(f)} for l,f,_,_ in floors],
            "layout_model":{"project_id":PID},
            "program_allocation":{"room_geometry":{"representation":"GEOMETRICAL_DRAFT_2D_PARTITION_NOT_CODE_COMPLIANCE",
                "mode":"POLYGON_PARTITION_V1","project_id":PID,"source_status":"USER_EXPLICIT_INPUT_UNVERIFIED",
                "building_code_compliance":False,"levels":[level(l,f,r,res) for l,f,r,res in floors]}}}

L_SHAPE=[[0,0],[20,0],[20,10],[10,10],[10,20],[0,20]]  # concave, 300 m2
def result():
    rect_opt=option("BALANCED",[("L01",rect(0,0,20,10),[("A",rect(0,0,8,10)),("B",rect(8,0,14,10))],rect(14,0,20,10)),
                                ("L02",rect(0,0,20,5),[("C",rect(0,0,10,5))],rect(10,0,20,5))])
    concave_opt=option("SCULPTURAL",[("L01",L_SHAPE,[("R1",rect(0,0,10,10)),("R2",rect(10,0,20,10)),("R3",rect(0,10,10,20))],None),
                                     ("L02",rect(0,0,10,10),[("R4",rect(0,0,10,6))],rect(0,6,10,10))])
    return {"schema":"ARCHIGROW_MASSING_RESULT_V1","project_id":PID,"source_sha256":"ab"*32,"coordinate_units":"m",
            "options":[rect_opt,concave_opt]}

def rg(r,i=0):
    return r["options"][i]["program_allocation"]["room_geometry"]

class MassingDxfTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def run_build(self,r,name="out",expect=None,raw=None):
        src=self.dir/(name+"_result.json")
        src.write_text(raw if raw is not None else json.dumps(r),encoding="utf-8")
        return D.build(src,self.dir/name,expect),self.dir/name
    def assert_hold(self,r,code,**kw):
        receipt,out=self.run_build(r,**kw)
        self.assertEqual(receipt["status"],"HOLD",receipt)
        self.assertTrue(receipt["failure_class"].startswith(code),receipt["failure_class"])
        self.assertEqual(receipt["options"],[])
        self.assertEqual(sorted(p.name for p in out.iterdir()),["massing_dxf_receipt.json"],"partial export left behind")

    def test_cli_roundtrip_two_options_rect_and_concave(self):
        src=self.dir/"massing_result.json";src.write_text(json.dumps(result()),encoding="utf-8")
        p=subprocess.run([sys.executable,str(TOOL),str(src),"--out-dir",str(self.dir/"o"),"--expect-project",PID],capture_output=True,text=True,timeout=60)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        r=json.loads((self.dir/"o"/"massing_dxf_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(r["status"],"PASS");self.assertEqual(r["legal_status"],"NOT_VERIFIED")
        self.assertEqual(r["inputs"][0]["sha256"],D.sha(src));self.assertEqual(r["source_sha256"],"ab"*32)
        self.assertIn("not a portfolio",r["limitations"][-1])
        self.assertEqual([o["strategy"] for o in r["options"]],["BALANCED","SCULPTURAL"])
        b,s=r["options"]
        self.assertEqual(b["layer_entity_counts"],{"BALANCED_L01_ENVELOPE":1,"BALANCED_L01_PROGRAM":2,"BALANCED_L01_UNPROGRAMMED":1,
                                                   "BALANCED_L02_ENVELOPE":1,"BALANCED_L02_PROGRAM":1,"BALANCED_L02_UNPROGRAMMED":1})
        self.assertEqual(s["layer_entity_counts"],{"SCULPTURAL_L01_ENVELOPE":1,"SCULPTURAL_L01_PROGRAM":3,
                                                   "SCULPTURAL_L02_ENVELOPE":1,"SCULPTURAL_L02_PROGRAM":1,"SCULPTURAL_L02_UNPROGRAMMED":1})
        self.assertEqual((b["entity_count"],s["entity_count"]),(7,7))
        tot={(t["level"],t["scope"]):t["area_m2"] for t in s["totals"]}
        self.assertEqual(tot[("SCULPTURAL_L01","ENVELOPE")],300.0);self.assertEqual(tot[("SCULPTURAL_L01","PROGRAM")],300.0)
        self.assertNotIn(("SCULPTURAL_L01","UNPROGRAMMED"),tot)
        self.assertEqual(tot[("SCULPTURAL_L02","UNPROGRAMMED")],40.0)
        for o in r["options"]:
            self.assertEqual(o["area_stage_receipt"]["status"],"PASS")
            self.assertEqual(o["dxf"]["sha256"],D.sha(o["dxf"]["ref"]));self.assertEqual(o["mapping"]["sha256"],D.sha(o["mapping"]["ref"]))
            self.assertEqual(o["area_stage_receipt"]["sha256"],D.sha(o["area_stage_receipt"]["ref"]))
        # independent files, each strategy only draws itself (no overlapping strategies in one drawing)
        import ezdxf
        for o in r["options"]:
            layers={e.dxf.layer for e in ezdxf.readfile(o["dxf"]["ref"]).modelspace()}
            self.assertTrue(all(l.startswith(o["strategy"]+"_") for l in layers))

    def test_existing_area_consumer_rerun_and_mapping_shape(self):
        r,out=self.run_build(result())
        self.assertEqual(r["status"],"PASS")
        o=r["options"][0]
        mapping=json.loads(Path(o["mapping"]["ref"]).read_text(encoding="utf-8"))
        self.assertEqual(mapping["layers"]["BALANCED_L01_PROGRAM"],{"level":"BALANCED_L01","scope":"PROGRAM","operation":"ADD"})
        self.assertEqual(mapping["layers"]["BALANCED_L01_ENVELOPE"]["scope"],"ENVELOPE")
        self.assertEqual(mapping["project_id"],PID)
        ov=D.AREA.export(o["dxf"]["ref"],o["mapping"]["ref"],self.dir/"again","ezdxf")
        self.assertEqual(ov["issues"],[]);self.assertEqual(ov["legal_status"],"NOT_VERIFIED")
        self.assertEqual(json.loads((self.dir/"again"/"stage_receipt.json").read_text(encoding="utf-8"))["status"],"PASS")
        self.assertEqual(ov["drawing_insunits"],6)

    def test_dxf_native_properties_and_xdata_room_ids(self):
        import ezdxf
        r,out=self.run_build(result())
        doc=ezdxf.readfile(r["options"][0]["dxf"]["ref"])
        self.assertEqual(doc.dxfversion,"AC1027");self.assertEqual(doc.header["$INSUNITS"],6)
        self.assertEqual(len(doc.audit().errors),0)
        prog={}
        for e in doc.modelspace():
            self.assertEqual(e.dxftype(),"LWPOLYLINE");self.assertTrue(e.closed)
            xd=dict(v[1].split("=",1) for v in e.get_xdata("ARCHIGROW"))
            self.assertEqual(xd["LEGAL_AREA_CLASS"],"NONE")
            if xd["AREA_QA_SCOPE"]=="PROGRAM":prog.setdefault(e.dxf.layer,[]).append(xd["DESIGN_ID"])
            if xd["AREA_QA_SCOPE"]=="UNPROGRAMMED":self.assertEqual(xd["DESIGN_LABEL"],"UNPROGRAMMED_NOT_CORRIDOR")
        self.assertEqual(prog,{"BALANCED_L01_PROGRAM":["A","B"],"BALANCED_L02_PROGRAM":["C"]})

    def test_repeatable_overwrite_of_generator_owned_dir(self):
        a,out=self.run_build(result());b,_=self.run_build(result())
        self.assertEqual((a["status"],b["status"]),("PASS","PASS"))

    def test_foreign_file_in_output_dir_blocks_and_is_preserved(self):
        keep=self.dir/"out"/"BALANCED";keep.mkdir(parents=True);(keep/"user_notes.txt").write_text("keep",encoding="utf-8")
        receipt,out=self.run_build(result())
        self.assertEqual(receipt["status"],"HOLD");self.assertTrue(receipt["failure_class"].startswith("OUTPUT_DIR_NOT_GENERATOR_OWNED"))
        self.assertEqual((keep/"user_notes.txt").read_text(encoding="utf-8"),"keep")
        self.assertFalse((out/"SCULPTURAL").exists())

    def test_missing_provenance_and_schema(self):
        r=result();del r["source_sha256"];self.assert_hold(r,"SOURCE_SHA256_MISSING_OR_INVALID",name="a")
        r=result();r["source_sha256"]="xyz";self.assert_hold(r,"SOURCE_SHA256_MISSING_OR_INVALID",name="b")
        r=result();r["schema"]="OTHER";self.assert_hold(r,"SCHEMA_UNSUPPORTED",name="c")
        r=result();r["project_id"]="";self.assert_hold(r,"PROJECT_ID_REQUIRED",name="d")
        r=result();del rg(r)["source_status"];self.assert_hold(r,"ROOM_GEOMETRY_PROVENANCE_MISSING",name="e")
        self.assert_hold(None,"RESULT_JSON_UNREADABLE",name="f",raw="{not json")

    def test_project_mismatch(self):
        self.assert_hold(result(),"PROJECT_MISMATCH",expect="OTHER_PROJECT",name="a")
        r=result();rg(r,1)["project_id"]="OTHER";self.assert_hold(r,"ROOM_GEOMETRY_PROJECT_MISMATCH",name="b")

    def test_no_rooms(self):
        r=result();del r["options"][1]["program_allocation"];self.assert_hold(r,"ROOM_GEOMETRY_MISSING:SCULPTURAL")
        r=result();rg(r)["levels"][0]["rooms"]=[];self.assert_hold(r,"NO_ROOMS",name="b")
        r=result();rg(r)["levels"]=[];self.assert_hold(r,"NO_ROOM_LEVELS",name="c")

    def test_no_law_assertion(self):
        r=result();rg(r)["building_code_compliance"]=True
        self.assert_hold(r,"BUILDING_CODE_CLAIM_NOT_ALLOWED")

    def test_malformed_polygons(self):
        bow=[[0,0],[8,10],[8,0],[0,10]]
        r=result();rg(r)["levels"][0]["rooms"][0]["polygon"]=bow;self.assert_hold(r,"ROOM_POLYGON_INVALID:A",name="a")
        r=result();rg(r)["levels"][0]["rooms"][0]["polygon"]=[[0,0],[1,1]];self.assert_hold(r,"ROOM_POLYGON_INVALID:A",name="b")
        r=result();rg(r)["levels"][0]["rooms"][0]["polygon"]=[[0,0],[8,"x"],[8,10]];self.assert_hold(r,"ROOM_POLYGON_INVALID:A",name="c")
        r=result();rg(r)["levels"][0]["rooms"][0]["polygon"]=rect(0,0,8,10)+[[0,0]];self.assert_hold(r,"ROOM_POLYGON_INVALID:A",name="d")
        r=result();rg(r)["levels"][0]["residual"]["polygon"]=bow;self.assert_hold(r,"RESIDUAL_POLYGON_INVALID",name="e")
        r=result();r["options"][0]["floors"][0]["polygon"]=bow;self.assert_hold(r,"FLOOR_POLYGON_INVALID",name="f")

    def test_area_tamper(self):
        r=result();rg(r)["levels"][0]["rooms"][0]["area_m2"]+=0.5;self.assert_hold(r,"ROOM_AREA_TAMPERED:A",name="a")
        r=result();rg(r)["levels"][0]["residual"]["area_m2"]-=0.5;self.assert_hold(r,"RESIDUAL_AREA_TAMPERED",name="b")
        r=result();rg(r)["levels"][0]["floor_area_m2"]+=1;self.assert_hold(r,"FLOOR_AREA_MISMATCH",name="c")
        r=result();rg(r)["levels"][0]["residual"]["kind"]="CORRIDOR";self.assert_hold(r,"RESIDUAL_KIND_INVALID",name="d")

    def test_geometry_violations(self):
        # room geometrically moved outside the floor with its stated area kept consistent
        r=result();x=rg(r)["levels"][0]["rooms"][1];x["polygon"]=rect(30,0,36,10);self.assert_hold(r,"POLYGON_OUTSIDE_FLOOR",name="a")
        # overlapping rooms, area still consistent per polygon
        r=result();x=rg(r)["levels"][0]["rooms"][1];x["polygon"]=rect(6,0,12,10);self.assert_hold(r,"POLYGON_OVERLAP",name="b")
        # dropped residual leaves a gap: rooms + residual != floor
        r=result();rg(r)["levels"][0]["residual"]=None;self.assert_hold(r,"AREA_CLOSURE_FAILED",name="c")
        r=result();rg(r)["levels"][0]["rooms"][1]["id"]="A";self.assert_hold(r,"DUPLICATE_ROOM_ID",name="d")
        # concave floor: a room inside the notch is outside the L-shaped floor
        r=result();rg(r,1)["levels"][0]["rooms"][1]["polygon"]=rect(10,10,20,20);self.assert_hold(r,"POLYGON_OUTSIDE_FLOOR",name="e")

    def test_readback_detects_tampered_dxf(self):
        import ezdxf
        opt=D.validate(result())[1][0]
        dxf=self.dir/"t.dxf";D.write_dxf(PID,opt,dxf)
        counts,totals=D.read_back(dxf,opt)
        self.assertEqual(sum(counts.values()),7);self.assertAlmostEqual(totals[("BALANCED_L01","PROGRAM")],140.0)
        doc=ezdxf.readfile(dxf);msp=doc.modelspace()
        first=[e for e in msp if e.dxf.layer=="BALANCED_L01_PROGRAM"][0]
        pts=list(first.get_points("xy"));pts[2]=(pts[2][0]+1.0,pts[2][1]);first.set_points(pts,format="xy")
        moved=self.dir/"moved.dxf";doc.saveas(moved)
        with self.assertRaises(D.Hold) as cm:D.read_back(moved,opt)
        self.assertTrue(str(cm.exception).startswith("DXF_VERTEX_MISMATCH"))
        doc=ezdxf.readfile(dxf);msp=doc.modelspace()
        msp.delete_entity([e for e in msp if e.dxf.layer=="BALANCED_L02_UNPROGRAMMED"][0])
        gone=self.dir/"gone.dxf";doc.saveas(gone)
        with self.assertRaises(D.Hold) as cm:D.read_back(gone,opt)
        self.assertEqual(str(cm.exception),"DXF_LAYER_SET_MISMATCH")
        doc=ezdxf.readfile(dxf);doc.header["$INSUNITS"]=4;units=self.dir/"mm.dxf";doc.saveas(units)
        with self.assertRaises(D.Hold) as cm:D.read_back(units,opt)
        self.assertEqual(str(cm.exception),"DXF_INSUNITS_NOT_METERS")

    def test_area_consumer_hold_is_not_swallowed(self):
        opt=D.validate(result())[1][0]
        dxf=self.dir/"t.dxf";D.write_dxf(PID,opt,dxf);_,totals=D.read_back(dxf,opt)
        mp=self.dir/"m.json";m=D.mapping_for(PID,opt,"0"*64)
        m["layers"]["BALANCED_L01_PROGRAM"]["scope"]="ENVELOPE"  # would double count the envelope
        mp.write_text(json.dumps(m),encoding="utf-8")
        with self.assertRaises(D.Hold) as cm:D.consume(PID,opt,dxf,mp,self.dir/"ev",totals)
        self.assertTrue(str(cm.exception).startswith("AREA_CONSUMER_"),str(cm.exception))
        m["layers"]["BALANCED_L01_PROGRAM"]["scope"]="PROGRAM";m["layers"]["BALANCED_L01_GHOST"]={"level":"X","scope":"PROGRAM","operation":"ADD"}
        mp.write_text(json.dumps(m),encoding="utf-8")
        with self.assertRaises(D.Hold) as cm:D.consume(PID,opt,dxf,mp,self.dir/"ev2",totals)
        self.assertIn("MAPPED_LAYER_NOT_FOUND",str(cm.exception))

    @unittest.skipUnless(GEO_PYTHON.exists(),"geometry venv (Shapely) not present")
    def test_generated_massing_result_with_real_room_geometry(self):
        # Room geometry needs Shapely (geometry venv); the DXF stage runs under the current interpreter (ezdxf).
        src={"schema":"ARCHIGROW_MASSING_INPUT_V1","project_id":PID,"source_role":"SYNTHETIC_TEST","rule_source_status":"UNVERIFIED_DEMO",
             "coordinate_units":"m","site_polygon":[[0,0],[40,0],[40,31],[0,31]],
             "constraints":{"max_coverage_pct":60,"max_far_pct":800,"target_far_counted_area_m2":2000,"floor_count":4,"floor_to_floor_m":3.5,"demo_clearance_m":0.5},
             "strategies":["BALANCED","SCULPTURAL"],
             "spatial_program":{"entrance_space_id":"LOBBY","room_geometry_mode":"POLYGON_PARTITION_V1",
                "spaces":[{"id":"LOBBY","name":"Lobby","area_m2":100,"category":"PUBLIC"},{"id":"SHOP","name":"Shop","area_m2":150,"category":"COMMERCIAL"},
                          {"id":"OFFICE","name":"Office","area_m2":300,"category":"OFFICE"}],
                "links":[{"a":"LOBBY","b":"SHOP","weight":5},{"a":"LOBBY","b":"OFFICE","weight":3}]}}
        (self.dir/"input.json").write_text(json.dumps(src),encoding="utf-8")
        p=subprocess.run([str(GEO_PYTHON),str(ROOT/"TOOLS"/"ARCHIGROW_MASSING.py"),str(self.dir/"input.json"),"--out-dir",str(self.dir/"m")],capture_output=True,text=True,timeout=60)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        receipt,out=D.build(self.dir/"m"/"massing_result.json",self.dir/"gen",PID),self.dir/"gen"
        self.assertEqual(receipt["status"],"PASS",receipt["failure_class"])
        self.assertEqual(len(receipt["options"]),2)

if __name__=="__main__":
    unittest.main(verbosity=1)
