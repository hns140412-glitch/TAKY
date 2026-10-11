#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_REPORT.py"
BIND=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_BIND.py"
BUILD=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_BUILD.py"
RENDER=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_RENDER.py"
QUALITY=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_QUALITY.py"

def run(cmd):
    proc=subprocess.run(cmd,capture_output=True,text=True)
    if proc.returncode!=0:
        raise RuntimeError((proc.stderr or proc.stdout)[-3000:])
    return proc.stdout.strip()

def main():
    p=argparse.ArgumentParser(description="One-shot architecture competition representation/output pipeline.")
    p.add_argument("--project-type",default="default")
    p.add_argument("--delivery",default="A3_REPORT",choices=["A1_BOARD","A3_REPORT","PPT","PDF_DRAWING_BOOK"])
    p.add_argument("--focus",default="")
    p.add_argument("--brief-file",default="")
    p.add_argument("--brief-verified",action="store_true")
    p.add_argument("--content-frozen",action="store_true")
    p.add_argument("--source-dir",default="")
    p.add_argument("--out-dir",required=True)
    p.add_argument("--no-render",action="store_true")
    args=p.parse_args()

    out=Path(args.out_dir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    package=out/"package.json"

    report_cmd=[
        sys.executable,str(REPORT),
        "--project-type",args.project_type,
        "--delivery",args.delivery,
        "--focus",args.focus,
        "--json","--output",str(package)
    ]
    if args.brief_file:
        report_cmd += ["--brief-file",str(Path(args.brief_file).resolve())]
    if args.brief_verified:
        report_cmd += ["--brief-verified"]
    if args.content_frozen:
        report_cmd += ["--content-frozen"]
    run(report_cmd)

    bindings=None
    if args.source_dir:
        bindings=out/"source-bindings.json"
        run([
            sys.executable,str(BIND),
            "--package",str(package),
            "--source-dir",str(Path(args.source_dir).resolve()),
            "--output",str(bindings)
        ])

    build_cmd=[sys.executable,str(BUILD),"--package",str(package),"--out-dir",str(out)]
    if bindings:
        build_cmd += ["--sources",str(bindings)]
    run(build_cmd)

    render_result=None
    quality_result=None
    if not args.no_render:
        render_text=run([sys.executable,str(RENDER),"--build-dir",str(out)])
        render_result=json.loads(render_text)
        quality_proc=subprocess.run(
            [sys.executable,str(QUALITY),"--build-dir",str(out)],
            capture_output=True,text=True
        )
        quality_text=(quality_proc.stdout or "").strip()
        if quality_text:
            quality_result=json.loads(quality_text)

    manifest=json.loads((out/"build-manifest.json").read_text(encoding="utf-8"))
    validation=json.loads((out/"validation.json").read_text(encoding="utf-8"))
    summary={
        "ok":True,
        "delivery":manifest["delivery"],
        "manifest_status":manifest["status"],
        "source_gap_count":len(validation.get("source_gaps",[])),
        "rendered":render_result is not None,
        "mechanical_render_pass":bool((render_result or {}).get("mechanical_render_pass")),
        "quality_status":(quality_result or {}).get("status"),
        "quality_hard_pass":bool((quality_result or {}).get("hard_pass")),
        "quality_errors":(quality_result or {}).get("errors",[]),
        "quality_warnings":(quality_result or {}).get("warnings",[]),
        "final_status":validation.get("status") or ("BUILT_UNRENDERED" if args.no_render else None),
        "out_dir":str(out),
        "next_gate":(
            "VISUAL_SOURCE_CROSS_CHECK"
            if not validation.get("source_gaps") and render_result and (quality_result or {}).get("hard_pass")
            else ("IMPROVE_QUALITY" if render_result and quality_result else "RESOLVE_SOURCE_GAPS")
        )
    }
    (out/"run-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
