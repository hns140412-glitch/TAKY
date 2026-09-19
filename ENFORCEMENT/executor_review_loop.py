#!/usr/bin/env python3
"""Deterministic TAKY review loop for executor/Codex completion reports.

Consumes the canonical task contract plus executor evidence and decides whether the
task advances from TAKY_REVIEW to HUMAN_APPROVAL or returns to REWORK.

This is evidence-gating, not semantic proof that the implementation is correct.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from fnmatch import fnmatch

PASS_STATES = {"PASS", "NOT_APPLICABLE"}
FAIL_STATES = {"FAIL", "UNVERIFIED", "NOT_RUN", "MISSING"}

def _index_acceptance(report: dict) -> dict[str, dict]:
    out = {}
    for item in report.get("acceptance_results", []):
        if isinstance(item, dict) and str(item.get("criterion", "")).strip():
            out[str(item["criterion"]).strip()] = item
    return out

def _path_allowed(path: str, allowed: list[str]) -> bool:
    for rule in allowed:
        rule = str(rule).strip()
        if not rule:
            continue
        if path == rule or path.startswith(rule.rstrip("/") + "/") or fnmatch(path, rule):
            return True
    return False

def review(task: dict, report: dict) -> dict:
    defects: list[dict] = []
    evidence: list[dict] = []

    if report.get("task_id") != task.get("task_id"):
        defects.append({
            "code": "TASK_ID_MISMATCH",
            "detail": f"expected {task.get('task_id')!r}, got {report.get('task_id')!r}",
        })

    changed_files = report.get("changed_files")
    allowed = (task.get("change_scope") or {}).get("allowed", [])
    if not isinstance(changed_files, list) or not changed_files:
        defects.append({"code": "CHANGED_FILES_MISSING", "detail": "executor report has no changed_files evidence"})
    else:
        outside = [p for p in changed_files if not _path_allowed(str(p), allowed)]
        if outside:
            defects.append({
                "code": "DIFF_SCOPE_VIOLATION",
                "detail": "changed files outside allowed scope",
                "files": outside,
            })

    acceptance = _index_acceptance(report)
    for criterion in task.get("acceptance_tests", []):
        item = acceptance.get(str(criterion))
        if not item:
            defects.append({
                "code": "ACCEPTANCE_EVIDENCE_MISSING",
                "criterion": criterion,
            })
            continue
        status = str(item.get("status", "")).upper()
        ev = str(item.get("evidence", "")).strip()
        if status != "PASS":
            defects.append({
                "code": "ACCEPTANCE_NOT_PASS",
                "criterion": criterion,
                "status": status or "MISSING",
            })
        elif not ev:
            defects.append({
                "code": "ACCEPTANCE_EVIDENCE_MISSING",
                "criterion": criterion,
            })
        else:
            evidence.append({"kind": "acceptance", "criterion": criterion, "evidence": ev})

    validation_results = report.get("validation_results")
    if not isinstance(validation_results, dict):
        validation_results = {}
    required = (task.get("validation") or {}).get("required", [])
    for gate in required:
        item = validation_results.get(gate)
        if not isinstance(item, dict):
            defects.append({"code": "VALIDATION_EVIDENCE_MISSING", "gate": gate})
            continue
        status = str(item.get("status", "")).upper()
        ev = str(item.get("evidence", "")).strip()
        if status not in PASS_STATES:
            defects.append({"code": "VALIDATION_NOT_PASS", "gate": gate, "status": status or "MISSING"})
        elif status == "PASS" and not ev:
            defects.append({"code": "VALIDATION_EVIDENCE_MISSING", "gate": gate})
        else:
            evidence.append({"kind": "validation", "gate": gate, "status": status, "evidence": ev})

    if (task.get("validation") or {}).get("mobile_runtime_required"):
        mobile = report.get("mobile_runtime_result")
        if not isinstance(mobile, dict):
            defects.append({"code": "MOBILE_RUNTIME_EVIDENCE_MISSING"})
        else:
            status = str(mobile.get("status", "")).upper()
            ev = str(mobile.get("evidence", "")).strip()
            if status != "PASS":
                defects.append({"code": "MOBILE_RUNTIME_NOT_PASS", "status": status or "MISSING"})
            elif not ev:
                defects.append({"code": "MOBILE_RUNTIME_EVIDENCE_MISSING"})
            else:
                evidence.append({"kind": "mobile_runtime", "evidence": ev})

    if report.get("scope_deviations"):
        defects.append({
            "code": "SCOPE_DEVIATION_REQUIRES_REVIEW",
            "detail": report.get("scope_deviations"),
        })

    if not str(report.get("commit_ref", "")).strip():
        defects.append({"code": "COMMIT_REF_MISSING"})

    unresolved = report.get("unresolved_risks", [])
    blocking_risks = []
    if isinstance(unresolved, list):
        for x in unresolved:
            if isinstance(x, dict) and str(x.get("severity", "")).upper() in {"HIGH", "BLOCKING"}:
                blocking_risks.append(x)
    if blocking_risks:
        defects.append({
            "code": "BLOCKING_UNRESOLVED_RISK",
            "risks": blocking_risks,
        })

    if defects:
        return {
            "pass": False,
            "review_decision": "REWORK",
            "state_transition": {"current_state": "TAKY_REVIEW", "requested_state": "REWORK"},
            "defects": defects,
            "acceptance_delta": [
                d.get("criterion") for d in defects if d.get("criterion")
            ],
            "evidence": evidence,
        }

    merge_required = bool((task.get("human_approval") or {}).get("merge_required", True))
    next_state = "HUMAN_APPROVAL" if merge_required else "MERGED"
    return {
        "pass": True,
        "review_decision": next_state,
        "state_transition": {"current_state": "TAKY_REVIEW", "requested_state": next_state},
        "defects": [],
        "acceptance_delta": [],
        "evidence": evidence,
        "commit_ref": report.get("commit_ref"),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    task = json.loads(args.task.read_text(encoding="utf-8"))
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = review(task, report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
