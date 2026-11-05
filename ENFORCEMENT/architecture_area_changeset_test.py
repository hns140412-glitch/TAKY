#!/usr/bin/env python3
"""Synthetic regression for existing ARCHIGROW DXF -> SVG -> area -> changeset."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    path=ROOT/"TOOLS"/(name+".py")
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

A=load("ARCHIGROW_AREA_DXF_SVG")
C=load("ARCHIGROW_AREA_CHANGESET")

def rectangle(handle,width,height,layer="A-AREA-GFA"):
    pts=[(0,0),(width,0),(width,height),(0,height)]
    result=["0","LWPOLYLINE","5",handle,"8",layer,"90","4","70","1"]
    for x,y in pts:result+=["10",str(x),"20",str(y)]
    return result

def make_dxf(path,entities):
    lines=["0","SECTION","2","HEADER","9","$INSUNITS","70","4","0","ENDSEC",
           "0","SECTION","2","ENTITIES"]
    for entity in entities:lines+=entity
    lines+=["0","ENDSEC","0","EOF"]
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")

class ChangeDetection(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.mapping=self.root/"mapping.json"
        self.mapping.write_text(json.dumps({"project_id":"SYNTHETIC","source_revision":"R01",
            "layers":{"A-AREA-GFA":{"level":"1F","scope":"GROSS_FLOOR","operation":"ADD"}}}),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def stage(self,name,entities):
        f=self.root/(name+".dxf");make_dxf(f,entities)
        path=self.root/name
        A.export(f,self.mapping,path,reader="builtin")
        return path
    def diff(self,old,new):
        return C.compare(old,new,self.root/"diff"/"changeset.json")
    def test_area_change_detected_and_totals_rebound(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        new=self.stage("new",[rectangle("A1",12000,10000)])
        result=self.diff(old,new)
        self.assertEqual(result["status"],"CANDIDATE_REVIEW_REQUIRED")
        self.assertEqual(result["changes"][0]["kind"],"MODIFIED")
        self.assertIn("AREA",result["changes"][0]["fields"])
        self.assertEqual(result["area_totals"][0]["delta_m2"],20)
        self.assertEqual(result["downstream_candidate"]["excel_rows_to_rebind"],[{"level":"1F","scope":"GROSS_FLOOR"}])
        self.assertEqual(result["approval"],"NOT_GRANTED")
    def test_relocated_same_area_flags_vector_change(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        entity=rectangle("A1",10000,10000)
        for i in range(0,len(entity)-1):
            if entity[i]=="10":
                entity[i+1]=str(float(entity[i+1])+1000)
        new=self.stage("new",[entity])
        r=self.diff(old,new)
        self.assertEqual(r["changes"][0]["fields"],["GEOMETRY"])
        self.assertEqual(r["area_totals"][0]["delta_m2"],0)
        self.assertTrue(r["downstream_candidate"]["drawing_vector_changed"])
        self.assertEqual(r["downstream_candidate"]["excel_rows_to_rebind"],[])
    def test_reassigned_handle_same_geometry_review_not_duplicate(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        new=self.stage("new",[rectangle("B1",10000,10000)])
        r=self.diff(old,new)
        self.assertEqual(len(r["changes"]),1)
        self.assertEqual(r["changes"][0]["kind"],"HANDLE_REASSIGNED")
        self.assertFalse(r["downstream_candidate"]["drawing_vector_changed"])
    def test_no_change(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        new=self.stage("new",[rectangle("A1",10000,10000)])
        r=self.diff(old,new)
        self.assertEqual(r["status"],"NO_CHANGE")
        self.assertEqual(r["changes"],[])
    def test_corrupted_output_fails_closed(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        new=self.stage("new",[rectangle("A1",12000,10000)])
        p=new/"area_evidence.csv"
        p.write_text(p.read_text(encoding="utf-8-sig").replace("120.0","200.0"),encoding="utf-8-sig")
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):self.diff(old,new)
    def test_revision_metadata_change_is_not_a_false_layer_change(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        self.mapping.write_text(json.dumps({"project_id":"SYNTHETIC","source_revision":"R02",
            "layers":{"A-AREA-GFA":{"level":"1F","scope":"GROSS_FLOOR","operation":"ADD"}}}),encoding="utf-8")
        new=self.stage("new",[rectangle("A1",10000,10000)])
        r=self.diff(old,new)
        self.assertEqual(r["status"],"NO_CHANGE")
        self.assertEqual(r["previous"]["source_identity"]["source_revision"],"R01")
        self.assertEqual(r["current"]["source_identity"]["source_revision"],"R02")
    def test_actual_scope_remap_requires_review(self):
        old=self.stage("old",[rectangle("A1",10000,10000)])
        self.mapping.write_text(json.dumps({"project_id":"SYNTHETIC","source_revision":"R02",
            "layers":{"A-AREA-GFA":{"level":"1F","scope":"NET_FLOOR","operation":"ADD"}}}),encoding="utf-8")
        new=self.stage("new",[rectangle("A1",10000,10000)])
        self.assertEqual(self.diff(old,new)["status"],"HOLD")

    def test_existing_pipeline_opt_in_and_receipt(self):
        P=load("ARCHIGROW_PIPELINE_RUN")
        old=self.stage("old",[rectangle("A1",10000,10000)])
        original_evidence_sha=A.digest(old/"design_overview_area.json")
        new_dxf=self.root/"new.dxf"
        make_dxf(new_dxf,[rectangle("A1",12000,10000)])
        manifest={"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1","project_id":"SYNTHETIC",
                  "stages":["AREA_EVIDENCE","AREA_CHANGESET"],
                  "inputs":{"area":{"dxf":str(new_dxf),"mapping":str(self.mapping),"reader":"builtin"},
                            "area_changeset":{"previous_stage_dir":str(old)}}}
        mf=self.root/"run.json"
        mf.write_text(json.dumps(manifest),encoding="utf-8")
        result=P.run(mf,self.root/"pipeline")
        self.assertEqual(result["status"],"PASS")
        receipt=json.loads((self.root/"pipeline"/"receipts"/"AREA_CHANGESET.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"],"PASS")
        self.assertEqual(receipt["summary"]["area_totals_changed"],1)
        self.assertTrue((self.root/"pipeline"/"stages"/"AREA_CHANGESET"/"area_changeset.json").exists())
        # No new runtime output overwrites either the original DXF or the previous area evidence.
        self.assertEqual(A.digest(old/"design_overview_area.json"),original_evidence_sha)
    def test_router_revision_route_has_inputs(self):
        R=load("ARCHIGROW_WORKFLOW_ROUTER")
        manifest=R.manifest_template("SYNTHETIC","DRAWING_REVISION")
        self.assertEqual(manifest["stages"],["AREA_EVIDENCE","AREA_CHANGESET"])
        self.assertEqual(manifest["inputs"]["area_changeset"],{"previous_stage_dir":None})

if __name__=="__main__":unittest.main()
