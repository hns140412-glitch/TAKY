#!/usr/bin/env python3
"""ArchiGrow integrated runtime: pipeline runner, engine CLIs and 2026-10-12 logic fixes."""
import importlib.util, json, subprocess, sys, tempfile, types, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
P=load(ROOT/"TOOLS"/"ARCHIGROW_PIPELINE_RUN.py","pipeline")
FX=load(ROOT/"ENFORCEMENT"/"architecture_area_evidence_test.py","area_fixtures")
PT=load(ROOT/"ENFORCEMENT"/"architecture_production_trace_test.py","trace_fixtures")
RG=load(ROOT/"ENFORCEMENT"/"architecture_regulatory_compiler_test.py","reg_fixtures")
GG=load(ROOT/"ENFORCEMENT"/"architecture_visual_geometry_guard_test.py","guard_fixtures")
K=load(ROOT/"TOOLS"/"ARCHIGROW_LAYOUT_KPI.py","kpi")
LEARN=load(ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_LEARN.py","comp_learn")
BUILD=load(ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_BUILD.py","comp_build")

def w(p,v): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(json.dumps(v,ensure_ascii=False),encoding="utf-8"); return Path(p).name
def unit(i,poly): return {"object_id":i,"object_type":"UNIT","level":"1F","polygon":poly,"area_scope":"GFA"}

def project(d,void=False,layout_extra=None):
    d=Path(d)
    ents=[FX.lw("A1","A-AREA-GFA",FX.sq(0,0,10000,10000)),FX.lw("A2","A-AREA-GFA",FX.sq(10000,0,5000,10000))]
    if void: ents.append(FX.lw("V1","A-AREA-VOID",FX.sq(2000,2000,1000,1000)))
    FX.dxf(d/"plan.dxf",ents)
    m={"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1","project_id":"P1","inputs":{
      "area":{"dxf":"plan.dxf","mapping":w(d/"map.json",{"project_id":"P1","layers":FX.LAYERS,"source_revision":"R03"})},
      "overview":{"approved_overview":w(d/"overview.json",{"project_id":"P1","gfa_m2":None})},
      "use_group":{"input":w(d/"uses.json",{"project_id":"P1","uses":[{"space_id":"S1","use":"업무시설","area_m2":150}],"source_ref":"law.go.kr","effective_date":"2026-07-28","change":{"from_use":"업무시설","to_use":"판매시설"}})},
      "layout":{"model":w(d/"layout.json",{"project_id":"P1","site_polygon":[[-1,-1],[30,-1],[30,20],[-1,20]],"objects":[unit("U1",[[0,0],[10,0],[10,10],[0,10]]),unit("U2",[[10,0],[15,0],[15,10],[10,10]])]+(layout_extra or [])})},
      "cross_check":[{"area_scope":"GROSS_FLOOR","area_level":"1F","kpi":"gfa_area","tolerance_m2":0.5}],
      "regulatory":{"input":w(d/"reg.json",{"project":{"project_id":"P1"},"rules":[RG.rule()]})},
      "geometry_guard":{"input":w(d/"guard.json",{"base":GG.snap(),"candidate":GG.snap(material="brick")})},
      "production":{"trace":w(d/"trace.json",PT.full())}}}
    w(d/"manifest.json",m); return d/"manifest.json",m

def st(summary): return {s["stage"]:s["status"] for s in summary["stages"]}

class PipelineRuntime(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_full_project_passes_every_stage_with_receipts(self):
        man,_=project(self.d); s=P.run(man)
        self.assertEqual(s["status"],"PASS",s["stages"])
        self.assertEqual(set(st(s)),set(P.ORDER)-{"COMPETITION","WORKBOOK_AUDIT","SITE_SOURCE","MASSING","SITE_CONTEXT","SOLAR_STUDY","DESIGN_RULE_REVIEW","AREA_CHANGESET"})  # optional stages have no inputs in this legacy fixture
        cc=json.loads((Path(s["out_dir"])/"stages"/"AREA_KPI_CROSS_CHECK"/"area_kpi_cross_check.json").read_text(encoding="utf-8"))
        self.assertEqual((cc["checks"][0]["cad_area_m2"],cc["checks"][0]["model_value"]),(150.0,150.0))
        case=json.loads((Path(s["out_dir"])/"stages"/"CASE_CANDIDATE"/"case_candidate.json").read_text(encoding="utf-8"))
        self.assertEqual((case["state"],case["promotion_authorized"],case["ledger_write"]),("CASE",False,"NOT_PERFORMED"))
        for r in (Path(s["out_dir"])/"receipts").glob("*.json"):
            rec=json.loads(r.read_text(encoding="utf-8")); self.assertEqual(rec["rule"],"TKY-ARCHIPIPE-001"); self.assertTrue(rec["outputs"])
        self.assertFalse(s["legal_feasibility_authorized"])
    def test_resume_reuses_unchanged_and_reruns_changed_dependents(self):
        man,m=project(self.d); P.run(man)
        again=P.run(man); self.assertTrue(all(v=="REUSED_LAST_PASS" for v in st(again).values()),st(again))
        lay=json.loads((self.d/"layout.json").read_text(encoding="utf-8")); lay["objects"][1]["polygon"]=[[10,0],[16,0],[16,10],[10,10]]
        w(self.d/"layout.json",lay)
        third=st(P.run(man))
        self.assertEqual((third["AREA_EVIDENCE"],third["LAYOUT_KPI"],third["AREA_KPI_CROSS_CHECK"]),("REUSED_LAST_PASS","PASS","HOLD"))
    def test_cad_model_mismatch_holds_cross_check(self):
        man,_=project(self.d,void=True); s=P.run(man)   # CAD 149 m2 vs model 150 m2 > 0.5 tolerance
        self.assertEqual((st(s)["AREA_KPI_CROSS_CHECK"],s["status"]),("HOLD","HOLD")); self.assertEqual(s["next_route"],"RESUME_FROM:AREA_KPI_CROSS_CHECK")
    def test_area_hold_blocks_dependents_only(self):
        man,_=project(self.d)
        FX.dxf(self.d/"plan.dxf",[FX.lw("A1","A-AREA-GFA",FX.sq(0,0,10000,10000)),FX.lw("A2","A-AREA-GFA",FX.sq(0,5000,10000,10000))])
        x=st(P.run(man))
        self.assertEqual((x["AREA_EVIDENCE"],x["OVERVIEW_BIND"],x["AREA_KPI_CROSS_CHECK"],x["REGULATORY"]),("HOLD","BLOCKED","BLOCKED","PASS"))
    def test_project_identity_mismatch_holds(self):
        man,_=project(self.d); w(self.d/"trace.json",{**PT.full(),"project_id":"OTHER"})
        s=P.run(man); r=json.loads((Path(s["out_dir"])/"receipts"/"PRODUCTION_TRACE.json").read_text(encoding="utf-8"))
        self.assertEqual((r["status"],r["failure_class"]),("HOLD","PROJECT_ID_MISMATCH")); self.assertEqual(st(s)["CASE_CANDIDATE"],"BLOCKED")
    def test_stage_exception_is_fail_not_crash(self):
        man,m=project(self.d); m["inputs"]["area"]["dxf"]="missing.dxf"; w(man,m)
        s=P.run(man); self.assertEqual((st(s)["AREA_EVIDENCE"],s["status"]),("FAIL","FAIL"))
    def test_single_stage_rerun_uses_upstream_receipts(self):
        man,_=project(self.d); P.run(man)
        s=P.run(man,only=["AREA_KPI_CROSS_CHECK"],force=True); self.assertEqual(st(s),{"AREA_KPI_CROSS_CHECK":"PASS"})
    def test_competition_stage_honors_delivery_and_holds_on_source_gaps(self):
        man,m=project(self.d); m["inputs"]={"competition":{"delivery":"PPT","project_type":"urban_civic"}}; w(man,m)
        s=P.run(man); r=json.loads((Path(s["out_dir"])/"receipts"/"COMPETITION.json").read_text(encoding="utf-8"))
        self.assertEqual((r["status"],r["summary"]["delivery"],r["summary"]["next_gate"]),("HOLD","PPT","RESOLVE_SOURCE_GAPS"))
    def test_router_template_connects_to_runner_and_blocks_unbound(self):
        R=load(ROOT/"TOOLS"/"ARCHIGROW_WORKFLOW_ROUTER.py","router")
        t=R.manifest_template("P1","FULL"); w(self.d/"tpl.json",t)
        self.assertTrue(set(t["stages"])<=set(P.ORDER)); self.assertIn("AREA_KPI_CROSS_CHECK",t["stages"])
        s=P.run(self.d/"tpl.json"); self.assertEqual(s["status"],"BLOCKED")
        self.assertEqual(st(s)["AREA_EVIDENCE"],"BLOCKED"); self.assertNotIn("FAIL",st(s).values())
    def test_cli_exit_codes(self):
        man,_=project(self.d)
        ok=subprocess.run([sys.executable,str(ROOT/"TOOLS"/"ARCHIGROW_PIPELINE_RUN.py"),str(man)],capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(ok.returncode,0,ok.stderr[-500:]); self.assertEqual(json.loads(ok.stdout)["status"],"PASS")

class EngineCLIs(unittest.TestCase):
    def test_engines_execute_project_input(self):
        with tempfile.TemporaryDirectory() as td:
            cases={"ARCHIGROW_LAYOUT_KPI.py":{"site_polygon":[[0,0],[10,0],[10,10],[0,10]],"objects":[unit("U1",[[1,1],[3,1],[3,3],[1,3]])]},
                   "ARCHIGROW_REGULATORY_COMPILER.py":{"project":{"project_id":"P1"},"rules":[RG.rule()]},
                   "ARCHIGROW_PRODUCTION_TRACE.py":PT.full(),
                   "ARCHIGROW_VISUAL_GEOMETRY_GUARD.py":{"base":GG.snap(),"candidate":GG.snap()}}
            for tool,data in cases.items():
                inp=Path(td)/(tool+".json"); inp.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
                p=subprocess.run([sys.executable,str(ROOT/"TOOLS"/tool),"--input",str(inp)],capture_output=True,text=True,encoding="utf-8")
                self.assertEqual(p.returncode,0,(tool,p.stdout[-400:],p.stderr[-400:])); self.assertTrue(json.loads(p.stdout)["ok"])
            bad=Path(td)/"bad.json"; bad.write_text(json.dumps({"site_polygon":[[0,0],[1,0]],"objects":[]}),encoding="utf-8")
            self.assertEqual(subprocess.run([sys.executable,str(ROOT/"TOOLS"/"ARCHIGROW_LAYOUT_KPI.py"),"--input",str(bad)],capture_output=True).returncode,2)

class LogicFixes(unittest.TestCase):
    def test_concave_site_notch_crossing_is_outside(self):
        site=[[0,0],[10,0],[10,4],[4,4],[4,10],[0,10]]   # L-shaped site; notch at x>4,y>4
        obj=unit("U1",[[3,3],[6,3],[6,6],[3,6]])           # all vertices except (6,6) inside... (6,6) in notch
        bridge=unit("B1",[[5,1],[9,1],[9,3.9],[5,3.9]])
        self.assertTrue(K.evaluate({"site_polygon":site,"objects":[bridge]})["ok"])
        span=unit("S1",[[1,5],[3,5],[3,9],[1,9]]); self.assertTrue(K.evaluate({"site_polygon":site,"objects":[span]})["ok"])
        cross=unit("X1",[[2,2],[9,2],[9,3],[3,3],[3,9],[2,9]])  # inside; control
        self.assertTrue(K.evaluate({"site_polygon":site,"objects":[cross]})["ok"])
        # vertices all inside the L but the edge (8,3)->(3,8) cuts across the notch
        notch=unit("N1",[[8,1],[8,3],[3,8],[1,8],[1,1]])
        r=K.evaluate({"site_polygon":site,"objects":[notch]})
        self.assertFalse(r["ok"]); self.assertIn("N1:OUTSIDE_SITE_BOUNDARY",r["issues"])
        self.assertFalse(K.evaluate({"site_polygon":site,"objects":[obj]})["ok"])
    def test_uninspectable_raster_fails_quality(self):
        with tempfile.TemporaryDirectory() as td:
            png=Path(td)/"plan.png"; png.write_bytes(b"not really a png")
            self.assertEqual(BUILD.inspect_source(str(png))["kind"],"RASTER_UNINSPECTED")
            saved=BUILD.Image; BUILD.Image=None
            try: self.assertEqual(BUILD.inspect_source(str(png))["reason"],"PIL_UNAVAILABLE")
            finally: BUILD.Image=saved
    def args(self,td,**kw):
        a=dict(ledger=str(Path(td)/"comp.jsonl"),lineage_ledger=str(Path(td)/"lineage.jsonl"),summary=False,project_id="P1",competition="C1",agency="A1",
               entry_id="E1",submission_stage="FINAL",submission_revision="R1",artifact_id="ART1",artifact_type="DRAWING",board_no="1",page_no=None,
               drawing_name="배치도",mode="CONTEXT",technique="figure_ground",outcome="OBSERVATION_ONLY",state="CASE",why="w",reviewer_signal="",failure_mode="",
               artifact_ref=["drive:art1"],source_ref=["drive:src1"])
        a.update(kw); return types.SimpleNamespace(**a)
    def test_competition_learning_idempotent_lineage_first_and_corrupt_ledger_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            r1,_,d1=LEARN.append_record_ex(self.args(td)); r2,_,d2=LEARN.append_record_ex(self.args(td))
            self.assertEqual((d1,d2,r1["evidence_fingerprint_sha256"]),(False,True,r2["evidence_fingerprint_sha256"]))
            self.assertEqual(len((Path(td)/"comp.jsonl").read_text(encoding="utf-8").splitlines()),1)
            saved=LEARN.materialize; LEARN.materialize=lambda *a,**k:{"ok":False}
            try:
                with self.assertRaises(RuntimeError): LEARN.append_record_ex(self.args(td,artifact_id="ART2"))
            finally: LEARN.materialize=saved
            self.assertEqual(len((Path(td)/"comp.jsonl").read_text(encoding="utf-8").splitlines()),1)  # no orphan row
            with (Path(td)/"comp.jsonl").open("a",encoding="utf-8") as f: f.write("{broken\n")
            with self.assertRaisesRegex(ValueError,"LEDGER_CORRUPT_LINE"): LEARN.summarize(str(Path(td)/"comp.jsonl"))

if __name__=="__main__": unittest.main()
