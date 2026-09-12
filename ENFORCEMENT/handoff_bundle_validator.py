#!/usr/bin/env python3
"""Validate self-contained TAKY handoff bundle closure.

Expected bundle root:
  MANIFEST.json
  HANDOFF.md (or manifest-declared handoff file)
  artifacts referenced by manifest

This validator proves offline bundle closure for the declared scope only.
It does not prove live external state freshness.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

AUTHORITY = {"CURRENT","CONFIRMED","HISTORICAL","SUPERSEDED","CONFLICT","PROCESS","HOLD","UNVERIFIED"}
FRESHNESS = {"SNAPSHOT_VERIFIED","LIVE_HEAD_VERIFIED","LIVE_HEAD_UNVERIFIED"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("bundle", type=Path)
    a = p.parse_args()
    root = a.bundle.resolve()
    manifest_path = root / "MANIFEST.json"
    errors = []
    if not manifest_path.is_file():
        print(json.dumps({"pass":False,"errors":["MANIFEST.json missing"]}, indent=2))
        return 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = data.get("artifacts", [])
    by_id = {}
    required_owners = set()
    for item in artifacts:
        aid = item.get("artifact_id")
        rel = item.get("bundle_path")
        if not aid or not rel:
            errors.append(f"artifact missing artifact_id/bundle_path: {item}")
            continue
        if aid in by_id:
            errors.append(f"duplicate artifact_id: {aid}")
        by_id[aid] = item
        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"artifact path escapes bundle: {aid}")
            continue
        if not path.is_file():
            errors.append(f"artifact missing: {aid} -> {rel}")
            continue
        expected = str(item.get("sha256", "")).lower()
        if not expected:
            errors.append(f"sha256 missing: {aid}")
        elif sha256(path) != expected:
            errors.append(f"sha256 mismatch: {aid}")
        if item.get("authority_class") not in AUTHORITY:
            errors.append(f"invalid authority_class: {aid}")
        if item.get("freshness") not in FRESHNESS:
            errors.append(f"invalid freshness: {aid}")
        if item.get("required_for_resume"):
            owner = item.get("owner")
            if not owner:
                errors.append(f"required artifact missing owner: {aid}")
            else:
                required_owners.add(str(owner))

    for aid in data.get("pointer_artifact_ids", []):
        if aid not in by_id:
            errors.append(f"unresolved pointer artifact_id: {aid}")

    maximum = str(data.get("claimed_scope", "")).lower() in {"maximum","full","all","최대","전체"}
    recipient_repo_access = bool(data.get("recipient_repo_access"))
    if maximum and not recipient_repo_access:
        missing = [x.get("artifact_id") for x in artifacts if x.get("required_for_resume") and not (root / x.get("bundle_path", "")).is_file()]
        if missing:
            errors.append(f"maximum/full bundle not self-contained; missing required artifacts: {missing}")

    sim = data.get("resume_simulation", {})
    if not sim.get("passed"):
        errors.append("resume_simulation not passed")
    assertions = sim.get("assertions", [])
    passed_owners = {str(x.get("owner")) for x in assertions if x.get("pass") and x.get("owner")}
    uncovered = sorted(required_owners - passed_owners)
    if uncovered:
        errors.append(f"resume simulation does not cover required owners: {uncovered}")

    boundary = data.get("coverage_boundary")
    if not isinstance(boundary, dict) or not boundary.get("proves") or not boundary.get("does_not_prove"):
        errors.append("coverage_boundary.proves/does_not_prove required")

    out = {
        "bundle": str(root),
        "artifact_count": len(artifacts),
        "required_owner_count": len(required_owners),
        "errors": errors,
        "pass": not errors,
        "claim_boundary": "OFFLINE_RECONSTRUCTION_PASS != LIVE_STATE_CURRENT"
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
