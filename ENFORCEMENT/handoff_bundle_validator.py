#!/usr/bin/env python3
"""Validate self-contained TAKY handoff bundle closure and evidence-bound resume.

Expected bundle root:
  MANIFEST.json
  HANDOFF.md (or manifest-declared handoff file)
  artifacts referenced by manifest
  machine-verifiable resume evidence artifact

A naked `resume_simulation.passed=true` is not accepted as proof.
This validator proves offline bundle closure and evidence binding for the declared scope only.
It does not prove hosted ChatGPT automatically read the state file or live external freshness.
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


def load_json(path: Path, errors: list[str], label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{label} invalid json: {exc}")
        return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("bundle", type=Path)
    a = p.parse_args()
    root = a.bundle.resolve()
    manifest_path = root / "MANIFEST.json"
    errors: list[str] = []

    if not manifest_path.is_file():
        print(json.dumps({"pass": False, "errors": ["MANIFEST.json missing"]}, indent=2))
        return 1

    data = load_json(manifest_path, errors, "MANIFEST.json")
    if data is None:
        print(json.dumps({"pass": False, "errors": errors}, indent=2))
        return 1

    artifacts = data.get("artifacts", [])
    if not isinstance(artifacts, list):
        errors.append("artifacts must be a list")
        artifacts = []

    by_id = {}
    artifact_paths = {}
    required_owners = set()

    for item in artifacts:
        if not isinstance(item, dict):
            errors.append(f"artifact not object: {item}")
            continue
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
        artifact_paths[aid] = path

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

    maximum = str(data.get("claimed_scope", "")).lower() in {"maximum", "full", "all", "최대", "전체"}
    recipient_repo_access = bool(data.get("recipient_repo_access"))
    if maximum and not recipient_repo_access:
        missing = [
            x.get("artifact_id") for x in artifacts
            if isinstance(x, dict)
            and x.get("required_for_resume")
            and not (root / x.get("bundle_path", "")).is_file()
        ]
        if missing:
            errors.append(f"maximum/full bundle not self-contained; missing required artifacts: {missing}")

    # Evidence-bound resume simulation. A boolean in MANIFEST is not proof.
    sim = data.get("resume_simulation", {})
    if not isinstance(sim, dict):
        errors.append("resume_simulation must be object")
        sim = {}

    if "passed" in sim and not sim.get("evidence_artifact_id"):
        errors.append("self-reported resume_simulation.passed is not accepted without evidence artifact")

    state_aid = str(sim.get("state_artifact_id", "")).strip()
    evidence_aid = str(sim.get("evidence_artifact_id", "")).strip()
    if not state_aid:
        errors.append("resume_simulation.state_artifact_id required")
    if not evidence_aid:
        errors.append("resume_simulation.evidence_artifact_id required")

    state_item = by_id.get(state_aid)
    evidence_item = by_id.get(evidence_aid)
    if state_aid and not state_item:
        errors.append(f"resume state artifact unresolved: {state_aid}")
    if evidence_aid and not evidence_item:
        errors.append(f"resume evidence artifact unresolved: {evidence_aid}")

    passed_owners = set()
    if state_item and evidence_item:
        state_path = artifact_paths.get(state_aid)
        evidence_path = artifact_paths.get(evidence_aid)
        if not state_path or not state_path.is_file():
            errors.append(f"resume state artifact missing: {state_aid}")
        if not evidence_path or not evidence_path.is_file():
            errors.append(f"resume evidence artifact missing: {evidence_aid}")
        else:
            evidence = load_json(evidence_path, errors, "resume evidence")
            if isinstance(evidence, dict):
                if evidence.get("evidence_type") != "TAKY_RESUME_EXECUTION_EVIDENCE":
                    errors.append("resume evidence_type invalid")
                if not str(evidence.get("session_id", "")).strip():
                    errors.append("resume evidence session_id missing")
                if evidence.get("state_read_verified") is not True:
                    errors.append("resume evidence does not prove state_read_verified")
                if str(evidence.get("state_artifact_id", "")) != state_aid:
                    errors.append("resume evidence state_artifact_id mismatch")

                actual_state_sha = sha256(state_path) if state_path and state_path.is_file() else ""
                manifest_state_sha = str(state_item.get("sha256", "")).lower()
                evidence_state_sha = str(evidence.get("state_sha256", "")).lower()
                if not actual_state_sha or evidence_state_sha != actual_state_sha:
                    errors.append("resume evidence state_sha256 does not match actual state artifact")
                if evidence_state_sha != manifest_state_sha:
                    errors.append("resume evidence state_sha256 does not match manifest state sha256")

                assertions = evidence.get("required_owner_assertions", [])
                if not isinstance(assertions, list):
                    errors.append("resume evidence required_owner_assertions must be list")
                    assertions = []
                passed_owners = {
                    str(x.get("owner")) for x in assertions
                    if isinstance(x, dict) and x.get("pass") is True and x.get("owner")
                }
                if not str(evidence.get("claim_boundary", "")).strip():
                    errors.append("resume evidence claim_boundary missing")

    uncovered = sorted(required_owners - passed_owners)
    if uncovered:
        errors.append(f"resume evidence does not cover required owners: {uncovered}")

    boundary = data.get("coverage_boundary")
    if not isinstance(boundary, dict) or not boundary.get("proves") or not boundary.get("does_not_prove"):
        errors.append("coverage_boundary.proves/does_not_prove required")

    out = {
        "bundle": str(root),
        "artifact_count": len(artifacts),
        "required_owner_count": len(required_owners),
        "resume_state_artifact_id": state_aid or None,
        "resume_evidence_artifact_id": evidence_aid or None,
        "errors": errors,
        "pass": not errors,
        "claim_boundary": "EVIDENCE_BOUND_OFFLINE_RESUME_PASS != HOSTED_SESSION_AUTO_READ != LIVE_STATE_CURRENT"
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
