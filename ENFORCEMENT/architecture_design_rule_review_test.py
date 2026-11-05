#!/usr/bin/env python3
"""Synthetic vertical-slice tests: real SVG polygon bytes + cited dummy manual + candidate geometry."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("ARCHIGROW_DESIGN_RULE_REVIEW",ROOT/"TOOLS"/"ARCHIGROW_DESIGN_RULE_REVIEW.py")
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

def poly(id,x,y,w,h):
    return f'<polygon id="{id}" points="{x},{y} {x+w},{y} {x+w},{y+h} {x},{y+h}" />'

class CaseReview(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.d=Path(self.tmp.name)
        (self.d/"manual.txt").write_text("SYNTHETIC DEMO ONLY\np3 room width 3.0m; storage 1.8m; p5 parking 2.3m and ramp 16%",encoding="utf-8")
        self.svg=self.d/"plan.svg"
        self.svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 11000 5000">'
            +poly("living",0,0,2800,4000)+poly("store",2800,0,2200,4000)
            +poly("route",6000,0,4000,3000)+poly("duct",7000,1000,1200,1000)
            +poly("ramp",6000,3500,4000,1400)+'</svg>',encoding="utf-8")
        self.manual={
            "schema":"ARCHIGROW_MANUAL_RULEPACK_V1","company":"SYNTHETIC_CONTRACTOR",
            "manual_source":{"path":"manual.txt","sha256":M.digest(self.d/"manual.txt"),"revision":"DEMO_01"},
            "rules":[
                {"id":"U-01","source_locator":"p.3","type":"MIN_ROOM_RECT_WIDTH","target_kind":"ROOM","target_use":"living","measure_axis":"x","threshold":3.0},
                {"id":"U-02","source_locator":"p.3","type":"MIN_ROOM_RECT_WIDTH","target_kind":"ROOM","target_use":"storage","measure_axis":"x","threshold":1.8},
                {"id":"G-01","source_locator":"p.5","type":"MIN_CLEAR_HEIGHT","target_kind":"DRIVE_ZONE","threshold":2.3},
                {"id":"G-02","source_locator":"p.5","type":"MAX_RAMP_GRADE","target_kind":"RAMP","threshold":16.0}
            ]}
        self.plan={"schema":"ARCHIGROW_SEMANTIC_SVG_PLAN_V1","project_id":"SYNTHETIC",
            "drawing_revision":"R02","source_svg":{"path":"plan.svg","sha256":M.digest(self.svg)},
            "meters_per_svg_unit":0.001,"completeness":{"overhead_obstacles":"VERIFIED_COMPLETE"},
            "entities":[{"id":"L","svg_id":"living","kind":"ROOM","level":"1F","use":"living"},
                        {"id":"S","svg_id":"store","kind":"ROOM","level":"1F","use":"storage"},
                        {"id":"D","svg_id":"route","kind":"DRIVE_ZONE","level":"B1","finished_floor_z_m":-3.4},
                        {"id":"O","svg_id":"duct","kind":"OBSTRUCTION","level":"B1","underside_z_m":-1.25},
                        {"id":"R","svg_id":"ramp","kind":"RAMP","level":"B1","rise_m":1.7,"run_m":10.0,"run_basis":"HORIZONTAL"}],
            "movable_partitions":[{"id":"LP-01","room_a":"L","room_b":"S","axis":"x","max_shift_m":0.35}]}
        self.write()
    def tearDown(self):self.tmp.cleanup()
    def write(self):
        self.mp=self.d/"manual.json";self.mp.write_text(json.dumps(self.manual),encoding="utf-8")
        self.pp=self.d/"plan.json";self.pp.write_text(json.dumps(self.plan),encoding="utf-8")
    def run_case(self):
        return M.review(self.pp,self.mp,self.d/"out")
    def test_full_unit_and_parking_warnings_and_actual_partition_alternative(self):
        doc=self.run_case()
        r={o["rule_id"]:o["status"] for o in doc["checks"]}
        self.assertEqual(r,{"U-01":"VIOLATION","U-02":"PASS","G-01":"VIOLATION","G-02":"VIOLATION"})
        self.assertEqual(doc["summary"],{"PASS":1,"VIOLATION":3,"NEEDS_SOURCE":0})
        self.assertGreater(len(doc["alternatives"]),0)
        winner=doc["alternatives"][0]
        self.assertEqual(winner["shift_m"],0.2)
        self.assertEqual(winner["candidate_rules"]["U-01"],"PASS")
        self.assertEqual(winner["candidate_rules"]["U-02"],"PASS")
        self.assertTrue((self.d/"out"/"alternative_overlay.svg").exists())
        self.assertEqual(json.loads((self.d/"out"/"stage_receipt.json").read_text(encoding="utf-8"))["status"],"HOLD")
        self.assertEqual(doc["authority"],"DESIGN_CANDIDATE_ONLY")
        self.assertEqual(doc["statutory_compliance"],"NOT_VERIFIED")
    def test_unknown_obstruction_coverage_blocks_unqualified_pass(self):
        self.plan["completeness"]={}
        self.plan["entities"][3]["underside_z_m"]=-0.8
        self.write()
        doc=self.run_case()
        self.assertEqual(next(o for o in doc["checks"] if o["rule_id"]=="G-01")["status"],"NEEDS_SOURCE")
        receipt=json.loads((self.d/"out"/"stage_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"],"HOLD")
    def test_unbound_svg_geometry_ref_is_not_guessed(self):
        self.plan["entities"][0]["svg_id"]="not-in-svg"
        self.write()
        with self.assertRaisesRegex(ValueError,"SEMANTIC_SVG_ELEMENT_MISSING"):self.run_case()
    def test_manual_bytes_change_fails_closed(self):
        (self.d/"manual.txt").write_text("changed",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"MANUAL_SHA_MISMATCH"):self.run_case()
    def test_svg_bytes_change_fails_closed(self):
        self.svg.write_text(self.svg.read_text(encoding="utf-8")+"<!-- revision -->",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SVG_SHA_MISMATCH"):self.run_case()
    def test_locked_partition_prevents_unsupported_alternative(self):
        self.plan["entities"][0]["locked"]=True
        self.write()
        doc=self.run_case()
        self.assertEqual(doc["alternatives"],[])
    def test_mechanical_result_does_not_overwrite_source_files(self):
        old=[M.digest(p) for p in (self.mp,self.pp,self.svg,self.d/"manual.txt")]
        self.run_case()
        self.assertEqual(old,[M.digest(p) for p in (self.mp,self.pp,self.svg,self.d/"manual.txt")])
    def test_rule_without_source_locator_refused(self):
        del self.manual["rules"][0]["source_locator"]
        self.write()
        with self.assertRaisesRegex(ValueError,"RULE_SOURCE_LOCATOR_REQUIRED"):self.run_case()
    def test_invalid_slanted_room_width_is_unknown_not_pass(self):
        txt=self.svg.read_text(encoding="utf-8").replace('2800,4000 0,4000','2700,4000 0,4000')
        self.svg.write_text(txt,encoding="utf-8")
        self.plan["source_svg"]["sha256"]=M.digest(self.svg)
        self.write()
        doc=self.run_case()
        self.assertEqual(next(o for o in doc["checks"] if o["rule_id"]=="U-01")["status"],"NEEDS_SOURCE")

    def test_same_plan_xy_different_floor_obstacle_not_falsely_assigned(self):
        self.plan["entities"][3]["level"]="B2"  # visually overlapping beam, unrelated floor
        self.write()
        doc=self.run_case()
        self.assertEqual(next(o for o in doc["checks"] if o["rule_id"]=="G-01")["status"],"NEEDS_SOURCE")
    def test_partition_cannot_move_across_floors(self):
        self.plan["entities"][1]["level"]="2F"
        self.write()
        self.assertEqual(self.run_case()["alternatives"],[])
    def test_missing_level_is_rejected(self):
        self.plan["entities"][0].pop("level")
        self.write()
        with self.assertRaisesRegex(ValueError,"ENTITY_LEVEL_REQUIRED"):self.run_case()

    def test_existing_router_and_pipeline_integration(self):
        root=Path(__file__).resolve().parents[1]
        def module(path,name):
            spec=importlib.util.spec_from_file_location(name,path)
            m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
        R=module(root/"TOOLS"/"ARCHIGROW_WORKFLOW_ROUTER.py","route")
        P=module(root/"TOOLS"/"ARCHIGROW_PIPELINE_RUN.py","pipeline")
        routed=R.manifest_template("SYNTHETIC","PLAN_MANUAL_REVIEW")
        self.assertEqual(routed["stages"],["DESIGN_RULE_REVIEW"])
        self.assertEqual(set(routed["inputs"]["design_review"]),{"plan_json","manual_rulepack_json"})
        routed["inputs"]["design_review"]={"plan_json":str(self.pp),"manual_rulepack_json":str(self.mp)}
        mf=self.d/"pipeline_manifest.json";mf.write_text(json.dumps(routed),encoding="utf-8")
        summary=P.run(mf,self.d/"pipeline_out")
        receipt=json.loads((self.d/"pipeline_out"/"receipts"/"DESIGN_RULE_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["status"],"HOLD")
        self.assertEqual(receipt["summary"]["alternative_count"]>0,True)
        self.assertTrue((self.d/"pipeline_out"/"stages"/"DESIGN_RULE_REVIEW"/"design_case_review.json").is_file())
        # Change to one satisfied, explicitly sourced rule. Mechanical PASS does not approve the design.
        self.manual["rules"]=[self.manual["rules"][1]]
        self.write()
        changed=P.run(mf,self.d/"pipeline_out")
        self.assertEqual(changed["status"],"PASS")
        self.assertFalse(changed["approval_inferred"])
        self.assertFalse(changed["legal_feasibility_authorized"])

def create_pilot(destination):
    import shutil
    d=Path(destination).resolve()
    d.mkdir(parents=True,exist_ok=True)
    fixture=CaseReview("test_full_unit_and_parking_warnings_and_actual_partition_alternative")
    fixture.setUp()
    try:
        # Real original-file hashes are preserved; source is explicitly synthetic.
        for filename in ("manual.txt","manual.json","plan.svg","plan.json"):
            shutil.copy2(fixture.d/filename,d/filename)
        P=fixture
        result=M.review(d/"plan.json",d/"manual.json",d/"out")
        (d/"README_SYNTHETIC_ONLY.txt").write_text(
            "SYNTHETIC DATA ONLY: not a contractor manual or actual project DWG.\n"
            "Open out/design_review_preview.html; out/design_review_table.csv opens in Excel.\n"
            "Original SVG, source-bound manual fixture and inputs remain untouched.\n"
            "No licensed Rhino/Grasshopper, XREF, DWG ingestion or PPT template binding was tested.\n"
            "DO NOT use DEMO widths, overhead clearance, or slopes as applicable code/contract standards.\n",encoding="utf-8")
        return {"destination":str(d),"status":result["status"],"issues":result["summary"],
                "alternatives":len(result["alternatives"])}
    finally:
        fixture.tearDown()

if __name__=="__main__":
    import sys
    if len(sys.argv)==3 and sys.argv[1]=="--pilot-dir":
        print(json.dumps(create_pilot(sys.argv[2]),ensure_ascii=False,indent=2))
    else:
        unittest.main()
