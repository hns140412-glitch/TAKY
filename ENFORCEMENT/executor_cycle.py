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

def guide_rework(defects: list[dict], task: dict) -> dict:
    """Route observed gaps toward the owner's outcome; never treat a route miss as goal failure.

    Guidance contains no shell command, external invocation or approval bypass.
    The executor must observe changed evidence before another verification attempt.
    """
    codes = [str(d.get("code") or "") for d in defects if isinstance(d, dict)]
    guide = []
    risk_boundary = False
    if any(code.startswith("RESULT_PREVIEW") or code.startswith("MOBILE_RUNTIME") for code in codes):
        guide.append({
            "route": "LOCAL_RESULT_INSPECTION",
            "action": "Reuse the existing browser/runtime witness where valid; if stale or absent, run the existing local UI smoke/e2e on the actual edited artifact, bind result revision + evidence hashes, then recheck.",
            "alternative": "When live browser access is unavailable, continue feasible implementation/static checks and leave only runtime parity UNVERIFIED; do not invent a screenshot or call the entire goal impossible.",
        })
    if any(code in {"DIFF_SCOPE_VIOLATION", "RESULT_PREVIEW_OUTSIDE_CHANGE_SCOPE", "SCOPE_DEVIATION_REQUIRES_REVIEW"} for code in codes):
        risk_boundary = True
        guide.append({
            "route": "PRESERVE_AND_RECONCILE_SCOPE",
            "action": "Keep existing worktree unchanged, compare required user outcome with permitted change scope and seek a compliant local implementation route.",
            "alternative": "Only if a broader scope is essential, request narrowly scoped human approval; do not silently edit protected files.",
        })
    if any(code.startswith("ACCEPTANCE_") or code.startswith("VALIDATION_") for code in codes):
        guide.append({
            "route": "TARGETED_BEHAVIORAL_CORRECTION",
            "action": "Identify the unmet acceptance behavior, improve the relevant implementation and produce real build/test output; avoid rerunning unchanged checks.",
            "alternative": "Use a materially different local diagnostic or narrower reproduction when the previous validation environment is unavailable.",
        })
    if any(code.startswith("GONGBANG") or code == "BLOCKING_UNRESOLVED_RISK" for code in codes):
        guide.append({
            "route": "RECOVER_INDEPENDENT_EVIDENCE",
            "action": "Gather the missing independent source/revision evidence through existing authorized paths; separate real risk from missing proof.",
            "alternative": "Continue unaffected work and isolate unresolved evidence as OPEN until supported; do not self-certify approval.",
        })
    if not guide:
        guide.append({
            "route": "TARGETED_ROOT_CAUSE_REPAIR",
            "action": "Inspect the reported defect codes and the last valid checkpoint, correct the smallest material cause, then compare the actual result to the original user outcome.",
            "alternative": "Try a distinct authorized route before declaring the desired outcome impossible.",
        })
    return {
        "guiding_rule": "TKY-GUIDING-001",
        "goal_state": "NOT_VERIFIED_YET",
        "current_route_state": "REWORK_REQUIRED",
        "stop_entire_task": False,
        "approval_boundary": risk_boundary,
        "same_condition_blind_retry": False,
        "next_owner": "ASSIGNED_EXECUTOR",
        "routes": guide,
        "verify_then_continue": True,
        "requires_actual_change_before_retry": True,
        "cost_and_protected_state": "Preserve current scope and worktree; no paid API/push/merge/deploy without prior user approval.",
    }


def run(envelope: dict, executor_result: dict, root: Path | None = None) -> dict:
    ingested = ingest(envelope, executor_result)
    if not ingested["pass"]:
        return {
            "pass": False,
            "stage": "INGEST",
            "detected": ingested["detected"],
            "review": None,
            "transition": None,
            "recovery_plan": {
                "guiding_rule": "TKY-GUIDING-001",
                "current_route_state": "INTEGRITY_RECONCILIATION_REQUIRED",
                "stop_entire_task": False,
                "action": "Recover the last authorized dispatch envelope and matching executor result; verify task/provider/contract hash before replay.",
                "alternative": "Resume authorized unaffected local work while the mismatched return remains untrusted.",
                "same_condition_blind_retry": False,
            },
        }

    task = ingested["task_contract"]
    report = ingested["completion_report"]
    # The trusted caller supplies the target repository root. Never take an
    # arbitrary evidence root from the executor's returned JSON.
    reviewed = review(task, report, root)
    # Missing trusted independent evidence is a recoverable HOLD, not a request
    # for the code author to rework already-valid implementation.  Keep the
    # lifecycle in TAKY_REVIEW; do not invent a state-machine transition.
    if reviewed.get("review_decision") == "HOLD":
        return {
            "pass": False,
            "stage": "REVIEW_HOLD",
            "detected": reviewed.get("defects", []) + reviewed.get("holds", []),
            "review": reviewed,
            "transition": None,
            "next_action": "RECOVER_INDEPENDENT_EVIDENCE",
            "external_executor_invocation_verified": False,
            "recovery_plan": {
                "required": True,
                "current_route_state": "INDEPENDENT_REVIEW_EVIDENCE_PENDING",
                "next_owner": "ORCHESTRATOR",
                "stop_entire_task": False,
                "same_condition_blind_retry": False,
                "action": "Obtain genuine reviewer-origin and source-bound evidence via authorized independent read-only investigation; continue unaffected implementation without claiming approval.",
                "approval_boundary": True,
            },
        }

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
        "recovery_plan": (
            guide_rework(reviewed.get("defects") or [], task)
            if reviewed.get("review_decision") == "REWORK"
            else {"required": False, "guiding_rule": "TKY-GUIDING-001", "next": "CONTINUE_TOWARD_USER_OUTCOME"}
        ),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelope", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = ap.parse_args()

    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    out = run(envelope, result, args.root)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # REWORK is controlled but not successful: shell automation must not
    # mistake rejected evidence for completed work.
    return 0 if out.get("pass") is True else 1

if __name__ == "__main__":
    raise SystemExit(main())
