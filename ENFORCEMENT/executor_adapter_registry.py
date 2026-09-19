#!/usr/bin/env python3
"""Resolve a task contract to an implemented TAKY executor adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_REGISTRY = Path("MASTER/EXECUTOR_ADAPTER_REGISTRY.json")

def resolve(task: dict, transport: str, registry: dict) -> dict:
    repo = str(task.get("repository","")).strip()
    automation = task.get("executor_automation") or {}
    validation = task.get("validation") or {}
    profile = str(automation.get("profile","")).strip()
    validation_profile = str(validation.get("profile","")).strip()
    transport = str(transport or "").strip().upper()

    matches=[]
    for a in registry.get("adapters",[]):
        if (
            a.get("repository")==repo
            and a.get("executor_profile")==profile
            and a.get("validation_profile")==validation_profile
            and str(a.get("transport","")).upper()==transport
            and a.get("queue_ready") is True
        ):
            matches.append(a)

    if len(matches)!=1:
        return {
            "pass":False,
            "detected":[
                "EXECUTOR_ADAPTER_NOT_FOUND" if not matches else "EXECUTOR_ADAPTER_AMBIGUOUS"
            ],
            "adapter":None
        }
    return {"pass":True,"detected":[],"adapter":matches[0]}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--task",type=Path,required=True)
    ap.add_argument("--transport",required=True)
    ap.add_argument("--registry",type=Path,default=DEFAULT_REGISTRY)
    args=ap.parse_args()
    task=json.loads(args.task.read_text(encoding="utf-8"))
    registry=json.loads(args.registry.read_text(encoding="utf-8"))
    out=resolve(task,args.transport,registry)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
