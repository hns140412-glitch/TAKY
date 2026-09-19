#!/usr/bin/env python3
"""Build an idempotent TAKY GitHub queue polling plan from one issue snapshot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from github_queue_consumer import consume, QUEUE_PREFIX
from github_issue_executor_queue import BEGIN_RECEIPT, BEGIN_RESULT

ISSUE_ACK="<!-- TAKY_QUEUE_ISSUE_ACK -->"
SOURCE_PREFIX="<!-- TAKY_QUEUE_SOURCE_COMMENT:"

def plan(snapshot: dict) -> dict:
    title=str(snapshot.get("title",""))
    if not title.startswith(QUEUE_PREFIX):
        return {"pass":True,"comments_to_publish":[],"processed":[]}

    issue={
        "number":snapshot.get("number"),
        "title":title,
        "body":snapshot.get("body") or "",
    }
    comments=snapshot.get("comments") or []
    bodies=[str(c.get("body") or "") for c in comments if isinstance(c,dict)]
    out=[]
    processed=[]

    if not any(ISSUE_ACK in b for b in bodies):
        result=consume({"_event_name":"issues","issue":issue})
        if result.get("comment"):
            out.append(result["comment"])
            processed.append({"kind":"issue","action":result.get("action")})

    for c in comments:
        if not isinstance(c,dict):
            continue
        cid=c.get("id")
        body=str(c.get("body") or "")
        if BEGIN_RECEIPT not in body and BEGIN_RESULT not in body:
            continue
        marker=f"{SOURCE_PREFIX}{cid} -->"
        if any(marker in b for b in bodies):
            continue
        result=consume({"_event_name":"issue_comment","issue":issue,"comment":{"id":cid,"body":body}})
        if result.get("comment"):
            out.append(result["comment"])
            processed.append({"kind":"comment","comment_id":cid,"action":result.get("action")})

    return {"pass":True,"comments_to_publish":out,"processed":processed}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    snapshot=json.loads(args.snapshot.read_text(encoding="utf-8"))
    result=plan(snapshot)
    if args.output:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
