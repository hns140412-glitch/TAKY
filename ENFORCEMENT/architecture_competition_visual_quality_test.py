#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_QUALITY.py"

spec=importlib.util.spec_from_file_location("quality",TOOL)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def write_build(root,delivery,items,slides=None):
    root.mkdir(parents=True,exist_ok=True)
    manifest={"delivery":delivery,"items":items}
    validation={
        "source_gaps":[],
        "render_evidence":{"mechanical_render_pass":True}
    }
    (root/"build-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False),encoding="utf-8")
    (root/"validation.json").write_text(json.dumps(validation,ensure_ascii=False),encoding="utf-8")
    if slides is not None:
        (root/"slides.json").write_text(json.dumps({"slides":slides},ensure_ascii=False),encoding="utf-8")

def main():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td)

        good=base/"good"
        write_build(good,"A3_REPORT",[
            {"id":"PLAN:1","order":1,"mode":"PLAN","question":"평면과 공간조직","layout_role":"HERO",
             "source_exists":True,"source_meta":{"kind":"VECTOR","width_px":None,"height_px":None}}
        ])
        r1=mod.evaluate(good)
        assert r1["status"]=="QUALITY_GATE_PASS"
        assert r1["hard_pass"] is True

        bad=base/"bad"
        write_build(bad,"A3_REPORT",[
            {"id":"PLAN:1","order":1,"mode":"PLAN","question":"평면과 공간조직","layout_role":"HERO",
             "source_exists":True,"source_meta":{"kind":"RASTER","width_px":800,"height_px":600}}
        ])
        r2=mod.evaluate(bad)
        assert r2["status"]=="QUALITY_GATE_FAIL"
        assert any(x.startswith("RASTER_WIDTH_LOW") for x in r2["errors"])

        ppt=base/"ppt"
        write_build(ppt,"PPT",[
            {"id":"PLAN:8","order":8,"mode":"PLAN",
             "question":"Communicate organization, use, scale and spatial character while preserving measured geometry.",
             "layout_role":"TECHNICAL_LARGE",
             "source_exists":True,"source_meta":{"kind":"VECTOR","width_px":None,"height_px":None}}
        ],slides=[{"slide_no":8,"claim":"평면과 공간조직"}])
        r3=mod.evaluate(ppt)
        assert r3["status"]=="QUALITY_GATE_PASS"
        assert r3["metrics"]["overlong_claim_count"]==0

    print("PASS: architecture competition visual quality gate")

if __name__=="__main__":
    raise SystemExit(main())
