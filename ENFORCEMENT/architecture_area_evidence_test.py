#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"TOOLS"/f"{name}.py")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
A=load("ARCHIGROW_AREA_DXF_SVG"); B=load("ARCHIGROW_DESIGN_OVERVIEW_BIND")
U=load("ARCHIGROW_USE_GROUP_CLASSIFIER"); R=load("ARCHIGROW_WORKFLOW_ROUTER"); K=load("ARCHIGROW_LAYOUT_KPI")

def lw(handle,layer,pts,closed=True,bulge=None,paper=False):
    s=["0","LWPOLYLINE","5",handle,"8",layer]+(["67","1"] if paper else [])+["90",str(len(pts)),"70","1" if closed else "0"]
    for i,(x,y) in enumerate(pts):
        s+=["10",str(x),"20",str(y)]+(["42",str(bulge)] if bulge and i==0 else [])
    return s
def oldpoly(handle,layer,pts):
    s=["0","POLYLINE","5",handle,"8",layer,"66","1","10","0","20","0","70","1"]
    for x,y in pts: s+=["0","VERTEX","8",layer,"10",str(x),"20",str(y)]
    return s+["0","SEQEND"]
def dxf(path,entities,insunits=4,blocks=()):
    s=["0","SECTION","2","HEADER","9","$INSUNITS","70",str(insunits),"0","ENDSEC","0","SECTION","2","BLOCKS"]
    for name,ents in blocks:
        s+=["0","BLOCK","8","0","2",name]; [s.extend(e) for e in ents]; s+=["0","ENDBLK"]
    s+=["0","ENDSEC","0","SECTION","2","ENTITIES"]
    for e in entities: s+=e
    s+=["0","ENDSEC","0","EOF"]
    Path(path).write_text("\n".join(s)+"\n",encoding="utf-8")
def sq(x,y,w,h): return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
LAYERS={"A-AREA-GFA":{"level":"1F","scope":"GROSS_FLOOR","operation":"ADD"},"A-AREA-VOID":{"level":"1F","scope":"GROSS_FLOOR","operation":"SUBTRACT","optional":True}}

class AreaEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def run_case(self,entities,mapping=None,**kw):
        src=self.d/"in.dxf"; dxf(src,entities,**kw)
        m=self.d/"map.json"; m.write_text(json.dumps(mapping or {"project_id":"P1","layers":LAYERS,"source_revision":"R03"}),encoding="utf-8")
        return A.export(src,m,self.d/"out",reader="builtin"),src,m
    def kinds(self,ov): return {i["issue"] for i in ov["issues"]}

    def test_clean_adjacent_rooms_with_contained_void_pass(self):
        closing=sq(0,0,10000,10000)+[(0,0)]  # CAD-style repeated closing vertex
        ov,src,_=self.run_case([lw("A1","A-AREA-GFA",closing),lw("A2","A-AREA-GFA",sq(10000,0,5000,10000)),
                                lw("V1","A-AREA-VOID",sq(2000,2000,1000,1000)),lw("X1","OTHER",sq(0,0,1,1)),
                                lw("P1","A-AREA-GFA",sq(0,0,99999,99999),paper=True)])
        self.assertEqual(ov["issues"],[]); self.assertEqual(ov["geometry_status"],"CALCULATED_REVIEW_REQUIRED")
        self.assertEqual(ov["totals"],[{"level":"1F","scope":"GROSS_FLOOR","area_m2":149.0}])
        self.assertEqual(ov["reader"],"builtin-ascii"); self.assertEqual(ov["legal_status"],"NOT_VERIFIED")
        self.assertEqual(ov["target_identity_status"],"DECLARED_BY_MAPPING")
        r=json.loads((self.d/"out"/"stage_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual((r["status"],r["next_route"],r["inputs"][0]["sha256"]),("PASS","OVERVIEW_BIND",A.digest(src)))
        for o in r["outputs"]: self.assertEqual(o["sha256"],A.digest(self.d/"out"/o["ref"]))
        self.assertIn("A2,A-AREA-GFA,1F,GROSS_FLOOR,ADD,50.0",(self.d/"out"/"area_evidence.csv").read_text(encoding="utf-8-sig"))
        self.assertIn('id="cad-V1"',(self.d/"out"/"area_evidence.svg").read_text(encoding="utf-8"))
    def test_collinear_half_overlap_holds_with_exact_area(self):
        ov,_,_=self.run_case([lw("A1","A-AREA-GFA",sq(0,0,10000,10000)),lw("A2","A-AREA-GFA",sq(0,5000,10000,10000))])
        hit=[i for i in ov["issues"] if i["issue"]=="OVERLAPPING_ADD_BOUNDARIES"]
        self.assertEqual(hit[0]["overlap_m2"],50.0); self.assertEqual(ov["geometry_status"],"HOLD")
        r=json.loads((self.d/"out"/"stage_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual((r["status"],r["next_route"]),("HOLD","FIX_SOURCE_OR_MAPPING"))
    def test_duplicate_boundary_detected(self):
        ov,_,_=self.run_case([lw("A1","A-AREA-GFA",sq(0,0,1000,1000)),lw("A2","A-AREA-GFA",list(reversed(sq(0,0,1000,1000))))])
        self.assertIn("DUPLICATE_BOUNDARY",self.kinds(ov))
    def test_subtract_outside_add_holds(self):
        ov,_,_=self.run_case([lw("A1","A-AREA-GFA",sq(0,0,1000,1000)),lw("V1","A-AREA-VOID",sq(500,500,1000,1000))])
        hit=[i for i in ov["issues"] if i["issue"]=="SUBTRACT_NOT_CONTAINED_IN_ADD"][0]
        self.assertEqual((hit["area_m2"],hit["covered_m2"]),(1.0,0.25))
    def test_subtract_covered_by_two_adjacent_adds_passes(self):
        ov,_,_=self.run_case([lw("A1","A-AREA-GFA",sq(0,0,1000,1000)),lw("A2","A-AREA-GFA",sq(1000,0,1000,1000)),lw("V1","A-AREA-VOID",sq(500,200,1000,500))])
        self.assertEqual(ov["issues"],[])
    def test_unit_conflict_and_unitless(self):
        ov,_,_=self.run_case([lw("A1","A-AREA-GFA",sq(0,0,1000,1000))],mapping={"project_id":"P1","layers":LAYERS,"meters_per_unit":0.01})
        self.assertIn("UNIT_OVERRIDE_CONFLICT",self.kinds(ov)); self.assertEqual(ov["target_identity_status"],"UNVERIFIED")
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_DRAWING_UNITS"):
            self.run_case([lw("A1","A-AREA-GFA",sq(0,0,1000,1000))],insunits=0)
    def test_mapped_geometry_hidden_in_block_holds(self):
        ins=["0","INSERT","5","I1","8","0","2","ROOMS","10","0","20","0"]
        ov,_,_=self.run_case([lw("A1","A-AREA-GFA",sq(0,0,1000,1000)),ins],blocks=[("ROOMS",[lw("B1","A-AREA-GFA",sq(0,0,10,10))])])
        self.assertIn("MAPPED_GEOMETRY_INSIDE_BLOCK_NOT_EXPLODED",self.kinds(ov))
    def test_refusals_and_legacy_polyline(self):
        ov,_,_=self.run_case([oldpoly("L1","A-AREA-GFA",sq(0,0,2000,1000)),lw("C1","A-AREA-GFA",sq(5000,0,10,10),bulge=0.5),
                              lw("O1","A-AREA-GFA",sq(8000,0,10,10),closed=False)])
        self.assertEqual(ov["totals"][0]["area_m2"],2.0)
        self.assertTrue({"CURVED_BULGE_REQUIRES_EXPLICIT_TESSELLATION","OPEN_BOUNDARY"}<=self.kinds(ov))
    def test_binary_dxf_refused_by_builtin_reader(self):
        p=self.d/"bin.dxf"; p.write_bytes(b"AutoCAD Binary DXF\r\n\x1a\x00")
        with self.assertRaisesRegex(ValueError,"BINARY_DXF_REQUIRES_EZDXF"): A.read_ascii(p)

class OverviewBind(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
        src=self.d/"in.dxf"; dxf(src,[lw("A1","A-AREA-GFA",sq(0,0,1000,1000))])
        self.map=self.d/"map.json"; self.map.write_text(json.dumps({"project_id":"P1","layers":LAYERS}),encoding="utf-8")
        A.export(src,self.map,self.d/"out",reader="builtin"); self.src=src
        self.area=self.d/"out"/"design_overview_area.json"
        self.ovw=self.d/"overview.json"; self.ovw.write_text(json.dumps({"project_id":"P1","gfa_m2":1.0}),encoding="utf-8")
    def tearDown(self): self.tmp.cleanup()
    def test_current_and_stale(self):
        r=B.bind(self.area,self.ovw,self.d/"b.json",self.src,self.map)
        self.assertEqual((r["binding_status"],r["source_freshness"]["source_dxf"]),("HOLD_REVIEW_REQUIRED","CURRENT"))
        self.src.write_text(self.src.read_text(encoding="utf-8").replace("1000","1200"),encoding="utf-8")
        self.assertEqual(B.bind(self.area,self.ovw,self.d/"b.json",self.src)["binding_status"],"HOLD_STALE_AREA_EVIDENCE")
    def test_never_overwrites_inputs_and_checks_project(self):
        before=self.ovw.read_bytes()
        with self.assertRaisesRegex(ValueError,"OUTPUT_WOULD_OVERWRITE_INPUT"): B.bind(self.area,self.ovw,self.ovw)
        self.assertEqual(self.ovw.read_bytes(),before)
        self.ovw.write_text(json.dumps({"project_id":"OTHER"}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PROJECT_ID_MISMATCH"): B.bind(self.area,self.ovw,self.d/"b.json")
    def test_geometry_hold_propagates(self):
        a=json.loads(self.area.read_text(encoding="utf-8")); a["geometry_status"]="HOLD"; a["issues"]=[{"issue":"X"}]
        self.area.write_text(json.dumps(a),encoding="utf-8")
        r=B.bind(self.area,self.ovw,self.d/"b.json"); self.assertEqual((r["binding_status"],r["geometry_issues"]),("HOLD_GEOMETRY_ISSUES",[{"issue":"X"}]))

class UseGroup(unittest.TestCase):
    def test_statutory_index_fixes(self):
        r=U.classify("P1",[{"space_id":"S1","use":"야영장 시설"},{"space_id":"S2","use":"제2종 근린생활시설","sub_use":"다중생활시설"},
                           {"space_id":"S3","use":"국방·군사시설"},{"space_id":"S4","use":"위험물저장 및 처리시설"},{"space_id":"S5","use":"제2종 근린생활시설"}],
                       "law.go.kr 건축법 시행령 제14조","2026-07-28")
        g={x["space_id"]:(x["candidate_group"],x["group_rank"]) for x in r["uses"]}
        self.assertEqual(g,{"S1":("교육 및 복지시설군",6),"S2":("영업시설군",5),"S3":("주거업무시설군",8),"S4":("산업 등의 시설군",2),"S5":("근린생활시설군",7)})
        self.assertIn("CONFIRM_NOT_다중생활시설",r["uses"][4]["flags"]); self.assertEqual(r["status"],"CANDIDATE_REVIEW_REQUIRED")
    def test_holds_without_source_or_unknown_use(self):
        r=U.classify("P1",[{"use":"카페"}]); self.assertEqual(r["status"],"HOLD"); self.assertEqual(len(r["issues"]),2)
    def test_change_direction_candidate(self):
        up=U.change_direction("제1종 근린생활시설","판매시설")
        self.assertEqual((up["direction"],up["procedure_candidate"],up["procedure_source_status"]),("TO_HIGHER_GROUP","PERMIT_CANDIDATE","UNVERIFIED_ART_19_2"))
        self.assertEqual(U.change_direction("판매시설","업무시설")["direction"],"TO_LOWER_GROUP")
        same=U.change_direction("단독주택","업무시설"); self.assertEqual((same["direction"],same["procedure_source_status"]),("SAME_GROUP","INDEX_VERIFIED"))
        self.assertEqual(U.change_direction("카페","업무시설")["status"],"HOLD")

class RouterAndKernel(unittest.TestCase):
    def test_router_routes_use_group_and_scripts_exist(self):
        p=R.plan("P1","PRODUCTION"); caps=[s["capability"] for s in p["steps"]]
        self.assertEqual(caps.index("USE_GROUP"),caps.index("OVERVIEW_BIND")+1)
        self.assertTrue(all(s["script_exists"] for s in R.plan("P1","FULL")["steps"]))
        self.assertEqual(p["status"],"ROUTING_ONLY_NOT_EXECUTED")
    def test_layout_kernel_collinear_overlap_regression(self):
        o=lambda i,poly:{"object_id":i,"object_type":"UNIT","level":"1F","polygon":poly,"area_scope":"GFA"}
        a=[[0,0],[10,0],[10,10],[0,10]]; b=[[0,5],[10,5],[10,15],[0,15]]
        r=K.evaluate({"site_polygon":[[-1,-1],[20,-1],[20,20],[-1,20]],"objects":[o("A",a),o("B",b)]})
        self.assertFalse(r["ok"]); self.assertTrue(any(x.startswith("OVERLAP:") for x in r["issues"]))
        self.assertTrue(K.polygons_overlap(a,[p[:] for p in a])); self.assertEqual(K.intersection_area(a,b),50.0)
        self.assertFalse(K.polygons_overlap(a,[[10,0],[20,0],[20,10],[10,10]]))

if __name__=="__main__": unittest.main()
