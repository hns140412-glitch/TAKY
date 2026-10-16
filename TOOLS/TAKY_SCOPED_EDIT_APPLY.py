#!/usr/bin/env python3
"""Transactional, hash-bound local application of a bounded model edit proposal.

No network or model calls. Plans are data, never shell commands. Existing UTF-8
files only; this helper cannot create, rename, delete, push, deploy, or run tests.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile

EXTENSIONS = {".py", ".ps1", ".js", ".ts", ".tsx", ".jsx", ".json", ".css", ".html"}
MAX_BYTES = 100_000
MAX_FILES = 2

class EditRejected(ValueError):
    pass

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def file_path(repo: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise EditRejected("INVALID_RELATIVE_PATH")
    rel = PurePosixPath(name)
    if rel.is_absolute() or any(x in {"", ".", ".."} for x in name.split("/")):
        raise EditRejected("UNSAFE_RELATIVE_PATH")
    if rel.suffix.lower() not in EXTENSIONS:
        raise EditRejected("UNSUPPORTED_EXTENSION")
    dst = repo.joinpath(*rel.parts)
    # Refuse symlinks/junctions at every part, not just at the final file.
    cursor = repo
    for component in rel.parts:
        cursor = cursor / component
        if cursor.is_symlink() or cursor.is_junction():
            raise EditRejected("REPARSE_POINT_NOT_ALLOWED")
    if not dst.is_file() or dst.stat().st_size > MAX_BYTES:
        raise EditRejected("ORIGINAL_MISSING_OR_TOO_LARGE")
    if not dst.resolve().is_relative_to(repo.resolve()):
        raise EditRejected("OUTSIDE_REPOSITORY")
    return dst

def plan_edits(task: dict, proposal: dict) -> list[dict]:
    if task.get("schema") != "TAKY_EXECUTION_REQUEST_V1" or task.get("mode") != "BOUNDED_EDIT_PROPOSAL":
        raise EditRejected("NOT_AN_IMPLEMENTATION_TASK")
    task_id = task.get("id")
    if not isinstance(task_id, str) or len(task_id) != 32 or proposal.get("task_id") != task_id:
        raise EditRejected("TASK_ID_MISMATCH")
    if task.get("no_push") is not True or task.get("no_deploy") is not True:
        raise EditRejected("UNSAFE_TASK_CONTRACT")
    repo = Path(task["repo"]).resolve(strict=True)
    approved = task.get("allowed_files")
    edits = proposal.get("edits")
    if not isinstance(approved, list) or not 1 <= len(approved) <= MAX_FILES:
        raise EditRejected("ALLOWED_FILES_MISSING")
    if not isinstance(edits, list) or not 1 <= len(edits) <= len(approved):
        raise EditRejected("INVALID_EDIT_COUNT")
    allowed = {}
    for entry in approved:
        if not isinstance(entry, dict):
            raise EditRejected("INVALID_APPROVED_ENTRY")
        name, expected = entry.get("path"), entry.get("sha256")
        if name in allowed or not isinstance(expected, str) or len(expected) != 64:
            raise EditRejected("INVALID_APPROVED_DIGEST")
        file_path(repo, name)
        allowed[name] = expected.lower()
    seen = set()
    prepared = []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path", "replacements"}:
            raise EditRejected("UNEXPECTED_EDIT_FIELDS")
        name = edit["path"]
        if name in seen or name not in allowed:
            raise EditRejected("UNAPPROVED_OR_DUPLICATE_FILE")
        seen.add(name)
        dst = file_path(repo, name)
        before = dst.read_bytes()
        if sha(before) != allowed[name]:
            raise EditRejected("SOURCE_CHANGED_SINCE_APPROVAL")
        try:
            old = before.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise EditRejected("NON_UTF8_FILE") from exc
        replacements = edit["replacements"]
        if not isinstance(replacements, list) or not 1 <= len(replacements) <= 12:
            raise EditRejected("INVALID_REPLACEMENTS")
        updated = old
        for item in replacements:
            if not isinstance(item, dict) or set(item) != {"old", "new"}:
                raise EditRejected("INVALID_REPLACEMENT_FIELDS")
            previous, replacement = item["old"], item["new"]
            if not isinstance(previous, str) or not previous or not isinstance(replacement, str):
                raise EditRejected("EMPTY_OR_INVALID_REPLACEMENT")
            if previous == replacement or updated.count(previous) != 1:
                raise EditRejected("NON_UNIQUE_OR_NOOP_REPLACEMENT")
            updated = updated.replace(previous, replacement, 1)
        encoded = (b"\xef\xbb\xbf" if before.startswith(b"\xef\xbb\xbf") else b"") + updated.encode("utf-8")
        if len(encoded) > MAX_BYTES or encoded == before:
            raise EditRejected("OVERSIZE_OR_NOOP_RESULT")
        if dst.suffix.lower() == ".json":
            json.loads(updated)
        if dst.suffix.lower() == ".py":
            ast.parse(updated, filename=str(dst))
        preview = "".join(difflib.unified_diff(old.splitlines(True), updated.splitlines(True),
                         fromfile=name, tofile=name))
        prepared.append({"path": str(dst), "relative": name, "before": before, "after": encoded,
                         "diff": preview[:5000], "before_sha256": sha(before), "after_sha256": sha(encoded)})
    return prepared

def apply(prepared: list[dict]) -> None:
    # Validate every preimage a second time before writing anything.
    for item in prepared:
        if sha(Path(item["path"]).read_bytes()) != item["before_sha256"]:
            raise EditRejected("CONCURRENT_SOURCE_CHANGE")
    staged = []
    replaced = []
    try:
        for item in prepared:
            dst = Path(item["path"])
            fd, name = tempfile.mkstemp(prefix=".taky-edit-", dir=str(dst.parent))
            os.close(fd)
            tmp = Path(name)
            staged.append(tmp)
            tmp.write_bytes(item["after"])
            os.chmod(tmp, stat.S_IMODE(dst.stat().st_mode))
        for item, tmp in zip(prepared, staged):
            dst = Path(item["path"])
            if sha(dst.read_bytes()) != item["before_sha256"]:
                raise EditRejected("CONCURRENT_SOURCE_CHANGE")
            os.replace(tmp, dst)
            replaced.append(item)
    except Exception:
        # Restore only files modified by this transaction, never unrelated files.
        for item in reversed(replaced):
            dst = Path(item["path"])
            if sha(dst.read_bytes()) == item["after_sha256"]:
                fd, name = tempfile.mkstemp(prefix=".taky-restore-", dir=str(dst.parent))
                os.close(fd)
                rollback = Path(name)
                try:
                    rollback.write_bytes(item["before"])
                    os.replace(rollback, dst)
                finally:
                    rollback.unlink(missing_ok=True)
        raise
    finally:
        for tmp in staged:
            tmp.unlink(missing_ok=True)

def run(task: dict, proposal: dict, *, execute=False) -> dict:
    prepared = plan_edits(task, proposal)
    if execute:
        if os.getenv("TAKY_USER_EXPLICIT_AUTHORIZATION") != "1" or os.getenv("TAKY_ALLOW_SCOPED_FILE_EDIT") != "1":
            raise EditRejected("SCOPED_EDIT_AUTHORIZATION_REQUIRED")
        apply(prepared)
    return {"status": "APPLIED_UNVERIFIED" if execute else "DRY_RUN_VALID",
            "task_id": task["id"], "files": [{"path": x["relative"],
            "before_sha256": x["before_sha256"], "after_sha256": x["after_sha256"],
            "diff": x["diff"]} for x in prepared],
            "model_calls": 0, "paid_api_calls": 0}

def extract_proposal(task: dict, text: str) -> dict:
    """Accept only a complete structured model proposal, never free-form patches."""
    if len(text) > 180_000:
        raise EditRejected("MODEL_RESPONSE_OVERSIZE")
    body = text.strip()
    if body.startswith("```json") and body.endswith("```"):
        body = body[7:-3].strip()
    try:
        proposal = json.loads(body)
    except (json.JSONDecodeError, TypeError) as exc:
        raise EditRejected("MODEL_RESPONSE_NOT_STRICT_JSON") from exc
    if isinstance(proposal, dict) and isinstance(proposal.get("result"), str):
        if proposal.get("is_error") is True:
            raise EditRejected("MODEL_REPORTED_ERROR")
        candidate = proposal["result"].strip()
        if candidate.startswith("```json") and candidate.endswith("```"):
            candidate = candidate[7:-3].strip()
        proposal = json.loads(candidate)
    if not isinstance(proposal, dict) or set(proposal) != {"task_id", "edits"}:
        raise EditRejected("MODEL_PROPOSAL_SCHEMA_INVALID")
    plan_edits(task, proposal)
    return proposal

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--proposal-file")
    parser.add_argument("--extract-output-file")
    parser.add_argument("--candidate-file")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        task = json.loads(Path(args.task_file).read_text(encoding="utf-8-sig"))
        if args.extract_output_file:
            if args.apply or not args.candidate_file or args.proposal_file:
                raise EditRejected("EXTRACTION_ARGUMENTS_INVALID")
            source = Path(args.extract_output_file).read_text(encoding="utf-8-sig")
            proposal = extract_proposal(task, source)
            dst = Path(args.candidate_file)
            if dst.exists():
                raise EditRejected("CANDIDATE_ALREADY_EXISTS")
            with dst.open("x", encoding="utf-8") as stream:
                json.dump(proposal, stream, ensure_ascii=False, indent=2)
            result = {"status": "PROPOSAL_VALIDATED_NOT_APPLIED",
                      "task_id": task["id"], "proposal_file": str(dst), "model_calls": 0}
        else:
            if not args.proposal_file:
                raise EditRejected("PROPOSAL_FILE_REQUIRED")
            proposal = json.loads(Path(args.proposal_file).read_text(encoding="utf-8-sig"))
            result = run(task, proposal, execute=args.apply)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (EditRejected, OSError, KeyError, TypeError, json.JSONDecodeError, SyntaxError) as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc)[:180]}, ensure_ascii=False))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
