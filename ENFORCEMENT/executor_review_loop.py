#!/usr/bin/env python3
"""Deterministic TAKY review loop for executor/Codex completion reports.

Consumes the canonical task contract plus executor evidence and decides whether the
task advances from TAKY_REVIEW to HUMAN_APPROVAL or returns to REWORK.

This is evidence-gating, not semantic proof that the implementation is correct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from fnmatch import fnmatch
from trace_to_regression import build_case as build_regression_case
from codex_task_contract_validator import validate as validate_task_contract

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

def _rework_actions(defects: list[dict]) -> list[dict]:
    """Route confirmed defects to the right repair surface; never auto-edit a manual."""
    routes = {
        "WORK_MANUAL": "RECHECK_MANUAL_BINDING",
        "DIFF_SCOPE": "RECONCILE_TASK_SCOPE",
        "CHANGED_FILES": "RECOVER_DIFF_EVIDENCE",
        "ACCEPTANCE_NOT_PASS": "FIX_IMPLEMENTATION_AND_REGRESSION",
        "VALIDATION_NOT_PASS": "FIX_IMPLEMENTATION_AND_REGRESSION",
        "MOBILE_RUNTIME_NOT_PASS": "FIX_IMPLEMENTATION_AND_REGRESSION",
        "BLOCKING_UNRESOLVED_RISK": "RESOLVE_BLOCKING_RISK",
    }
    actions = []
    seen = set()
    for defect in defects:
        code = str(defect.get("code", ""))
        route = next((value for prefix, value in routes.items() if code.startswith(prefix)),
                     "RECOVER_VERIFIABLE_EVIDENCE")
        if route not in seen:
            actions.append({"route": route, "trigger": code,
                            "manual_auto_edit": False, "blind_retry_allowed": False})
            seen.add(route)
    return actions


def _readback_manual_artifact(target: dict) -> tuple[str, str]:
    """Read a single size-bounded, pinned intake artifact from a fixed local anchor.

    The report cannot choose a path, network URL, command, or alternate anchor.
    Returns (failure_code, observed_sha256). This checks bytes and declared
    postconditions, not independent semantic correctness of model work.
    """
    if not isinstance(target, dict) or target.get("anchor") != "SOURCE_VAULT_REVIEW_EVENTS":
        return "WORK_MANUAL_ARTIFACT_ANCHOR_FORBIDDEN", ""
    name = target.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"REV-[a-f0-9]{24}[.]json", name):
        return "WORK_MANUAL_ARTIFACT_NAME_INVALID", ""
    expected_hash = target.get("sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
        return "WORK_MANUAL_ARTIFACT_HASH_INVALID", ""
    source_vault = Path(__file__).resolve().parents[3].parent / "TAKY-SOURCE-VAULT"
    root = source_vault / "data" / "direction_intake" / "review_events"
    path = root / name
    try:
        if path.is_symlink() or path.resolve(strict=True).parent != root.resolve(strict=True):
            return "WORK_MANUAL_ARTIFACT_PATH_UNSAFE", ""
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            return "WORK_MANUAL_ARTIFACT_SIZE_OR_TYPE_INVALID", ""
        raw = path.read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != expected_hash:
            return "WORK_MANUAL_ARTIFACT_SHA256_MISMATCH", actual_hash
        doc = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(doc, dict) or doc.get("event_id", "") + ".json" != name:
            return "WORK_MANUAL_ARTIFACT_EVENT_ID_INVALID", actual_hash
        expected = target.get("expected_fields")
        if not isinstance(expected, dict) or not expected:
            return "WORK_MANUAL_ARTIFACT_FIELDS_INVALID", actual_hash
        for key, value in expected.items():
            if key not in {"schema", "event_id", "review_stage", "index_state",
                           "forming_state", "canonical_promotion", "source_type"}:
                return "WORK_MANUAL_ARTIFACT_FIELDS_INVALID", actual_hash
            if doc.get(key) != value:
                return "WORK_MANUAL_ARTIFACT_POSTCONDITION_MISMATCH", actual_hash
        return "", actual_hash
    except (OSError, ValueError, TypeError, UnicodeError):
        return "WORK_MANUAL_ARTIFACT_READBACK_FAILED", ""


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

    # The executor must explicitly state how the selected, SHA-pinned manual
    # affected the task. This is an evidence claim, NOT independent proof of use.
    manual = task.get("work_manual_binding")
    if manual is not None:
        # A transport checksum alone is not approval of a forged manual binding.
        for err in validate_task_contract(task):
            if err.startswith("WORK_MANUAL_"):
                defects.append({"code": err})
        applied = report.get("work_manual_evidence")
        if not isinstance(manual, dict):
            pass  # Already reported by the validator; never dereference it.
        elif not isinstance(applied, dict):
            defects.append({"code": "WORK_MANUAL_EVIDENCE_MISSING"})
        elif (applied.get("skill_id") != manual.get("skill_id")
              or applied.get("version_sha256") != manual.get("version_sha256")):
            defects.append({"code": "WORK_MANUAL_VERSION_MISMATCH"})
        elif not str(applied.get("execution_implication") or "").strip() or not str(
                applied.get("evidence_ref") or "").strip():
            defects.append({"code": "WORK_MANUAL_APPLICATION_EVIDENCE_MISSING"})
        else:
            target = manual.get("artifact_evidence")
            artifact_status = "EXECUTOR_REPORTED_NOT_INDEPENDENTLY_VERIFIED"
            observed_sha = None
            if target is not None:
                if not isinstance(target, dict):
                    defects.append({"code": "WORK_MANUAL_ARTIFACT_TARGET_INVALID"})
                elif applied.get("evidence_ref") != (
                    str(target.get("anchor", "")) + ":" + str(target.get("name", ""))
                ):
                    defects.append({"code": "WORK_MANUAL_ARTIFACT_REPORT_REF_MISMATCH"})
                else:
                    failure, observed_sha = _readback_manual_artifact(target)
                    if failure:
                        defects.append({"code": failure})
                    else:
                        artifact_status = "LOCAL_ARTIFACT_READBACK_VERIFIED"
            evidence.append({"kind": "work_manual", "skill_id": manual["skill_id"],
                             "version_sha256": manual["version_sha256"],
                             "status": artifact_status,
                             "observed_sha256": observed_sha,
                             "evidence_ref": applied["evidence_ref"]})

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
        candidate = None
        failure_event = report.get("confirmed_failure_event")
        if isinstance(failure_event, dict):
            candidate_result = build_regression_case(failure_event)
            if candidate_result["pass"]:
                candidate = candidate_result["regression_case"]
        return {
            "pass": False,
            "review_decision": "REWORK",
            "rework_actions": _rework_actions(defects),
            "regression_case_candidate": candidate,
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
