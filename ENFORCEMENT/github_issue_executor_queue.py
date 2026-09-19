#!/usr/bin/env python3
"""GitHub Issue queue formatter/parser for TAKY executor dispatch.

This module is deliberately network-free. It converts an integrity-bound dispatch
envelope into a GitHub Issue payload and parses executor receipt/result comments.
Actual GitHub mutation is performed by an authorized GitHub connector/adapter.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BEGIN_DISPATCH="<!-- TAKY_EXECUTOR_DISPATCH_JSON_BEGIN -->"
END_DISPATCH="<!-- TAKY_EXECUTOR_DISPATCH_JSON_END -->"
BEGIN_RECEIPT="<!-- TAKY_EXECUTOR_RECEIPT_JSON_BEGIN -->"
END_RECEIPT="<!-- TAKY_EXECUTOR_RECEIPT_JSON_END -->"
BEGIN_RESULT="<!-- TAKY_EXECUTOR_RESULT_JSON_BEGIN -->"
END_RESULT="<!-- TAKY_EXECUTOR_RESULT_JSON_END -->"

def issue_payload(envelope: dict) -> dict:
    task_id=str(envelope.get("task_id","")).strip()
    digest=str(envelope.get("task_contract_sha256","")).strip()
    provider=str(envelope.get("provider","")).strip().upper()
    if not task_id or not digest or not provider:
        return {"pass":False,"detected":["GITHUB_QUEUE_ENVELOPE_INCOMPLETE"],"issue":None}

    title=f"[TAKY EXECUTOR QUEUE] {task_id} -> {provider}"
    body=(
        "TAKY controlled executor dispatch.\n\n"
        "**Do not edit the machine block.** Executor adapters should post a receipt "
        "and later a result comment using the documented machine markers.\n\n"
        f"- Task ID: `{task_id}`\n"
        f"- Provider: `{provider}`\n"
        f"- Contract SHA256: `{digest}`\n"
        f"- Dispatch status: `{envelope.get('dispatch_status','DISPATCH_READY')}`\n\n"
        f"{BEGIN_DISPATCH}\n"
        f"{json.dumps(envelope,ensure_ascii=False,sort_keys=True)}\n"
        f"{END_DISPATCH}\n"
    )
    return {
        "pass":True,
        "detected":[],
        "issue":{
            "title":title,
            "body":body,
            "labels":["taky-executor-queue"]
        }
    }

def _extract(text:str, begin:str, end:str):
    pattern=re.escape(begin)+r"\s*(\{.*?\})\s*"+re.escape(end)
    m=re.search(pattern,text,re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

def parse_comment(text:str) -> dict:
    receipt=_extract(text,BEGIN_RECEIPT,END_RECEIPT)
    result=_extract(text,BEGIN_RESULT,END_RESULT)
    if receipt is None and result is None:
        return {"pass":False,"detected":["GITHUB_QUEUE_MACHINE_BLOCK_MISSING"]}
    return {"pass":True,"detected":[],"receipt":receipt,"result":result}

def main()->int:
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("issue")
    p.add_argument("--envelope",type=Path,required=True)
    p.add_argument("--output",type=Path)
    q=sub.add_parser("parse-comment")
    q.add_argument("--comment",type=Path,required=True)
    args=ap.parse_args()

    if args.cmd=="issue":
        env=json.loads(args.envelope.read_text(encoding="utf-8"))
        out=issue_payload(env)
        if out["pass"] and args.output:
            args.output.write_text(json.dumps(out["issue"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:
        out=parse_comment(args.comment.read_text(encoding="utf-8"))
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
