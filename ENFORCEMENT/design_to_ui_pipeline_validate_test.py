#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "design_to_ui_pipeline_validate.py"
RECEIPT = HERE / "design_to_ui_receipt_issue.py"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write_json(p: Path, data: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def run(*args, expect=0):
    cp = subprocess.run([sys.executable, *map(str,args)], text=True, capture_output=True)
    if cp.returncode != expect:
        raise AssertionError(f"return={cp.returncode} expected={expect}\nSTDOUT\n{cp.stdout}\nSTDERR\n{cp.stderr}")
    return cp

def build(root: Path, open_asset: bool):
    (root/"design/golden").mkdir(parents=True, exist_ok=True)
    (root/"design/contracts").mkdir(parents=True, exist_ok=True)
    (root/"design/fixtures").mkdir(parents=True, exist_ok=True)
    (root/"assets").mkdir(parents=True, exist_ok=True)

    golden = root/"design/golden/home.png"
    golden.write_bytes(b"approved-golden-bytes")
    fixture_a = root/"design/fixtures/home-initial.json"
    fixture_b = root/"design/fixtures/home-empty.json"
    write_json(fixture_a, {"fixture":"INITIAL"})
    write_json(fixture_b, {"fixture":"EMPTY"})
    asset = root/"assets/dummy.bin"
    asset.write_bytes(b"approved-production-layer")

    screen_contract = root/"design/contracts/home.screen.json"
    write_json(screen_contract, {
        "schema":"TAKY_SCREEN_CONTRACT_V2",
        "screen_id":"home",
        "regions":[{"id":"main"}],
        "typography":{"primary":"system"},
        "components":[{"id":"root"}],
        "responsive":{"safe_area":True},
        "interactions":[{"id":"tap"}],
        "states":["INITIAL","EMPTY"]
    })

    layer_contract = root/"design/contracts/home.layers.json"
    layers=[]
    for role in ["BACKGROUND","FOREGROUND","OBJECT","CHARACTER_SLOT","FUNCTION_UI"]:
        if open_asset and role=="BACKGROUND":
            layers.append({"role":role,"status":"ASSET_PRODUCTION_OPEN"})
        else:
            layers.append({"role":role,"status":"BOUND","path":"assets/dummy.bin","sha256":sha(asset)})
    write_json(layer_contract, {
        "schema":"TAKY_LAYER_CONTRACT_V1",
        "screen_id":"home",
        "layers":layers
    })

    manifest = {
        "schema":"TAKY_DESIGN_TO_UI_PIPELINE_V1",
        "project":"TEST_APP",
        "source_commit":"1"*40,
        "policy":{
            "runtime_must_not_auto_become_golden":True,
            "flattened_mockup_runtime_forbidden":True,
            "evidence_files_required":True,
            "image_generation_optional":True
        },
        "screens":[{
            "id":"home",
            "authority_ref":"USER_APPROVED_TEST",
            "golden":{"path":"design/golden/home.png","sha256":sha(golden),"use":"REFERENCE_ONLY"},
            "screen_contract":{"path":"design/contracts/home.screen.json","sha256":sha(screen_contract)},
            "layer_contract":{"path":"design/contracts/home.layers.json","sha256":sha(layer_contract)},
            "viewports":[{"id":"phone","width":390,"height":844,"dpr":2}],
            "states":[
                {"id":"INITIAL","fixture_path":"design/fixtures/home-initial.json","fixture_sha256":sha(fixture_a)},
                {"id":"EMPTY","fixture_path":"design/fixtures/home-empty.json","fixture_sha256":sha(fixture_b)}
            ]
        }]
    }
    manifest_path=root/"design-to-ui.json"
    write_json(manifest_path, manifest)
    return manifest_path, golden, layer_contract

def evidence(path: Path, kind: str, manifest: Path, coverage: list[str]):
    m=json.loads(manifest.read_text(encoding="utf-8"))
    write_json(path,{
        "schema":"TAKY_DESIGN_EVIDENCE_V1",
        "kind":kind,
        "pass":True,
        "manifest_sha256":sha(manifest),
        "source_commit":m["source_commit"],
        "coverage":coverage
    })

def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)

        # 1) Missing art can remain OPEN without invalidating the contract.
        manifest, golden, _ = build(root, open_asset=True)
        validation=root/"validation-open.json"
        run(VALIDATOR, manifest, "--root", root, "--out", validation)
        v=json.loads(validation.read_text())
        assert v["contract_valid"] is True
        assert v["design_pass_ready"] is False
        assert any("ASSET_PRODUCTION_OPEN" in x for x in v["blockers"])

        # 2) All bound layers -> ready for evidence.
        manifest, golden, _ = build(root, open_asset=False)
        validation=root/"validation.json"
        run(VALIDATOR, manifest, "--root", root, "--out", validation)
        v=json.loads(validation.read_text())
        assert v["contract_valid"] is True and v["design_pass_ready"] is True

        audit=root/"ui-audit"
        visual=audit/"visual-result.json"
        interaction=audit/"interaction-result.json"
        responsive=audit/"responsive-result.json"
        asset=audit/"asset-result.json"
        evidence(visual,"VISUAL",manifest,["home:INITIAL:phone","home:EMPTY:phone"])
        evidence(interaction,"INTERACTION",manifest,["home:INITIAL","home:EMPTY"])
        evidence(responsive,"RESPONSIVE",manifest,["home:INITIAL:phone","home:EMPTY:phone"])
        evidence(asset,"ASSET_INTEGRITY",manifest,["home"])
        receipt=audit/"design-receipt.json"
        run(RECEIPT,
            "--manifest",manifest,
            "--contract-validation",validation,
            "--visual",visual,
            "--interaction",interaction,
            "--responsive",responsive,
            "--asset",asset,
            "--out",receipt)
        r=json.loads(receipt.read_text())
        assert r["pass"] is True and len(r["evidence"])==4

        # 3) Golden tamper must fail closed.
        golden.write_bytes(b"tampered")
        run(VALIDATOR, manifest, "--root", root, expect=1)
        golden.write_bytes(b"approved-golden-bytes")

        # 4) Missing evidence coverage must block receipt.
        evidence(visual,"VISUAL",manifest,["home:INITIAL:phone"])
        cp=subprocess.run([
            sys.executable,str(RECEIPT),
            "--manifest",str(manifest),
            "--contract-validation",str(validation),
            "--visual",str(visual),
            "--interaction",str(interaction),
            "--responsive",str(responsive),
            "--asset",str(asset),
            "--out",str(receipt)
        ],text=True,capture_output=True)
        assert cp.returncode != 0 and "VISUAL_COVERAGE_MISSING" in (cp.stdout+cp.stderr)

    print("DESIGN_TO_UI_PIPELINE_V1_REGRESSION=PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
