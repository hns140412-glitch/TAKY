#!/usr/bin/env python3
"""TAKY execution state engine.

Owns task lifecycle transitions and rework routing for controlled repository runs.
It is intentionally small and deterministic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_TRANSITIONS = {
    "READY": {"ASSIGNED_TO_CODEX"},
    "ASSIGNED_TO_CODEX": {"IN_PROGRESS"},
    "IN_PROGRESS": {"CODEX_DONE"},
    "CODEX_DONE": {"TAKY_REVIEW"},
    "TAKY_REVIEW": {"REWORK", "HUMAN_APPROVAL"},
    "REWORK": {"ASSIGNED_TO_CODEX", "IN_PROGRESS"},
    "HUMAN_APPROVAL": {"MERGED"},
    "MERGED": {"DEPLOYED"},
    "DEPLOYED": set(),
}

def transition(record: dict) -> dict:
    current = str(record.get("current_state", "")).strip().upper()
    requested = str(record.get("requested_state", "")).strip().upper()
    if not current or not requested:
        return {"pass": False, "detected": ["STATE_TRANSITION_INCOMPLETE"]}

    if requested not in ALLOWED_TRANSITIONS.get(current, set()):
        return {
            "pass": False,
            "detected": [f"FORBIDDEN_STATE_TRANSITION:{current}->{requested}"],
            "current_state": current,
        }

    if requested == "REWORK":
        defects = record.get("defects")
        if not isinstance(defects, list) or not defects:
            return {
                "pass": False,
                "detected": ["REWORK_WITHOUT_DEFECT_EVIDENCE"],
                "current_state": current,
            }

    if requested == "MERGED" and record.get("merge_approval_required", True):
        if not record.get("human_approval_evidence"):
            return {
                "pass": False,
                "detected": ["HUMAN_APPROVAL_MISSING:merge"],
                "current_state": current,
            }

    if requested == "DEPLOYED" and record.get("production_approval_required", True):
        if not record.get("human_approval_evidence"):
            return {
                "pass": False,
                "detected": ["HUMAN_APPROVAL_MISSING:production_deploy"],
                "current_state": current,
            }

    return {
        "pass": True,
        "detected": [],
        "previous_state": current,
        "current_state": requested,
        "rework": {
            "required": requested == "REWORK",
            "defects": record.get("defects", []) if requested == "REWORK" else [],
            "acceptance_delta": record.get("acceptance_delta", []) if requested == "REWORK" else [],
        },
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    args = ap.parse_args()
    data = json.loads(args.record.read_text(encoding="utf-8"))
    result = transition(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
