#!/usr/bin/env python3
import json, sys
from pathlib import Path

def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)

def main(path):
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    if d.get("authority") not in {"REFERENCE_ONLY","EVIDENCE_ASSIST"}:
        fail("NotebookLM output authority must be REFERENCE_ONLY/EVIDENCE_ASSIST")
    if d.get("canonical_status") not in {"NOT_CANONICAL","PENDING_RAW_RECHECK"}:
        fail("NotebookLM output cannot arrive as canonical")
    srcs=d.get("source_refs")
    if not isinstance(srcs,list) or not srcs: fail("source_refs required")
    candidates=d.get("candidates")
    if not isinstance(candidates,list): fail("candidates must be list")
    for i,c in enumerate(candidates):
        cid=c.get("candidate_id") or f"candidate[{i}]"
        for k in ("source_ref","actor","semantic_content","candidate_disposition","needs_raw_recheck"):
            if k not in c: fail(f"{cid}: missing {k}")
        if c.get("source_ref") not in srcs:
            fail(f"{cid}: source_ref not declared")
        if c.get("needs_raw_recheck") is not True:
            fail(f"{cid}: NotebookLM candidate must require raw recheck")
        if c.get("canonicalized") is True:
            fail(f"{cid}: candidate cannot be canonicalized at intake")
        if c.get("actor") not in {"USER","ASSISTANT","SYSTEM","UNKNOWN"}:
            fail(f"{cid}: invalid actor")
    cov=d.get("coverage") or {}
    if cov.get("claims_full_account_history") is True:
        fail("NotebookLM intake must not claim full account history unless separately verified")
    print(f"PASS: NotebookLM intake {d.get('output_id','<no-output-id>')} candidates={len(candidates)}")

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: notebooklm_output_intake_validator.py <output.json>")
        raise SystemExit(2)
    main(sys.argv[1])
