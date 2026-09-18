#!/usr/bin/env python3
import json
import sys
from pathlib import Path

DIRECT_INPUT_CLASSES = {"RAW_CONVERSATION","PRESERVED_TRANSCRIPT","RECOVERY_WITNESS","ORIGINAL_ATTACHMENT","PAGE_CAPTURE","HANDOFF","DERIVED_ANALYSIS","CANONICAL_REFERENCE"}

def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)

def main(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    sources=data.get("sources")
    if not isinstance(sources,list):
        fail("sources must be a list")
    ids=set()
    for i,s in enumerate(sources):
        sid=s.get("source_id")
        if not sid: fail(f"source[{i}] missing source_id")
        if sid in ids: fail(f"duplicate source_id: {sid}")
        ids.add(sid)
        cls=s.get("source_class")
        eligible=s.get("notebooklm_eligible")
        checked=s.get("content_checked")
        sec=s.get("security_status")
        auth=s.get("authority_status")
        has_auth=bool(s.get("contains_session_or_auth_data",False))

        if eligible:
            if checked is not True:
                fail(f"{sid}: NotebookLM-eligible source not content-checked")
            if sec != "SAFE_FOR_NOTEBOOKLM":
                fail(f"{sid}: NotebookLM-eligible source security_status={sec}")
            if has_auth:
                fail(f"{sid}: source with session/auth data cannot be NotebookLM-eligible")

        if cls == "NOTEBOOKLM_OUTPUT":
            if eligible:
                fail(f"{sid}: NotebookLM output cannot be reclassified as direct NotebookLM input by this registry")
            if auth not in {"REFERENCE_ONLY","EVIDENCE_ASSIST"}:
                fail(f"{sid}: NotebookLM output authority must remain REFERENCE_ONLY/EVIDENCE_ASSIST")

        if cls in {"HANDOFF","DERIVED_ANALYSIS"} and auth == "DIRECT_SOURCE":
            fail(f"{sid}: derived/handoff source cannot masquerade as DIRECT_SOURCE")

        if cls == "PAGE_CAPTURE" and has_auth and sec not in {"SECURITY_HOLD","SANITIZE_REQUIRED"}:
            fail(f"{sid}: page capture with auth/session data must be held/sanitized")

    print(f"PASS: {data.get('registry_id','<no-registry-id>')} sources={len(sources)}")

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: notebooklm_source_validator.py <source-registry.json>")
        raise SystemExit(2)
    main(sys.argv[1])
