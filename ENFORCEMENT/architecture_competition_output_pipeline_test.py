#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

binder=load("binder",ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_BIND.py")
builder=load("builder",ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_BUILD.py")
renderer=load("renderer",ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_RENDER.py")

def main():
    profiles=json.loads((ROOT/"DOMAIN"/"ARCHITECTURE_COMPETITION_OUTPUT_PROFILE_REGISTRY.json").read_text(encoding="utf-8"))["profiles"]
    assert set(profiles)=={"A1_BOARD","A3_REPORT","PPT","PDF_DRAWING_BOOK"}

    package={
        "delivery":"A3_REPORT","brief_verified":True,"content_frozen":False,"focus":"test",
        "items":[
            {"order":1,"mode":"PLAN","question":"Plan proof","source_required":"verified plan","production_path":"CAD->SVG","recommended_techniques":["clean_vector_plan"]},
            {"order":2,"mode":"SECTION","question":"Section proof","source_required":"verified section","production_path":"CAD->SVG","recommended_techniques":["rendered_section"]}
        ]
    }
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        (td/"plan.png").write_bytes(b"x")
        (td/"section.png").write_bytes(b"x")
        found=binder.build(package,td)
        assert len(found["bindings"])==2
        manifest=builder.build_manifest(package,profiles["A3_REPORT"],found["bindings"])
        assert manifest["status"]=="READY_TO_RENDER"
        assert all(x["binding_status"]=="BOUND" for x in manifest["items"])
        assert renderer.expected_page_count(manifest)==2

        no_sources=builder.build_manifest(package,profiles["A3_REPORT"],{})
        assert no_sources["status"]=="SOURCE_GAPS"
        assert all(x["binding_status"]=="MISSING_SOURCE" for x in no_sources["items"])

        assert renderer.expected_page_count({"delivery":"A1_BOARD","items":[1,2]})==1
        assert renderer.expected_page_count({"delivery":"PPT","items":[1,2,3]})==3
        assert renderer.expected_page_count({"delivery":"PDF_DRAWING_BOOK","items":[1,2,3]})==4

    print("PASS: architecture competition result-specific output pipeline")

if __name__=="__main__":
    raise SystemExit(main())
