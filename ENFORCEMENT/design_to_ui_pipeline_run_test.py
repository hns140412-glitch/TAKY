#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
RUNNER=HERE/"design_to_ui_pipeline_run.py"

def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path: Path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")

def git_commit(root: Path,message: str):
    if not (root/".git").exists():
        subprocess.run(["git","init","-q"],cwd=root,check=True)
        subprocess.run(["git","config","user.email","test@example.com"],cwd=root,check=True)
        subprocess.run(["git","config","user.name","TAKY Test"],cwd=root,check=True)
    subprocess.run(["git","add","-A"],cwd=root,check=True)
    subprocess.run(["git","commit","-qm",message],cwd=root,check=True)

def setup(root: Path,fail_stage: str|None=None):
    (root/"design/golden").mkdir(parents=True)
    (root/"design/contracts").mkdir(parents=True)
    (root/"design/fixtures").mkdir(parents=True)
    (root/"assets").mkdir(parents=True)
    (root/"tools").mkdir(parents=True)

    ref=Image.new("RGB",(240,320),(240,230,210))
    ImageDraw.Draw(ref).rectangle((40,70,200,250),fill=(70,100,80))
    ref.save(root/"design/golden/home.png")
    (root/"assets/layer.bin").write_bytes(b"layer")
    write(root/"design/fixtures/home.json",{"fixture":"BASE"})
    write(root/"design/contracts/home.screen.json",{
        "schema":"TAKY_SCREEN_CONTRACT_V2","screen_id":"home",
        "regions":[{"id":"main"}],"typography":{"primary":"system"},
        "components":[{"id":"root"}],"responsive":{"safe_area":True},
        "interactions":[{"id":"tap"}],"states":["BASE"],
        "visual_compare":{"mae_max":0.01,"changed_ratio_max":0.02,"pixel_delta_threshold":16,
          "regions":[{"id":"main","x":0,"y":0,"w":1,"h":1,"critical":True}]}
    })
    write(root/"design/contracts/home.layers.json",{
        "schema":"TAKY_LAYER_CONTRACT_V1","screen_id":"home","layers":[
          ({"role":"BACKGROUND","status":"ASSET_PRODUCTION_OPEN"} if fail_stage=="contract" else {"role":"BACKGROUND","status":"BOUND","path":"assets/layer.bin","sha256":sha(root/"assets/layer.bin")}),
          {"role":"FOREGROUND","status":"BOUND","path":"assets/layer.bin","sha256":sha(root/"assets/layer.bin")},
          {"role":"OBJECT","status":"BOUND","path":"assets/layer.bin","sha256":sha(root/"assets/layer.bin")},
          {"role":"CHARACTER_SLOT","status":"RUNTIME_SLOT","selector":"#character","owner":"TEST","resolver_contract":"TEST"},
          {"role":"FUNCTION_UI","status":"LIVE_DOM","selector":"#app","owner":"TEST"}
        ]
    })
    screen=root/"design/contracts/home.screen.json"; layers=root/"design/contracts/home.layers.json"; fixture=root/"design/fixtures/home.json"
    manifest={
      "schema":"TAKY_DESIGN_TO_UI_PIPELINE_V1","project":"RUNNER_TEST","source_commit":"3"*40,
      "policy":{"runtime_must_not_auto_become_golden":True,"flattened_mockup_runtime_forbidden":True,"evidence_files_required":True,"image_generation_optional":True},
      "screens":[{
        "id":"home","authority_ref":"TEST",
        "golden":{"status":"BOUND","source_receipt":"TEST","path":"design/golden/home.png","sha256":sha(root/"design/golden/home.png"),"use":"REFERENCE_ONLY"},
        "screen_contract":{"path":"design/contracts/home.screen.json","sha256":sha(screen)},
        "layer_contract":{"path":"design/contracts/home.layers.json","sha256":sha(layers)},
        "viewports":[{"id":"phone","width":240,"height":320,"dpr":1}],
        "states":[{"id":"BASE","fixture_path":"design/fixtures/home.json","fixture_sha256":sha(fixture),"visual_policy":"GOLDEN_PARITY"}]
      }]
    }
    write(root/"design-to-ui.json",manifest)
    manifest_sha=sha(root/"design-to-ui.json")

    adapter_py=root/"tools/adapter.py"
    adapter_py.write_text("""from pathlib import Path
import shutil,sys
root=Path.cwd(); mode=sys.argv[1]
out=root/'ui-audit';out.mkdir(exist_ok=True)
if mode=='capture':
    shutil.copyfile(root/'design/golden/home.png',out/'home.png')
    sys.exit(0)
passed=not (len(sys.argv)>2 and sys.argv[2]=='fail')
sys.exit(0 if passed else 1)
""",encoding="utf-8")
    fail_arg=lambda stage:["fail"] if fail_stage==stage else []
    write(root/"design-ui-adapter.json",{
      "schema":"TAKY_DESIGN_UI_ADAPTER_V1",
      "capture":{
        "command":[sys.executable,"tools/adapter.py","capture"],
        "artifacts":[
          {"screen_id":"home","state_id":"BASE","viewport_id":"phone","path":"ui-audit/home.png"}
        ]
      },
      "checks":{
        "interaction":{"command":[sys.executable,"tools/adapter.py","interaction",*fail_arg("interaction")],"coverage":["home:BASE"]},
        "responsive":{"command":[sys.executable,"tools/adapter.py","responsive",*fail_arg("responsive")],"coverage":["home:BASE:phone"]},
        "asset_integrity":{"command":[sys.executable,"tools/adapter.py","asset",*fail_arg("asset_integrity")],"coverage":["home"]}
      }
    })
    git_commit(root,"fixture")

def run(root: Path):
    return subprocess.run([sys.executable,str(RUNNER),"--root",str(root)],text=True,capture_output=True)

def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);setup(root)
        cp=run(root)
        assert cp.returncode==0,(cp.stdout,cp.stderr)
        s=json.loads((root/"ui-audit/pipeline-status.json").read_text())
        assert s["status"]=="DESIGN_PASS",s
        assert (root/"ui-audit/design-receipt.json").is_file()

    with tempfile.TemporaryDirectory() as td:
        root=Path(td);setup(root,"interaction")
        write(root/"ui-audit/design-receipt.json",{"stale":True})
        cp=run(root)
        assert cp.returncode!=0
        s=json.loads((root/"ui-audit/pipeline-status.json").read_text())
        assert s["status"]=="INTERACTION_BLOCKED",s
        assert s["routing"]["return_to_stage"]=="IMPLEMENT",s
        assert s["routing"]["owner"]=="UI_IMPLEMENTATION",s
        assert not (root/"ui-audit/design-receipt.json").exists()

    with tempfile.TemporaryDirectory() as td:
        root=Path(td);setup(root,"contract")
        cp=run(root)
        assert cp.returncode!=0
        s=json.loads((root/"ui-audit/pipeline-status.json").read_text())
        assert s["status"]=="CONTRACT_BLOCKED",s
        assert s["routing"]["return_to_stage"]=="UI_CONTRACT",s
        assert s["routing"]["owner"]=="ASSET_CONTRACT",s
        assert "interaction" in s["evidence"]["completed_checks"],s
        assert "responsive" in s["evidence"]["completed_checks"],s
        assert "asset_integrity" in s["evidence"]["completed_checks"],s
        assert "visual" in s["evidence"]["deferred_checks"],s
        assert (root/"ui-audit/interaction-result.json").is_file()
        assert (root/"ui-audit/responsive-result.json").is_file()
        assert (root/"ui-audit/asset-result.json").is_file()
        assert not (root/"ui-audit/design-receipt.json").exists()

    with tempfile.TemporaryDirectory() as td:
        root=Path(td);setup(root)
        a=json.loads((root/"design-ui-adapter.json").read_text())
        a["checks"]["interaction"]["coverage"]=[]
        write(root/"design-ui-adapter.json",a)
        git_commit(root,"coverage mutation")
        cp=run(root)
        assert cp.returncode!=0
        s=json.loads((root/"ui-audit/pipeline-status.json").read_text())
        assert s["status"]=="CONTRACT_BLOCKED",s
        assert "ADAPTER_COVERAGE_MISSING:interaction:home:BASE" in s["detail"],s

    with tempfile.TemporaryDirectory() as td:
        root=Path(td);setup(root)
        m=json.loads((root/"design-to-ui.json").read_text())
        m["screens"][0]["states"][0]["interaction_policy"]="NOT_APPLICABLE"
        write(root/"design-to-ui.json",m)
        a=json.loads((root/"design-ui-adapter.json").read_text())
        a["checks"]["interaction"]["coverage"]=[]
        write(root/"design-ui-adapter.json",a)
        git_commit(root,"not applicable mutation")
        cp=run(root)
        assert cp.returncode==0,(cp.stdout,cp.stderr)
        s=json.loads((root/"ui-audit/pipeline-status.json").read_text())
        assert s["status"]=="DESIGN_PASS",s
        evidence=json.loads((root/"ui-audit/interaction-result.json").read_text())
        assert evidence["coverage"]==[],evidence

    print("DESIGN_TO_UI_PIPELINE_RUNNER_V1=PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
