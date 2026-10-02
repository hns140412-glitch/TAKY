#!/usr/bin/env python3
"""Issue TAKY Design-to-UI evidence receipt from real evidence files.

No manual --*-pass switches exist by design.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
KINDS = ("VISUAL","INTERACTION","RESPONSIVE","ASSET_INTEGRITY")

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def canonical_hash(x: dict) -> str:
    raw = json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def expected_coverage(manifest: dict, kind: str) -> set[str]:
    rows = set()
    for screen in manifest.get("screens", []):
        sid = screen["id"]
        state_rows = screen.get("states", [])
        views = [v["id"] for v in screen.get("viewports", [])]
        if kind == "VISUAL":
            visual_states = [s["id"] for s in state_rows if s.get("visual_policy","GOLDEN_PARITY") == "GOLDEN_PARITY"]
            rows |= {f"{sid}:{state}:{view}" for state in visual_states for view in views}
        elif kind == "RESPONSIVE":
            responsive_states = [s["id"] for s in state_rows if s.get("responsive_policy","REQUIRED") == "REQUIRED"]
            rows |= {f"{sid}:{state}:{view}" for state in responsive_states for view in views}
        elif kind == "INTERACTION":
            interaction_states = [s["id"] for s in state_rows if s.get("interaction_policy","REQUIRED") == "REQUIRED"]
            rows |= {f"{sid}:{state}" for state in interaction_states}
        else:
            rows.add(sid)
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--contract-validation", required=True, type=Path)
    ap.add_argument("--visual", required=True, type=Path)
    ap.add_argument("--interaction", required=True, type=Path)
    ap.add_argument("--responsive", required=True, type=Path)
    ap.add_argument("--asset", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    manifest_sha = sha256(args.manifest)
    source_commit = str(manifest.get("source_commit",""))
    if not SHA40.match(source_commit):
        raise SystemExit("SOURCE_COMMIT_INVALID")

    cv = json.loads(args.contract_validation.read_text(encoding="utf-8"))
    if cv.get("contract_valid") is not True:
        raise SystemExit("CONTRACT_VALIDATION_NOT_PASS")
    if cv.get("design_pass_ready") is not True:
        raise SystemExit("DESIGN_NOT_READY_UNRESOLVED_LAYER_BLOCKER")

    evidence_paths = {
        "VISUAL": args.visual,
        "INTERACTION": args.interaction,
        "RESPONSIVE": args.responsive,
        "ASSET_INTEGRITY": args.asset,
    }
    evidence_rows = []
    tested_revision = None
    for kind, path in evidence_paths.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != "TAKY_DESIGN_EVIDENCE_V1":
            raise SystemExit(f"{kind}_EVIDENCE_SCHEMA_INVALID")
        if data.get("kind") != kind:
            raise SystemExit(f"{kind}_EVIDENCE_KIND_MISMATCH")
        if data.get("pass") is not True:
            raise SystemExit(f"{kind}_EVIDENCE_NOT_PASS")
        if data.get("manifest_sha256") != manifest_sha:
            raise SystemExit(f"{kind}_MANIFEST_SHA_MISMATCH")
        if data.get("source_commit") != source_commit:
            raise SystemExit(f"{kind}_SOURCE_COMMIT_MISMATCH")
        revision = data.get("tested_revision")
        if not isinstance(revision,str) or not SHA40.match(revision):
            raise SystemExit(f"{kind}_TESTED_REVISION_INVALID")
        if data.get("worktree_dirty") is not False:
            raise SystemExit(f"{kind}_WORKTREE_NOT_CLEAN")
        if tested_revision is None:
            tested_revision = revision
        elif revision != tested_revision:
            raise SystemExit(f"{kind}_TESTED_REVISION_MISMATCH")
        got = set(data.get("coverage") or [])
        missing = sorted(expected_coverage(manifest, kind) - got)
        if missing:
            raise SystemExit(f"{kind}_COVERAGE_MISSING:" + ",".join(missing))
        evidence_rows.append({
            "kind": kind,
            "path": str(path),
            "sha256": sha256(path),
            "coverage_count": len(got),
        })

    body = {
        "schema": "TAKY_DESIGN_TO_UI_RECEIPT_V1",
        "project": manifest["project"],
        "source_commit": source_commit,
        "tested_revision": tested_revision,
        "manifest_sha256": manifest_sha,
        "contract_validation_sha256": sha256(args.contract_validation),
        "evidence": evidence_rows,
        "pass": True,
    }
    out = {**body, "receipt_sha256": canonical_hash(body)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
