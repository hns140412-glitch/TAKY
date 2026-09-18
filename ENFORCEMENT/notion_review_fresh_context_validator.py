#!/usr/bin/env python3
"""Fresh-context Notion review routing regression validator.

Mechanical projection only. Semantic ownership remains:
- OS/COMMAND_INTERACTION.md (command routing)
- OS/NOTION_OPS.md (Notion review workflow)
- MASTER/ENFORCEMENT_PROTOCOL.md / ENFORCEMENT/taky_gate.py (failure gate)

This validator simulates a brand-new context with only the user's command.
It does not claim hosted ChatGPT/Work auto-invocation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from taky_gate import validate_record

LINK_ALIASES = {
    "노션검토",
    "노션 검토",
    "/노션검토",
    "/노션링크검토",
}
STRUCTURE_ALIASES = {
    "노션구조검토",
    "노션 구조검토",
    "/노션구조검토",
}

EXPECTED_LINK_WORKFLOW = "NOTION_LINK_INTELLIGENCE_REVIEW"
EXPECTED_STRUCTURE_WORKFLOW = "NOTION_STRUCTURE_REVIEW"
REQUIRED_PHASES = [
    "SOURCE_ACQUISITION",
    "SOURCE_GRAPH_CLOSURE",
    "ANALYSIS",
    "COMPARE",
    "IMPROVE",
    "REVIEW_RECORD_UPDATE",
]


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def deterministic_route(command: str) -> str:
    n = normalize(command)
    if n in LINK_ALIASES:
        return EXPECTED_LINK_WORKFLOW
    if n in STRUCTURE_ALIASES:
        return EXPECTED_STRUCTURE_WORKFLOW
    return "UNRESOLVED"


def require_doc_contract(repo_root: Path) -> List[str]:
    failures: List[str] = []
    docs = {
        "TAKY.md": [
            "/노션검토",
            "📚 나의 링크",
            "original/root source",
            "source-graph closure",
            "analysis/compare/improve",
        ],
        "OS/COMMAND_INTERACTION.md": [
            "The user SHALL NOT need to invoke TAKY separately",
            "노션검토",
            "content/link intelligence review",
            "ROOT/ORIGINAL SOURCE",
            "SOURCE GRAPH CLOSURE",
            "ANALYZE",
            "COMPARE",
            "IMPROVE",
            "/노션검토 ≠ /반영",
        ],
        "OS/NOTION_OPS.md": [
            "Phase A — Source Acquisition / Source Graph Closure",
            "Phase B — Analysis / Compare / Improve",
            "ROOT_SOURCE_STATE",
            "SOURCE_GRAPH_STATE",
            "MATERIAL_NODES_DISCOVERED",
            "MATERIAL_NODES_DISPOSITIONED",
            "SOURCE_GRAPH_EVIDENCE",
        ],
    }
    for rel, needles in docs.items():
        path = repo_root / rel
        if not path.exists():
            failures.append("MISSING_DOC:" + rel)
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                failures.append("DOC_CONTRACT_MISSING:" + rel + ":" + needle)
    return failures


def validate_fixture(payload: Dict[str, Any], repo_root: Path) -> List[str]:
    failures: List[str] = []
    command = str(payload.get("user_input", ""))
    prior = payload.get("prior_context", [])
    assistant = payload.get("assistant_result", {})

    if prior not in ([], None):
        failures.append("FRESH_CONTEXT_NOT_ZERO")

    expected_route = deterministic_route(command)
    if expected_route == "UNRESOLVED":
        failures.append("COMMAND_UNRESOLVED")

    if bool(assistant.get("requires_taky_prefix", False)):
        failures.append("TAKY_PREFIX_WRONGLY_REQUIRED")

    selected = str(assistant.get("selected_workflow", ""))
    if selected != expected_route:
        failures.append("WRONG_ROUTE:" + (selected or "EMPTY") + "!=" + expected_route)

    if expected_route == EXPECTED_LINK_WORKFLOW:
        if assistant.get("target_collection") != "📚 나의 링크":
            failures.append("WRONG_DEFAULT_COLLECTION")
        phases = assistant.get("required_phases", [])
        if phases != REQUIRED_PHASES:
            failures.append("REQUIRED_PHASES_MISMATCH")
        if bool(assistant.get("structure_audit_is_default", False)):
            failures.append("STRUCTURE_AUDIT_SUBSTITUTED")
        if bool(assistant.get("canonical_write_authorized", False)):
            failures.append("CANONICAL_WRITE_WRONGLY_AUTHORIZED")

        record = assistant.get("execution_record", {})
        if not isinstance(record, dict):
            failures.append("EXECUTION_RECORD_MISSING")
        else:
            gate_failures = validate_record(record)
            failures.extend("GATE:" + x for x in gate_failures)

    failures.extend(require_doc_contract(repo_root))
    return failures


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("fixture", type=Path)
    p.add_argument("--repo-root", type=Path, default=Path("."))
    args = p.parse_args()

    payload = json.loads(args.fixture.read_text(encoding="utf-8"))
    failures = validate_fixture(payload, args.repo_root)
    result = {
        "fixture": str(args.fixture),
        "fresh_context": True,
        "user_input": payload.get("user_input"),
        "deterministic_route": deterministic_route(str(payload.get("user_input", ""))),
        "failures": failures,
        "pass": not failures,
        "boundary": "REPOSITORY_FRESH_CONTEXT_REPLAY_ONLY; HOSTED_CHATGPT_WORK_AUTO_INVOCATION_UNVERIFIED",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
