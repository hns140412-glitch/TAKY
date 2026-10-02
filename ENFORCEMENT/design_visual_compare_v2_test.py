#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
COMPARE=HERE/"design_visual_compare_v2.py"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2)+"\n",encoding="utf-8")
def call(root,expect):
    cp=subprocess.run([sys.executable,str(COMPARE),"--manifest",str(root/"design-to-ui.json"),"--render-manifest",str(root/"ui-audit/render-manifest.json"),"--root",str(root),"--out","ui-audit/visual-result.json","--diff-dir","ui-audit/diff"],text=True,capture_output=True)
    if cp.returncode!=expect: raise AssertionError(cp.stdout+"\n"+cp.stderr)
    return json.loads((root/"ui-audit/visual-result.json").read_text())

def setup(root):
    (root/"design/golden").mkdir(parents=True)
    (root/"design/contracts").mkdir(parents=True)
    (root/"design/fixtures").mkdir(parents=True)
    (root/"ui-audit").mkdir(parents=True)
    ref=Image.new("RGB",(100,120),(240,230,210)); ImageDraw.Draw(ref).rectangle((20,30,80,90),fill=(70,100,80)); ref.save(root/"design/golden/home.png")
    actual=ref.copy(); actual.save(root/"ui-audit/home.png")
    fixture=root/"design/fixtures/home.json"; write(fixture,{"synthetic":True})
    contract=root/"design/contracts/home.json"
    write(contract,{"schema":"TAKY_SCREEN_CONTRACT_V2","screen_id":"home","regions":[{"id":"main"}],"typography":{"x":1},"components":[{"id":"root"}],"responsive":{"x":1},"interactions":[{"id":"tap"}],"states":["BASE"],
      "visual_compare":{"mae_max":0.01,"changed_ratio_max":0.02,"pixel_delta_threshold":16,
        "regions":[{"id":"critical","x":0.15,"y":0.2,"w":0.7,"h":0.6,"critical":True,"mae_max":0.01,"changed_ratio_max":0.02}]}})
    layer=root/"design/contracts/layers.json"
    write(layer,{"schema":"TAKY_LAYER_CONTRACT_V1","screen_id":"home","layers":[]})
    manifest=root/"design-to-ui.json"
    write(manifest,{"schema":"TAKY_DESIGN_TO_UI_PIPELINE_V1","project":"TEST","source_commit":"2"*40,
      "policy":{"runtime_must_not_auto_become_golden":True,"flattened_mockup_runtime_forbidden":True,"evidence_files_required":True,"image_generation_optional":True},
      "screens":[{"id":"home","authority_ref":"TEST","golden":{"status":"BOUND","source_receipt":"TEST","path":"design/golden/home.png","sha256":sha(root/"design/golden/home.png"),"use":"REFERENCE_ONLY"},
        "screen_contract":{"path":"design/contracts/home.json","sha256":sha(contract)},"layer_contract":{"path":"design/contracts/layers.json","sha256":sha(layer)},
        "viewports":[{"id":"phone","width":100,"height":120,"dpr":1}],
        "states":[{"id":"BASE","fixture_path":"design/fixtures/home.json","fixture_sha256":sha(fixture),"visual_policy":"GOLDEN_PARITY"}]}]})
    write(root/"ui-audit/render-manifest.json",{"schema":"TAKY_RENDER_MANIFEST_V1","project":"TEST","manifest_sha256":sha(manifest),"source_commit":"2"*40,
      "entries":[{"screen_id":"home","state_id":"BASE","viewport_id":"phone","actual_path":"ui-audit/home.png","actual_sha256":sha(root/"ui-audit/home.png")}]})

def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); setup(root)
        r=call(root,0)
        assert r["pass"] is True and r["coverage"]==["home:BASE:phone"]
        assert (root/r["results"][0]["diff_path"]).is_file()

        # Critical-region visual drift must fail.
        img=Image.open(root/"ui-audit/home.png").convert("RGB")
        ImageDraw.Draw(img).rectangle((25,35,75,85),fill=(200,30,30)); img.save(root/"ui-audit/home.png")
        rm=json.loads((root/"ui-audit/render-manifest.json").read_text())
        rm["entries"][0]["actual_sha256"]=sha(root/"ui-audit/home.png"); write(root/"ui-audit/render-manifest.json",rm)
        r=call(root,1)
        assert r["pass"] is False and r["results"][0]["regions"][0]["pass"] is False

        # Dimension mismatch is a hard visual failure; no implicit resize.
        Image.new("RGB",(90,120),(240,230,210)).save(root/"ui-audit/home.png")
        rm["entries"][0]["actual_sha256"]=sha(root/"ui-audit/home.png"); write(root/"ui-audit/render-manifest.json",rm)
        r=call(root,1)
        assert r["results"][0]["error"]=="DIMENSION_MISMATCH"

    print("DESIGN_VISUAL_COMPARE_V2_REGRESSION=PASS")
    return 0
if __name__=="__main__": raise SystemExit(main())
