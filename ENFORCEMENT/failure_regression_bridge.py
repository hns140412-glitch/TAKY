#!/usr/bin/env python3
"""Bridge durable TAKY failure learning into regression candidates without auto-promotion."""
from __future__ import annotations
import json
from pathlib import Path
from trace_to_regression import build_case

def load_jsonl(path:Path):
    if not path.exists(): return []
    rows=[]
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        try: rows.append(json.loads(line))
        except Exception: continue
    return rows

def unresolved_repeated_failures(rows):
    recovered={r.get("failed_sig") for r in rows if r.get("kind")=="RECOVERY_ROUTE"}
    latest={}
    for r in rows:
        if r.get("kind")=="REPEATED_FAILURE" and r.get("failed_sig"):
            latest[r["failed_sig"]]=r
    return [r for sig,r in latest.items() if sig not in recovered]

def to_regression_candidate(failure, expected):
    event={
        "outcome_state":"FAILED_CONFIRMED",
        "source_ref":"FAILURE_LEDGER:"+str(failure.get("failed_sig") or ""),
        "invariant":"Do not repeat an unchanged route after repeated confirmed failure",
        "observed":{"cause":failure.get("cause"),"action":failure.get("action"),
                    "error_fingerprint":failure.get("error_fingerprint")},
        "expected":expected,
        "task_family":"TAKY_EXECUTION_RECOVERY"
    }
    return build_case(event)

def summarize(path:Path):
    rows=load_jsonl(path)
    unresolved=unresolved_repeated_failures(rows)
    return {"events":len(rows),"unresolved_repeated_failures":len(unresolved),
            "candidate_count":len(unresolved),"auto_promote":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--ledger",required=True)
    a=p.parse_args(); print(json.dumps(summarize(Path(a.ledger)),ensure_ascii=False,indent=2))
