#!/usr/bin/env python3
"""End-to-end TAKY executor return cycle for controlled runtimes.

Integrity-bind result -> TAKY evidence review -> deterministic lifecycle transition.
External executor invocation itself remains outside this module.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from executor_result_ingest import ingest
from executor_review_loop import review
from execution_state_engine import transition

def run(envelope: dict, executor_result: dict) -> dict:
    ingested = ingest(envelope, executor_result)
    if not ingested["pass"]:
        return {
            "pass": False,
            "stage": "INGEST",
            "detected": ingested["detected"],
            "review": None,
            "transition": None,
        }

    task = ingested["task_contract"]
    report = ingested["completion_report"]
    reviewed = review(task, report)

    state_record = dict(reviewed.get("state_transition") or {})
    if reviewed.get("review_decision") == "REWORK":
        state_record["defects"] = reviewed.get("defects", [])
        state_record["acceptance_delta"] = reviewed.get("acceptance_delta", [])

    # Human approval transition is review output only; merge still requires
    # separate human approval evidence in the state engine's next transition.
    transitioned = transition(state_record)

    return {
        "pass": bool(reviewed.get("pass")) and bool(transitioned.get("pass")),
        "stage": "REVIEW_COMPLETE",
        "detected": reviewed.get("defects", []),
        "review": reviewed,
        "transition": transitioned,
        "next_action": (
            "AWAIT_HUMAN_APPROVAL"
            if reviewed.get("review_decision") == "HUMAN_APPROVAL"
            else "RETURN_REWORK_TO_EXECUTOR"
        ),
        "external_executor_invocation_verified": False,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelope", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()

    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    out = run(envelope, result)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # REWORK is a valid controlled outcome even though review.pass is false.
    review_decision = ((out.get("review") or {}).get("review_decision"))
    controlled = out.get("stage") == "REVIEW_COMPLETE" and review_decision in {"HUMAN_APPROVAL", "REWORK"}
    return 0 if controlled else 1

if __name__ == "__main__":
    raise SystemExit(main())
