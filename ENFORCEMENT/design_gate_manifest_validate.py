#!/usr/bin/env python3
"""TAKY Design Gate V1 manifest validator.

Validates authority/provenance requirements only.
Pixel/render comparison remains the responsibility of the consumer app's browser test.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

SCHEMA="TAKY_DESIGN_GATE_V1"
RULE="TKY-ASSET-001"
SHA_RE=re.compile(r"^[0-9a-fA-F]{64}$")

def sha256(p: Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def validate(cfg: dict, root: Path)->list[str]:
    e=[]
    if cfg.get("schema") != SCHEMA: e.append("SCHEMA_INVALID")
    if cfg.get("rule_id") != RULE: e.append("RULE_BINDING_MISSING")
    if not str(cfg.get("project","")).strip(): e.append("PROJECT_MISSING")
    screens=cfg.get("screens")
    if not isinstance(screens,list) or not screens:
        e.append("SCREENS_MISSING")
        return e
    seen=set()
    for s in screens:
        sid=str(s.get("id","")).strip()
        if not sid or sid in seen: e.append("SCREEN_ID_INVALID_OR_DUPLICATE")
        seen.add(sid)
        for key in ("authority_ref","approved_reference","snapshot_name"):
            if not str(s.get(key,"")).strip(): e.append(f"{sid}:{key.upper()}_MISSING")
        ref=str(s.get("approved_reference",""))
        if ref:
            p=(root/ref).resolve()
            try: p.relative_to(root.resolve())
            except ValueError:
                e.append(f"{sid}:REFERENCE_ESCAPES_ROOT"); continue
            if not p.is_file() or p.stat().st_size == 0:
                e.append(f"{sid}:APPROVED_REFERENCE_MISSING"); continue
            expected=str(s.get("approved_sha256",""))
            if not SHA_RE.match(expected): e.append(f"{sid}:APPROVED_SHA_MISSING")
            elif sha256(p).lower()!=expected.lower(): e.append(f"{sid}:APPROVED_SHA_MISMATCH")
        elif not SHA_RE.match(str(s.get("approved_sha256",""))):
            e.append(f"{sid}:APPROVED_SHA_MISSING")
    pol=cfg.get("policy",{})
    for k in ("current_runtime_must_not_auto_become_golden","approved_reference_required","hash_pin_required","visual_diff_required"):
        if pol.get(k) is not True: e.append(f"POLICY_{k.upper()}_NOT_HARD")
    return e

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--root",type=Path,default=Path.cwd())
    a=ap.parse_args()
    cfg=json.loads(a.manifest.read_text(encoding="utf-8"))
    errors=validate(cfg,a.root)
    print(json.dumps({"pass":not errors,"detected":errors},ensure_ascii=False,indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
