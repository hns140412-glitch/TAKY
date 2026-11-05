#!/usr/bin/env python3
"""TAKY-001 local read-only work slice (PR event watch source/receipt/review readback).

Fail-closed verifier that the canonical TAKY-001 row, its pinned sources, the
implementation receipt and the signed Codex review are mutually consistent.
It reads exact absolute official paths only (no glob/guess), calls no model,
shell, browser or GitHub CLI, never invents a PR binding, and never writes.

Status vocabulary: PASS (check holds) / HOLD (cannot be trusted or bound) /
FAIL (recorded value contradicts the live file). A PASS here proves only a
local readback; it is not a semantic review and not portfolio DONE.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from TAKY_ORCHESTRATION_RECONCILE import DEFAULT_BOARD

WORK_ID = "TAKY-001"
PROJECT = "TAKY"
TAKY_ROOT = Path(r"D:\Git PWA\TAKY")
SOURCE_PATHS = (
    r"D:\Git PWA\TAKY\TOOLS\TAKY_PR_EVENT_WATCH.py",
    r"D:\Git PWA\TAKY\TOOLS\TAKY_PR_EVENT_WATCH_TEST.py",
)
RECEIPT_PATH = (r"D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\80_EVIDENCE"
                r"\TAKY-001_PRWATCH_IMPLEMENTATION_RECEIPT_20261027.json")
REVIEW_PATH = (r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY"
               r"\TAKY_ROUTED_746ec2da2a0a4651bea832e681d7b9d6.json")
ACTIVE_STATUSES = ("NOT_STARTED", "DISCOVERY", "EVALUATION", "READY", "IMPLEMENTING")
REVIEW_STATE = "COMPLETE_UNVERIFIED"
REVIEW_QA_STATE = "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
MAX_BYTES = 8 * 1024 * 1024


class Hold(Exception):
    def __init__(self, reason: str, status: str = "HOLD", detail: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.status = status
        self.detail = detail


def _norm(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Hold("PATH_INVALID")
    p = value if os.path.isabs(value) else str(TAKY_ROOT / value)
    return os.path.normcase(os.path.normpath(p))


def _safe_file(path: str) -> Path:
    if not isinstance(path, str) or not os.path.isabs(path):
        raise Hold("PATH_NOT_ABSOLUTE")
    p = Path(os.path.normpath(path))
    # Final component and every ancestor must be a plain directory entry.
    for node in (p, *p.parents):
        if node.is_symlink() or getattr(node, "is_junction", lambda: False)():
            raise Hold("PATH_REPARSE")
    try:
        resolved = p.resolve(strict=True)
        # Any redirection inside the tree changes the post-anchor components; the drive
        # anchor itself may legitimately differ (mapped/virtual drives such as F:).
        if ([x.casefold() for x in resolved.parts[1:]]
                != [x.casefold() for x in p.parts[1:]]):
            raise Hold("PATH_REDIRECTED_UNTRUSTED")
        if not resolved.is_file() or not 0 < resolved.stat().st_size <= MAX_BYTES:
            raise Hold("FILE_UNREADABLE_OR_OVERSIZE")
    except OSError:
        raise Hold("FILE_MISSING")
    return resolved


def _sha(path: str) -> str:
    return hashlib.sha256(_safe_file(path).read_bytes()).hexdigest()


def _no_dup_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Hold("JSON_DUPLICATE_KEY")
        out[key] = value
    return out


def _load(path) -> object:
    try:
        return json.loads(_safe_file(str(path)).read_text(encoding="utf-8"),
                          object_pairs_hook=_no_dup_pairs)
    except (OSError, UnicodeError, ValueError):
        raise Hold("JSON_UNREADABLE")


def _row(board) -> dict:
    rows = board.get("tasks") if isinstance(board, dict) else None
    if not isinstance(rows, list):
        raise Hold("BOARD_UNTRUSTED")
    match = [r for r in rows if isinstance(r, dict) and r.get("id") == WORK_ID]
    if len(match) != 1:
        raise Hold("WORK_ID_NOT_UNIQUE_IN_REGISTER")
    row = match[0]
    intake = row.get("intake")
    if not isinstance(intake, dict) or intake.get("project") != PROJECT:
        raise Hold("PROJECT_MISMATCH")
    if row.get("status") not in ACTIVE_STATUSES:
        raise Hold("WORK_NOT_ACTIVE")
    if row.get("approval_required") is not False:
        raise Hold("APPROVAL_REQUIRED_OR_UNKNOWN")
    if row.get("dependencies") != []:
        raise Hold("DEPENDENCIES_NOT_EMPTY")
    return row


def _pins(row: dict, sources) -> dict:
    pins = row.get("planned_source_bindings")
    if not isinstance(pins, list) or len(pins) != len(sources):
        raise Hold("PLANNED_SOURCE_BINDINGS_INVALID")
    seen = {}
    for pin in pins:
        if not isinstance(pin, dict) or set(pin) != {"path", "sha256"}:
            raise Hold("PLANNED_SOURCE_BINDING_KEYS")
        if not isinstance(pin["sha256"], str) or not HEX64_RE.match(pin["sha256"]):
            raise Hold("PLANNED_SOURCE_PIN_SHA_INVALID")
        key = _norm(pin["path"])
        if key in seen:
            raise Hold("PLANNED_SOURCE_BINDING_DUPLICATE")
        seen[key] = pin["sha256"]
    expected = {_norm(s) for s in sources}
    if set(seen) != expected:
        raise Hold("PLANNED_SOURCE_BINDING_PATHS_UNEXPECTED")
    for s in sources:
        if seen[_norm(s)] != _sha(s):
            raise Hold("PLANNED_SOURCE_PIN_SHA_MISMATCH", "FAIL")
    return seen


def _receipt(receipt_path: str, sources) -> None:
    rec = _load(receipt_path)
    if not isinstance(rec, dict) or rec.get("work_id") != WORK_ID:
        raise Hold("RECEIPT_WORK_ID_MISMATCH")
    scope = rec.get("current_verified_scope")
    mapping = scope.get("source_sha256") if isinstance(scope, dict) else None
    if not isinstance(mapping, dict):
        raise Hold("RECEIPT_SOURCE_MAPPING_MISSING")
    normed = {}
    for key, value in mapping.items():
        try:
            nkey = _norm(key)
        except Hold:
            raise Hold("RECEIPT_SOURCE_KEY_INVALID")
        if nkey in normed:
            raise Hold("RECEIPT_SOURCE_KEY_DUPLICATE")
        normed[nkey] = value
    for s in sources:
        value = normed.get(_norm(s))
        if not isinstance(value, str) or not HEX64_RE.match(value):
            raise Hold("RECEIPT_SOURCE_SHA_ABSENT")
        if value != _sha(s):
            raise Hold("RECEIPT_SOURCE_SHA_MISMATCH", "FAIL")


def _review(review_path: str, receipt_path: str, sources) -> None:
    """The historical Codex review pinned *source versions*, not a later receipt.

    An old limited review never independently certifies today's corrected files.
    """
    rev = _load(review_path)
    if not isinstance(rev, dict):
        raise Hold("REVIEW_SHAPE_INVALID")
    if rev.get("state") != REVIEW_STATE:
        raise Hold("REVIEW_STATE_NOT_RECORDED_STATE")
    if rev.get("content_quality_verified") is not False:
        raise Hold("REVIEW_QUALITY_FLAG_UNEXPECTED")
    if rev.get("content_qa_state") != REVIEW_QA_STATE:
        raise Hold("REVIEW_QA_STATE_UNEXPECTED")
    binding = rev.get("review_source_binding")
    manifest = binding.get("source_manifest") if isinstance(binding, dict) else None
    if not isinstance(manifest, list):
        raise Hold("REVIEW_SOURCE_MANIFEST_MISSING")
    receipt = _load(receipt_path)
    scope = receipt.get("current_verified_scope") if isinstance(receipt, dict) else None
    historical = scope.get("original_review_source_sha256") if isinstance(scope, dict) else None
    if not isinstance(historical, dict):
        raise Hold("HISTORICAL_REVIEW_SOURCE_PINS_MISSING")
    original = {}
    for path, digest in historical.items():
        if not isinstance(digest, str) or not HEX64_RE.fullmatch(digest):
            raise Hold("HISTORICAL_REVIEW_SOURCE_PIN_INVALID")
        key = _norm(path)
        if key in original:
            raise Hold("HISTORICAL_REVIEW_SOURCE_DUPLICATE")
        original[key] = digest
    expected = {_norm(s) for s in sources}
    if set(original) != expected or len(manifest) != len(expected):
        raise Hold("REVIEW_SOURCE_SET_MISMATCH")
    seen = {}
    for item in manifest:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise Hold("REVIEW_SOURCE_MANIFEST_INVALID")
        digest = item.get("sha256")
        if not isinstance(digest, str) or not HEX64_RE.fullmatch(digest):
            raise Hold("REVIEW_SOURCE_SHA_INVALID")
        key = _norm(item["path"])
        if key in seen:
            raise Hold("REVIEW_SOURCE_DUPLICATE")
        seen[key] = digest
    if set(seen) != expected:
        raise Hold("REVIEW_SOURCE_SET_MISMATCH")
    if seen != original:
        raise Hold("HISTORICAL_REVIEW_SOURCE_SHA_MISMATCH", "FAIL")
    # Self-consistent manifest is reference only: content_quality_verified is false and no
    # verified signer is checked here, so this never counts as independent/authenticated PASS.
    raise Hold("HISTORICAL_REVIEW_NOT_INDEPENDENTLY_VERIFIED", "HOLD",
               "historical manifest matches original Codex packet (reference diagnostic only); "
               "no authenticated signed PASS; semantic content NOT verified; current sources not promoted")


def _try_norm(value):
    try:
        return _norm(value)
    except Hold:
        return None


def _binding(row: dict) -> dict:
    pr = row.get("github_pr")
    if pr is None:
        raise Hold("PR_OWNER_BINDING_MISSING")
    if (not isinstance(pr, dict) or set(pr) != {"repo", "pr"}
            or not isinstance(pr["repo"], str) or not REPO_RE.match(pr["repo"])
            or type(pr["pr"]) is not int or pr["pr"] <= 0):
        raise Hold("PR_OWNER_BINDING_INVALID")
    return pr


def _run(name, fn, next_action=None) -> dict:
    try:
        detail = fn()
        return {"name": name, "status": "PASS", "detail": detail or "OK"}
    except Hold as hold:
        out = {"name": name, "status": hold.status, "reason": hold.reason}
        if hold.detail:
            out["detail"] = hold.detail
    except Exception as exc:  # unexpected shape: fail closed, never PASS
        out = {"name": name, "status": "HOLD", "reason": "UNEXPECTED_" + type(exc).__name__}
    if next_action:
        out["next_action"] = next_action
    return out


def evaluate(board_path=None, receipt_path=RECEIPT_PATH, review_path=REVIEW_PATH,
             sources=SOURCE_PATHS) -> list[dict]:
    """Read-only. Returns one check dict per gate; any non-PASS keeps the slice open."""
    holder = {}

    def row_check():
        board = _load(board_path if board_path is not None else DEFAULT_BOARD)
        holder["row"] = _row(board)
        return "unique active row, approval_required=false, no dependencies"

    checks = [_run("canonical_task_row", row_check)]
    # Fixture injection is a test seam; production uses the pinned DEFAULT_BOARD.
    checks[0]["board_source"] = ("FIXTURE_INJECTED" if board_path is not None
                                 else "CANONICAL_DEFAULT_BOARD")
    row_ok = checks[0]["status"] == "PASS"
    if row_ok:
        checks.append(_run("planned_source_pins_match_live",
                           lambda: "%d pins match live sha256" % len(_pins(holder["row"], sources))))
    else:
        checks.append({"name": "planned_source_pins_match_live", "status": "HOLD",
                       "reason": "SKIPPED_ROW_UNTRUSTED"})
    checks.append(_run("implementation_receipt_source_sha",
                       lambda: _receipt(receipt_path, sources) or "receipt source sha256 match live"))
    checks.append(_run("signed_review_status_and_receipt_sha",
                       lambda: _review(review_path, receipt_path, sources)))
    if row_ok:
        binding_hint = ("Owner must bind official github_pr {repo, pr} on the TAKY-001 register row; "
                        "no binding is inferred and no GitHub call is made here")
        checks.append(_run("github_pr_owner_binding",
                           lambda: "binding %(repo)s#%(pr)d present; PR observation NOT run here" % _binding(holder["row"]),
                           binding_hint))
    else:
        checks.append({"name": "github_pr_owner_binding", "status": "HOLD",
                       "reason": "SKIPPED_ROW_UNTRUSTED"})
    return checks


def pr_work_slice(_timeout: int = 75) -> list[dict]:
    """Worker entry matching the ALL_READONLY_WORKERS(timeout) -> list[dict] contract."""
    return evaluate()


WORKERS = {WORK_ID: pr_work_slice}
