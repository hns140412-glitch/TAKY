#!/usr/bin/env python3
"""Safe local rebuild entrypoint for TAKY chat+work progress dashboards.

Only reads authorized existing local export intake and Workbench sources.
No undocumented ChatGPT API, no model, paid call, Git modification or deploy.
Fails closed on a stage error. Existing original texts and CURRENT untouched.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
STAGES=(
    "TAKY_CONVERSATION_FUTURE_SYNC.py",
    "TAKY_OCTOBER_CONVERSATION_EVIDENCE.py",
    "TAKY_CONVERSATION_PROGRESS_BOARD.py",
    "TAKY_CONVERSATION_UNIFIED_VIEW.py",
)
def run(check_only=False):
    results=[]
    for name in STAGES:
        script=HERE/name
        if not script.is_file():raise FileNotFoundError("REQUIRED_STAGE_MISSING:"+name)
        if check_only:
            results.append({"stage":name,"state":"AVAILABLE"})
            continue
        cmd=[sys.executable,"-B",str(script)]
        try:
            r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             encoding="utf-8",errors="replace",timeout=90,check=False,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except subprocess.TimeoutExpired:
            raise RuntimeError("STAGE_TIMEOUT:"+name)
        if r.returncode!=0:
            raise RuntimeError("STAGE_FAILED:"+name+":"+r.stderr[-550:])
        last=r.stdout.strip().splitlines()
        try:
            output=json.loads(last[-1]) if last else {}
        except ValueError:
            raise RuntimeError("STAGE_RECEIPT_NOT_JSON:"+name)
        results.append({"stage":name,"receipt":output})
    return {"schema":"TAKY_CONVERSATION_REFRESH_LOCAL_V1",
            "mode":"CHECK_ONLY" if check_only else "LOCAL_DERIVED_REFRESH",
            "stages":results,
            "native_chat_coverage":"EXPORT_SOURCES_ONLY_NOT_ACCOUNT_COMPLETE",
            "canonical_modified":False,
            "git_push_merge_deploy":False,
            "paid_api_calls":0}
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-only",action="store_true")
    args=ap.parse_args()
    print(json.dumps(run(check_only=args.check_only),ensure_ascii=False))
