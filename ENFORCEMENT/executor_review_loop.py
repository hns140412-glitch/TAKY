#!/usr/bin/env python3
"""Deterministic TAKY review loop for executor/Codex completion reports.

Consumes the canonical task contract plus executor evidence and decides whether the
task advances from TAKY_REVIEW to HUMAN_APPROVAL or returns to REWORK.

This is evidence-gating, not semantic proof that the implementation is correct.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
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

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMIT_RE = re.compile(r"[0-9a-fA-F]{7,40}")
REVIEWER_KINDS = {"codex", "claude"}


def _commit_exists(root: Path, ref: str) -> bool:
    """True only when ``ref`` is a hex id naming a commit object in the local repo."""
    if not COMMIT_RE.fullmatch(ref):
        return False
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", ref + "^{commit}"],
            capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _load_bound_doc(entry: object, base: Path) -> dict | None:
    """Read an evidence file named by ``entry`` only if its bytes match evidence_sha256."""
    from gongbang_scope_gate_candidate import _read_best_effort, _read_fd_relative, _safe_open_supported
    if not isinstance(entry, dict):
        return None
    ref, digest = entry.get("evidence_ref"), entry.get("evidence_sha256")
    if not isinstance(ref, str) or not isinstance(digest, str) or len(digest) != 64:
        return None
    raw = ref.strip().replace("\\", "/")
    parts = raw.split("/")
    if raw.startswith("/") or ":" in raw or any(p in ("", ".", "..") for p in parts):
        return None
    try:
        data, reason = (_read_fd_relative if _safe_open_supported() else _read_best_effort)(base, parts)
        if reason or hashlib.sha256(data).hexdigest() != digest.lower():
            return None
        doc = json.loads(data.decode("utf-8"))
    except (OSError, ValueError, RuntimeError):
        return None
    return doc if isinstance(doc, dict) else None


RECEIPT_KEY_ENV = "TAKY_REVIEW_RECEIPT_KEY"
RECEIPT_ALG = "HMAC-SHA256"
_HEX64 = re.compile(r"[0-9a-f]{64}")


def _review_record_digest(doc: dict) -> str:
    body = {k: v for k, v in doc.items() if k != "provider_receipt"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sign_review_receipt(doc: dict, issuer: str, key: bytes | str) -> dict:
    """Issuer-side helper: produce the receipt a verifier-held key vouches for.

    Only a party holding the verifier key can mint this. The executor must not hold it.
    """
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    digest = _review_record_digest(doc)
    mac = hmac.new(key_bytes, f"{issuer}\n{digest}".encode("utf-8"), hashlib.sha256).hexdigest()
    return {"alg": RECEIPT_ALG, "issuer": issuer, "review_record_sha256": digest, "signature": mac}


def verify_review_receipt(doc: dict, task_id: object, revision: str, executor_id: str,
                          key: bytes | str | None) -> list[str]:
    """Return reasons the reviewer identity is NOT authenticated ([] = receipt verified).

    A reviewer_id/session/source hash written into the review record is only a claim. It is
    authenticated only by a receipt whose MAC, over the whole record, was made with a key the
    executor does not hold. Pure function: no git or fd-relative open needed to exercise it.
    """
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    if not key_bytes or len(key_bytes) < 16:
        return ["NO_VERIFIER_KEY_CONFIGURED"]
    receipt = doc.get("provider_receipt")
    if not isinstance(receipt, dict):
        return ["PROVIDER_RECEIPT_MISSING_SELF_ATTESTED_ONLY"]
    reasons = []
    issuer = receipt.get("issuer")
    if receipt.get("alg") != RECEIPT_ALG or not isinstance(issuer, str) or not issuer.strip():
        return ["PROVIDER_RECEIPT_MALFORMED"]
    digest = _review_record_digest(doc)
    mac = hmac.new(key_bytes, f"{issuer}\n{digest}".encode("utf-8"), hashlib.sha256).hexdigest()
    signature = receipt.get("signature")
    if (receipt.get("review_record_sha256") != digest or not isinstance(signature, str)
            or not hmac.compare_digest(signature, mac)):
        return ["PROVIDER_RECEIPT_SIGNATURE_INVALID"]
    if issuer.strip().casefold() == executor_id.casefold() or \
            str(doc.get("reviewer_id") or "").strip().casefold() == issuer.strip().casefold():
        reasons.append("RECEIPT_ISSUER_NOT_INDEPENDENT")
    if doc.get("task_id") != task_id:
        reasons.append("RECEIPT_TASK_MISMATCH")
    if not revision or doc.get("revision") != revision:
        reasons.append("RECEIPT_REVISION_MISMATCH")
    source = doc.get("source_sha256")
    if not isinstance(source, str) or not _HEX64.fullmatch(source):
        reasons.append("RECEIPT_SOURCE_HASH_MISSING")
    return reasons


def _material_review_defects(task: dict, report: dict, root: Path, defects: list,
                             holds: list | None = None, receipt_key: bytes | str | None = None) -> None:
    """Extra fail-closed checks for material tasks so review cannot be a rubber stamp.

    These prove the review record is hash-bound, names a reviewer different from the executor,
    and declares a match against the user's original intent. Reviewer identity is only claimed
    by the record; it is authenticated solely by a verifier-keyed provider receipt. Without one
    the review is a HOLD (recorded in ``holds``), never a verified independent PASS. They do not
    prove the intent verdict is semantically right.
    """
    from gongbang_scope_gate_candidate import _verify_ref
    task_id = task.get("task_id")
    commit = str(report.get("commit_ref") or "").strip()

    try:
        base = Path(root).resolve()
    except (OSError, ValueError, RuntimeError, TypeError):
        base = None

    # A commit that does not exist locally cannot be the reviewed revision.
    if commit and (base is None or not _commit_exists(base, commit)):
        defects.append({"code": "COMMIT_REF_NOT_FOUND", "commit_ref": commit})

    # PASS must be backed by a hash-bound evidence file, not a self-reported string.
    claims = [("acceptance", c, i) for c, i in _index_acceptance(report).items()
              if str(i.get("status", "")).upper() == "PASS"]
    claims += [("validation", g, i) for g, i in (report.get("validation_results") or {}).items()
               if isinstance(i, dict) and str(i.get("status", "")).upper() == "PASS"] \
        if isinstance(report.get("validation_results"), dict) else []
    for kind, name, item in claims:
        reason = ("ROOT_UNREADABLE" if base is None
                  else _verify_ref(item, base, task_id, commit))
        if reason == "RACE_SAFETY_UNVERIFIED" and holds is not None:
            holds.append({"code": "PASS_CLAIM_PLATFORM_HOLD", "kind": kind, "name": name, "reason": reason})
        elif reason:
            defects.append({"code": "PASS_CLAIM_UNVERIFIED", "kind": kind, "name": name, "reason": reason})

    # The user's own words are the intent source; assistant-authored scope is not accepted.
    intent = task.get("original_user_intent")
    intent_text = intent.get("text") if isinstance(intent, dict) else intent
    if (not isinstance(intent_text, str) or not intent_text.strip()
            or (isinstance(intent, dict) and intent.get("source") != "user")):
        defects.append({"code": "ORIGINAL_USER_INTENT_MISSING"})
        intent_text = None

    gb = report.get("gongbang_evidence")
    doc = _load_bound_doc(gb.get("independent_review") if isinstance(gb, dict) else None,
                          base) if base else None
    if doc is None:
        defects.append({"code": "INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED", "reason": "REVIEW_RECORD_UNREADABLE"})
        return
    problems = []
    reviewer = str(doc.get("reviewer_id") or "").strip()
    executor = str(report.get("executor_id") or "").strip()
    if str(doc.get("reviewer_kind") or "").lower() not in REVIEWER_KINDS:
        problems.append("REVIEWER_KIND_UNKNOWN")
    if not reviewer or not str(doc.get("reviewer_session_id") or "").strip():
        problems.append("REVIEWER_IDENTITY_MISSING")
    if not executor:
        problems.append("EXECUTOR_ID_MISSING")
    elif reviewer.casefold() == executor.casefold():
        problems.append("REVIEWER_IS_EXECUTOR")
    if doc.get("review_scope") != "ORIGINAL_SOURCE":
        problems.append("REVIEW_SCOPE_NOT_ORIGINAL_SOURCE")
    if doc.get("verdict") != "PASS":
        problems.append("REVIEW_VERDICT_NOT_PASS")
    if problems:
        defects.append({"code": "INDEPENDENT_REVIEW_PROVENANCE_UNVERIFIED", "reason": problems})
    elif holds is not None:
        unauthenticated = verify_review_receipt(doc, task_id, commit, executor, receipt_key)
        if unauthenticated:
            holds.append({"code": "REVIEWER_IDENTITY_UNAUTHENTICATED", "reason": unauthenticated,
                          "claimed_reviewer_id": reviewer, "verified": False})
    if intent_text is not None and (
            doc.get("intent_sha256") != hashlib.sha256(intent_text.encode("utf-8")).hexdigest()
            or doc.get("intent_verdict") != "MATCH"):
        defects.append({"code": "ORIGINAL_INTENT_NOT_COMPARED"})

def review(task: dict, report: dict, root: Path | None = None,
           receipt_key: bytes | str | None = None) -> dict:
    defects: list[dict] = []
    holds: list[dict] = []
    evidence: list[dict] = []
    if receipt_key is None:
        receipt_key = os.environ.get(RECEIPT_KEY_ENV)

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

    # Material TAKY tasks require the complete cross-examination contract.
    # Review evidence belongs to the executor report, not the task request.
    if task.get('material_taky_turn') is True or task.get('gongbang_required') is True:
        from gongbang_scope_gate_candidate import evaluate as evaluate_gongbang
        gongbang = evaluate_gongbang(report.get('gongbang_evidence') or {}, root or REPO_ROOT,
                                     task.get('task_id'), str(report.get('commit_ref') or '').strip())
        if gongbang['status'] != 'PASS':
            reasons = list((gongbang.get('unverified') or {}).values())
            if (not gongbang.get('missing') and not gongbang.get('preconditions') and
                    reasons and all(reason == 'RACE_SAFETY_UNVERIFIED' for reason in reasons)):
                holds.append({'code': 'GONGBANG_PLATFORM_EVIDENCE_HOLD',
                              'reason': 'RACE_SAFETY_UNVERIFIED'})
            else:
                defects.append({'code': 'GONGBANG_SCOPE_INCOMPLETE', 'missing': gongbang['missing'],
                                'unverified': gongbang.get('unverified', {}),
                                'preconditions': gongbang.get('preconditions', [])})
        else:
            # Hash/binding verified only; issuer identity is not proven by this gate.
            evidence.append({'kind': 'gongbang', 'issuer': gongbang['issuer']})
        _material_review_defects(task, report, root or REPO_ROOT, defects, holds, receipt_key)
        if not holds and not defects:
            evidence.append({'kind': 'independent_review', 'identity': 'PROVIDER_RECEIPT_VERIFIED'})

    validation = task.get("validation") or {}
    requires_preview = (
        validation.get("result_preview_required") is True
        or validation.get("mobile_runtime_required") is True
        or str(validation.get("artifact_kind") or "").lower()
        in {"ui", "pwa", "image", "asset", "document", "pdf", "presentation", "spreadsheet"}
    )
    if requires_preview:
        # Reuse existing on-disk SHA256 evidence verification. A render witness
        # does not prove visual 1:1 parity or substitute for human approval.
        from result_preview_gate import validate_preview
        preview = report.get("result_preview")
        if not isinstance(preview, dict):
            defects.append({"code": "RESULT_PREVIEW_EVIDENCE_MISSING"})
        else:
            result = validate_preview(preview, root or REPO_ROOT)
            if result.get("pass") is not True or result.get("release_eligible") is not True:
                defects.append({"code": "RESULT_PREVIEW_NOT_VERIFIED", "detected": result.get("detected", [])})
            elif (
                preview.get("task_id") != task.get("task_id")
                or preview.get("preview_required") is not True
                or preview.get("preview_receipt_hash") != result.get("preview_receipt_hash")
            ):
                defects.append({"code": "RESULT_PREVIEW_RECEIPT_BINDING_MISMATCH"})
            elif not _path_allowed(str(preview.get("result_path") or ""), allowed):
                defects.append({"code": "RESULT_PREVIEW_OUTSIDE_CHANGE_SCOPE"})
            else:
                evidence.append({
                    "kind": "revision_bound_preview",
                    "result_path": result["result_path"],
                    "result_revision_hash": result["result_revision_hash"],
                    "preview_receipt_hash": result["preview_receipt_hash"],
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
            "holds": holds,
            "independent_pass_verified": False,
        }

    if holds:
        # Identity cannot be authenticated: neither approve nor claim a verified independent PASS.
        return {
            "pass": False,
            "review_decision": "HOLD",
            "state_transition": {"current_state": "TAKY_REVIEW", "requested_state": "TAKY_REVIEW"},
            "defects": [],
            "holds": holds,
            "acceptance_delta": [],
            "evidence": evidence,
            "independent_pass_verified": False,
        }

    # Review never performs or implies a merge: approval is a separate step.
    next_state = "HUMAN_APPROVAL"
    return {
        "pass": True,
        "review_decision": next_state,
        "state_transition": {"current_state": "TAKY_REVIEW", "requested_state": next_state},
        "defects": [],
        "holds": [],
        "acceptance_delta": [],
        "evidence": evidence,
        "independent_pass_verified": any(e.get("kind") == "independent_review" for e in evidence),
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
