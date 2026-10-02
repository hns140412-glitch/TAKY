#!/usr/bin/env python3
"""Guard snapshot/live and repository/hosted-runtime claim boundaries."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def require(text: str, needle: str, code: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(code)

def main() -> int:
    failures: list[str] = []

    current_path = ROOT / "CURRENT" / "SYSTEM_WIDE_REVIEW.json"
    state_path = ROOT / "STATE.md"
    resolver_path = ROOT / "ENFORCEMENT" / "semantic_current_resolver.py"
    orchestrator_path = ROOT / "ENFORCEMENT" / "runtime_orchestrator.py"

    current = json.loads(current_path.read_text(encoding="utf-8"))
    state = state_path.read_text(encoding="utf-8")
    resolver = resolver_path.read_text(encoding="utf-8")
    orchestrator = orchestrator_path.read_text(encoding="utf-8")
    orchestrator_flat = " ".join(orchestrator.split())

    if current.get("role") != "SEMANTIC_RESUME_POINTER":
        failures.append("SYSTEM_CURRENT_ROLE_NOT_RESUME_POINTER")
    if current.get("authority_transfer") is not False:
        failures.append("SYSTEM_CURRENT_AUTHORITY_TRANSFER_NOT_FALSE")

    evidence_basis = str(current.get("evidence_basis", ""))
    live_compare = str(current.get("live_head_comparison", ""))
    if "dated snapshots" not in evidence_basis:
        failures.append("DATED_SNAPSHOT_BOUNDARY_MISSING")
    if "REQUERY_BEFORE_LATER_CURRENT_CLAIM" not in live_compare:
        failures.append("LIVE_REQUERY_REQUIREMENT_MISSING")

    require(
        state,
        "requery before any later live-current claim",
        "STATE_LIVE_REQUERY_BOUNDARY_MISSING",
        failures,
    )
    require(
        resolver,
        '"claim_ceiling": "AUDITED_SNAPSHOT_NOT_LIVE_OR_DEPLOYMENT_PROOF"',
        "RESOLVER_CLAIM_CEILING_MISSING",
        failures,
    )
    require(
        orchestrator_flat,
        "does not invoke hosted ChatGPT automatically",
        "HOSTED_AUTO_INVOCATION_BOUNDARY_MISSING",
        failures,
    )
    require(
        state,
        "hosted automatic state read, semantic rehydration, and trusted routing remain UNVERIFIED",
        "HOSTED_RUNTIME_UNVERIFIED_BOUNDARY_MISSING",
        failures,
    )

    result = {
        "pass": not failures,
        "snapshot_claim_ceiling": "AUDITED_SNAPSHOT_NOT_LIVE",
        "hosted_runtime_enforcement": "UNVERIFIED_NOT_INFERRED",
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
