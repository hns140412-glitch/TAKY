#!/usr/bin/env python3
"""TAKY Design-to-UI Pipeline Runner V1.

One orchestrator for:
contract -> capture -> visual -> interaction -> responsive -> asset -> receipt.

App-specific work is delegated to argv-only adapters. shell=True is never used.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
VALIDATOR=HERE/"design_to_ui_pipeline_validate.py"
VISUAL=HERE/"design_visual_compare_v2.py"
RECEIPT=HERE/"design_to_ui_receipt_issue.py"

STATUSES={
    "contract":"CONTRACT_BLOCKED",
    "capture":"CAPTURE_BLOCKED",
    "visual":"VISUAL_BLOCKED",
    "interaction":"INTERACTION_BLOCKED",
    "responsive":"RESPONSIVE_BLOCKED",
    "asset_integrity":"ASSET_BLOCKED",
    "receipt":"RECEIPT_BLOCKED",
}
EXPECTED_OUTPUTS={
    "capture":"ui-audit/render-manifest.json",
    "interaction":"ui-audit/interaction-result.json",
    "responsive":"ui-audit/responsive-result.json",
    "asset_integrity":"ui-audit/asset-result.json",
}
EXPECTED_KINDS={
    "interaction":"INTERACTION",
    "responsive":"RESPONSIVE",
    "asset_integrity":"ASSET_INTEGRITY",
}

def sha256(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def safe(root: Path, rel: str)->Path:
    p=(root/rel).resolve()
    p.relative_to(root.resolve())
    return p

def route_failure(stage: str, detail: str, evidence: dict|None=None)->dict:
    evidence=evidence or {}
    blockers=evidence.get("blockers") or []
    joined=";".join(str(x) for x in blockers)

    if stage=="contract":
        if "GOLDEN_" in joined or "SOURCE_" in detail or "SHA_" in detail:
            return {"return_to_stage":"APPROVAL_LOCK","owner":"AUTHORITY","next_action":"resolve approved source / Golden authority and rerun full pipeline"}
        if "ASSET_IMPORT_OPEN" in joined or "ASSET_PRODUCTION_OPEN" in joined:
            return {"return_to_stage":"UI_CONTRACT","owner":"ASSET_CONTRACT","next_action":"resolve declared asset blocker without inventing replacement art, then rerun full pipeline"}
        if "IMPLEMENTATION_OPEN" in joined:
            return {"return_to_stage":"IMPLEMENT","owner":"UI_IMPLEMENTATION","next_action":"implement the declared missing DOM/component/slot, then rerun full pipeline"}
        if detail.startswith("ADAPTER_"):
            return {"return_to_stage":"VERIFY_CORRECT","owner":"APP_ADAPTER","next_action":"repair adapter contract and rerun full pipeline"}
        return {"return_to_stage":"UI_CONTRACT","owner":"UI_CONTRACT","next_action":"repair manifest/screen/layer/state contract and rerun full pipeline"}

    if stage=="capture":
        return {"return_to_stage":"VERIFY_CORRECT","owner":"APP_ADAPTER","next_action":"repair deterministic browser capture adapter/output and rerun full pipeline"}
    if stage=="visual":
        return {"return_to_stage":"IMPLEMENT","owner":"UI_IMPLEMENTATION","next_action":"inspect visual diff/critical ROI, correct UI implementation, and rerun full pipeline"}
    if stage=="interaction":
        return {"return_to_stage":"IMPLEMENT","owner":"UI_IMPLEMENTATION","next_action":"correct interaction/state behavior and rerun full pipeline"}
    if stage=="responsive":
        return {"return_to_stage":"IMPLEMENT","owner":"UI_IMPLEMENTATION","next_action":"correct responsive layout/safe-area behavior; update contract only if approved rule was incomplete; rerun full pipeline"}
    if stage=="asset_integrity":
        return {"return_to_stage":"UI_CONTRACT","owner":"ASSET_CONTRACT","next_action":"repair approved asset binding/provenance/hash and rerun full pipeline"}
    if stage=="receipt":
        return {"return_to_stage":"VERIFY_CORRECT","owner":"PIPELINE","next_action":"repair evidence identity/coverage mismatch and rerun full pipeline"}
    return {"return_to_stage":"VERIFY_CORRECT","owner":"PIPELINE","next_action":"inspect failure and rerun full pipeline"}

def write_status(root: Path, status: str, stage: str, detail: str="", evidence: dict|None=None, routing: dict|None=None)->None:
    out=root/"ui-audit/pipeline-status.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    payload={
        "schema":"TAKY_DESIGN_TO_UI_PIPELINE_STATUS_V1",
        "status":status,
        "stage":stage,
        "detail":detail,
        "evidence":evidence or {},
        "routing":routing,
    }
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False,indent=2))

def fail(root: Path, stage: str, detail: str, evidence: dict|None=None)->int:
    routing=route_failure(stage,detail,evidence)
    write_status(root,STATUSES.get(stage,"CONTRACT_BLOCKED"),stage,detail,evidence,routing)
    return 1

def run(argv: list[str], cwd: Path)->subprocess.CompletedProcess:
    return subprocess.run(argv,cwd=cwd,text=True,capture_output=True,shell=False)

def validate_adapter(cfg: dict, root: Path)->list[str]:
    errors=[]
    if cfg.get("schema")!="TAKY_DESIGN_UI_ADAPTER_V1":
        errors.append("ADAPTER_SCHEMA_INVALID")
    commands=cfg.get("commands")
    if not isinstance(commands,dict):
        errors.append("ADAPTER_COMMANDS_MISSING")
        return errors
    for name in ("capture","interaction","responsive","asset_integrity"):
        argv=commands.get(name)
        if not isinstance(argv,list) or not argv or any(not isinstance(x,str) or not x for x in argv):
            errors.append(f"ADAPTER_COMMAND_INVALID:{name}")
    outputs=cfg.get("outputs")
    if not isinstance(outputs,dict):
        errors.append("ADAPTER_OUTPUTS_MISSING")
    else:
        expected={
            "render_manifest":"ui-audit/render-manifest.json",
            "interaction":"ui-audit/interaction-result.json",
            "responsive":"ui-audit/responsive-result.json",
            "asset_integrity":"ui-audit/asset-result.json",
        }
        for key,value in expected.items():
            if outputs.get(key)!=value:
                errors.append(f"ADAPTER_OUTPUT_INVALID:{key}")
    return errors

def evidence_check(path: Path, kind: str, manifest_sha: str, source_commit: str)->str|None:
    if not path.is_file():
        return "EVIDENCE_MISSING"
    try:
        data=read_json(path)
    except Exception:
        return "EVIDENCE_JSON_INVALID"
    if data.get("schema")!="TAKY_DESIGN_EVIDENCE_V1":
        return "EVIDENCE_SCHEMA_INVALID"
    if data.get("kind")!=kind:
        return "EVIDENCE_KIND_MISMATCH"
    if data.get("pass") is not True:
        return "EVIDENCE_NOT_PASS"
    if data.get("manifest_sha256")!=manifest_sha:
        return "EVIDENCE_MANIFEST_SHA_MISMATCH"
    if data.get("source_commit")!=source_commit:
        return "EVIDENCE_SOURCE_COMMIT_MISMATCH"
    if not isinstance(data.get("coverage"),list):
        return "EVIDENCE_COVERAGE_INVALID"
    return None

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path.cwd())
    ap.add_argument("--manifest",default="design-to-ui.json")
    ap.add_argument("--adapter",default="design-ui-adapter.json")
    args=ap.parse_args()

    root=args.root.resolve()
    manifest_path=safe(root,args.manifest)
    adapter_path=safe(root,args.adapter)
    audit=root/"ui-audit"
    audit.mkdir(parents=True,exist_ok=True)
    contract_out=audit/"contract-validation.json"

    if not manifest_path.is_file():
        return fail(root,"contract","MANIFEST_MISSING")
    if not adapter_path.is_file():
        return fail(root,"contract","ADAPTER_MISSING")

    try:
        manifest=read_json(manifest_path)
        adapter=read_json(adapter_path)
    except Exception as e:
        return fail(root,"contract","JSON_INVALID:"+type(e).__name__)

    adapter_errors=validate_adapter(adapter,root)
    if adapter_errors:
        return fail(root,"contract",";".join(adapter_errors))

    cp=run([sys.executable,str(VALIDATOR),str(manifest_path),"--root",str(root),"--out",str(contract_out)],root)
    if cp.returncode!=0:
        return fail(root,"contract","CONTRACT_VALIDATOR_FAILED",{"stdout":cp.stdout[-4000:],"stderr":cp.stderr[-2000:]})
    try:
        cv=read_json(contract_out)
    except Exception:
        return fail(root,"contract","CONTRACT_VALIDATION_RESULT_INVALID")
    if cv.get("contract_valid") is not True:
        return fail(root,"contract","CONTRACT_INVALID")
    contract_blockers=list(cv.get("blockers") or [])

    manifest_sha=sha256(manifest_path)
    source_commit=str(manifest.get("source_commit",""))

    # Capture first because central Visual Compare owns VISUAL evidence.
    cp=run(adapter["commands"]["capture"],root)
    render_manifest=audit/"render-manifest.json"
    if cp.returncode!=0:
        return fail(root,"capture","ADAPTER_COMMAND_FAILED",{"stderr":cp.stderr[-2000:]})
    if not render_manifest.is_file():
        return fail(root,"capture","RENDER_MANIFEST_MISSING")

    visual_out=audit/"visual-result.json"
    visual_blocker_tokens=("GOLDEN_IMPORT_OPEN","ASSET_IMPORT_OPEN","ASSET_PRODUCTION_OPEN","IMPLEMENTATION_OPEN")
    visual_deferred=any(any(token in str(blocker) for token in visual_blocker_tokens) for blocker in contract_blockers)
    completed_checks=["contract","capture"]
    deferred_checks=[]

    if visual_deferred:
        deferred_checks.append("visual")
    else:
        cp=run([
            sys.executable,str(VISUAL),
            "--manifest",str(manifest_path),
            "--render-manifest",str(render_manifest),
            "--root",str(root),
            "--out","ui-audit/visual-result.json",
            "--diff-dir","ui-audit/diff",
        ],root)
        if cp.returncode!=0:
            return fail(root,"visual","VISUAL_COMPARE_FAILED",{"result":"ui-audit/visual-result.json"})
        completed_checks.append("visual")

    for stage in ("interaction","responsive","asset_integrity"):
        cp=run(adapter["commands"][stage],root)
        if cp.returncode!=0:
            return fail(root,stage,"ADAPTER_COMMAND_FAILED",{"stderr":cp.stderr[-2000:]})
        path=root/EXPECTED_OUTPUTS[stage]
        problem=evidence_check(path,EXPECTED_KINDS[stage],manifest_sha,source_commit)
        if problem:
            return fail(root,stage,problem,{"result":EXPECTED_OUTPUTS[stage],"contract_blockers":contract_blockers})
        completed_checks.append(stage)

    if contract_blockers:
        return fail(root,"contract","UNRESOLVED_CONTRACT_BLOCKERS",{
            "blockers":contract_blockers,
            "completed_checks":completed_checks,
            "deferred_checks":deferred_checks,
        })

    receipt=audit/"design-receipt.json"
    cp=run([
        sys.executable,str(RECEIPT),
        "--manifest",str(manifest_path),
        "--contract-validation",str(contract_out),
        "--visual",str(visual_out),
        "--interaction",str(audit/"interaction-result.json"),
        "--responsive",str(audit/"responsive-result.json"),
        "--asset",str(audit/"asset-result.json"),
        "--out",str(receipt),
    ],root)
    if cp.returncode!=0:
        return fail(root,"receipt","RECEIPT_ISSUE_FAILED",{"stderr":cp.stderr[-2000:]})

    write_status(root,"DESIGN_PASS","design_pass","ALL_REQUIRED_DESIGN_EVIDENCE_PASS",{
        "contract":"ui-audit/contract-validation.json",
        "visual":"ui-audit/visual-result.json",
        "interaction":"ui-audit/interaction-result.json",
        "responsive":"ui-audit/responsive-result.json",
        "asset_integrity":"ui-audit/asset-result.json",
        "receipt":"ui-audit/design-receipt.json",
    },None)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
