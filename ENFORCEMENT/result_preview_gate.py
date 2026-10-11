#!/usr/bin/env python3
"""Revision-bound result preview and release gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

VERSION = "1.0"
SHA_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
ACCEPTANCE_METHODS = {
    "SELF_VALIDATION",
    "CROSS_VALIDATION",
    "HUMAN_REVIEW",
    "RUNTIME_VALIDATION",
    "MECHANICAL_VALIDATION",
}


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _rooted(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("PREVIEW_EVIDENCE_PATH_INVALID")
    rel = Path(value)
    if rel.is_absolute():
        raise ValueError("PREVIEW_EVIDENCE_PATH_ABSOLUTE")
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("PREVIEW_EVIDENCE_PATH_ESCAPES_ROOT")
    return candidate


def validate_preview(record: dict[str, Any], root: Path) -> dict[str, Any]:
    detected: list[str] = []
    if record.get("preview_version") != VERSION:
        detected.append("RESULT_PREVIEW_VERSION_INVALID")

    task_id = record.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        detected.append("RESULT_PREVIEW_TASK_ID_MISSING")

    preview_required = record.get("preview_required")
    if not isinstance(preview_required, bool):
        detected.append("RESULT_PREVIEW_REQUIRED_FLAG_INVALID")
        preview_required = True

    if preview_required is False:
        reason = record.get("not_applicable_reason")
        if not isinstance(reason, str) or not reason.strip():
            detected.append("RESULT_PREVIEW_NOT_APPLICABLE_REASON_MISSING")
        if record.get("acceptance_result") != "NOT_APPLICABLE":
            detected.append("RESULT_PREVIEW_NOT_APPLICABLE_ACCEPTANCE_INVALID")
        return {
            "pass": not detected,
            "detected": detected,
            "preview_required": False,
            "acceptance_result": "NOT_APPLICABLE",
            "release_eligible": False,
            "preview_receipt_hash": _canonical_hash(record) if not detected else None,
        }

    revision = record.get("result_revision_hash")
    if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
        detected.append("RESULT_PREVIEW_REVISION_HASH_INVALID")

    surface = record.get("preview_surface")
    if not isinstance(surface, str) or not surface.strip():
        detected.append("RESULT_PREVIEW_SURFACE_MISSING")

    method = record.get("acceptance_method")
    if method not in ACCEPTANCE_METHODS:
        detected.append("RESULT_PREVIEW_ACCEPTANCE_METHOD_INVALID")

    reviewer = record.get("reviewer_ref")
    if not isinstance(reviewer, str) or not reviewer.strip():
        detected.append("RESULT_PREVIEW_REVIEWER_REF_MISSING")

    if record.get("acceptance_result") != "PASS":
        detected.append("RESULT_PREVIEW_ACCEPTANCE_NOT_PASS")

    evidence = record.get("preview_evidence")
    if not isinstance(evidence, list) or not evidence:
        detected.append("RESULT_PREVIEW_EVIDENCE_MISSING")
        evidence = []

    seen_paths: set[Path] = set()
    for idx, item in enumerate(evidence):
        if not isinstance(item, dict):
            detected.append(f"RESULT_PREVIEW_EVIDENCE_INVALID:{idx}")
            continue
        try:
            path = _rooted(root, item.get("evidence_path"))
        except ValueError as exc:
            detected.append(f"{exc}:{idx}")
            continue
        if path in seen_paths:
            detected.append(f"RESULT_PREVIEW_EVIDENCE_DUPLICATE:{idx}")
            continue
        seen_paths.add(path)
        if not path.is_file() or not path.stat().st_size:
            detected.append(f"RESULT_PREVIEW_EVIDENCE_FILE_MISSING:{idx}")
            continue
        expected = item.get("evidence_sha256")
        if not isinstance(expected, str) or not SHA_RE.fullmatch(expected):
            detected.append(f"RESULT_PREVIEW_EVIDENCE_HASH_INVALID:{idx}")
            continue
        if expected != _file_hash(path):
            detected.append(f"RESULT_PREVIEW_EVIDENCE_HASH_MISMATCH:{idx}")

    result_path = record.get("result_path")
    if not isinstance(result_path, str) or not result_path.strip():
        detected.append("RESULT_PREVIEW_RESULT_PATH_REQUIRED")
        result_path = None
    else:
        try:
            result_file = _rooted(root, result_path)
        except ValueError as exc:
            detected.append(str(exc))
        else:
            if not result_file.is_file() or not result_file.stat().st_size:
                detected.append("RESULT_PREVIEW_RESULT_FILE_MISSING")
            elif isinstance(revision, str) and SHA_RE.fullmatch(revision):
                if revision != _file_hash(result_file):
                    detected.append("RESULT_PREVIEW_REVISION_FILE_MISMATCH")

    receipt_core = {
        "preview_version": VERSION,
        "task_id": task_id,
        "preview_required": True,
        "result_path": result_path,
        "result_revision_hash": revision,
        "preview_surface": surface,
        "preview_evidence": evidence,
        "acceptance_result": record.get("acceptance_result"),
        "acceptance_method": method,
        "reviewer_ref": reviewer,
    }
    return {
        "pass": not detected,
        "detected": list(dict.fromkeys(detected)),
        **receipt_core,
        "release_eligible": not detected,
        "preview_receipt_hash": _canonical_hash(receipt_core) if not detected else None,
    }


def _preview_receipt_core(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "preview_version": receipt.get("preview_version"),
        "task_id": receipt.get("task_id"),
        "preview_required": receipt.get("preview_required"),
        "result_path": receipt.get("result_path"),
        "result_revision_hash": receipt.get("result_revision_hash"),
        "preview_surface": receipt.get("preview_surface"),
        "preview_evidence": receipt.get("preview_evidence"),
        "acceptance_result": receipt.get("acceptance_result"),
        "acceptance_method": receipt.get("acceptance_method"),
        "reviewer_ref": receipt.get("reviewer_ref"),
    }


def validate_release(
    preview_receipt: dict[str, Any],
    release_request: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    detected: list[str] = []

    stored_preview_hash = preview_receipt.get("preview_receipt_hash")
    receipt_core = _preview_receipt_core(preview_receipt)
    if not isinstance(stored_preview_hash, str) or not SHA_RE.fullmatch(stored_preview_hash):
        detected.append("RESULT_RELEASE_PREVIEW_RECEIPT_HASH_INVALID")
    else:
        actual_preview_hash = _canonical_hash(receipt_core)
        if stored_preview_hash != actual_preview_hash:
            detected.append("RESULT_RELEASE_PREVIEW_RECEIPT_INTEGRITY_MISMATCH")

    revalidated_preview = None
    if root is None:
        detected.append("RESULT_RELEASE_ROOT_REQUIRED")
    else:
        revalidated_preview = validate_preview(receipt_core, root)
        if revalidated_preview.get("pass") is not True:
            detected.extend(
                f"RESULT_RELEASE_PREVIEW_REVALIDATION:{code}"
                for code in revalidated_preview.get("detected", [])
            )
        elif revalidated_preview.get("preview_receipt_hash") != stored_preview_hash:
            detected.append("RESULT_RELEASE_PREVIEW_RECEIPT_REVALIDATION_HASH_MISMATCH")

    if preview_receipt.get("preview_required") is not True:
        detected.append("RESULT_RELEASE_PREVIEW_NOT_REQUIRED_RECORD")
    if preview_receipt.get("acceptance_result") != "PASS":
        detected.append("RESULT_RELEASE_ACCEPTANCE_NOT_PASS")
    if revalidated_preview is None or revalidated_preview.get("release_eligible") is not True:
        detected.append("RESULT_RELEASE_PREVIEW_NOT_ELIGIBLE")

    task_id = release_request.get("task_id")
    if task_id != preview_receipt.get("task_id"):
        detected.append("RESULT_RELEASE_TASK_ID_MISMATCH")

    revision = release_request.get("result_revision_hash")
    if revision != preview_receipt.get("result_revision_hash"):
        detected.append("RESULT_RELEASE_REVISION_MISMATCH")
    if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
        detected.append("RESULT_RELEASE_REVISION_HASH_INVALID")

    preview_hash = release_request.get("preview_receipt_hash")
    if not isinstance(preview_hash, str) or not SHA_RE.fullmatch(preview_hash):
        detected.append("RESULT_RELEASE_REQUEST_PREVIEW_HASH_INVALID")
    if preview_hash != preview_receipt.get("preview_receipt_hash"):
        detected.append("RESULT_RELEASE_PREVIEW_RECEIPT_HASH_MISMATCH")

    result_path = preview_receipt.get("result_path")
    if root is None:
        pass
    elif not isinstance(result_path, str) or not result_path.strip():
        detected.append("RESULT_RELEASE_RESULT_PATH_MISSING")
    else:
        try:
            result_file = _rooted(root, result_path)
        except ValueError as exc:
            detected.append(str(exc))
        else:
            if not result_file.is_file() or not result_file.stat().st_size:
                detected.append("RESULT_RELEASE_RESULT_FILE_MISSING")
            elif isinstance(revision, str) and SHA_RE.fullmatch(revision):
                if _file_hash(result_file) != revision:
                    detected.append("RESULT_RELEASE_RESULT_REVISION_CHANGED")

    target = release_request.get("release_target")
    if not isinstance(target, str) or not target.strip():
        detected.append("RESULT_RELEASE_TARGET_MISSING")

    payload_hash = release_request.get("release_payload_hash")
    if not isinstance(payload_hash, str) or not SHA_RE.fullmatch(payload_hash):
        detected.append("RESULT_RELEASE_PAYLOAD_HASH_INVALID")

    binding_core = {
        "task_id": task_id,
        "result_revision_hash": revision,
        "preview_receipt_hash": preview_hash,
        "release_target": target,
        "release_payload_hash": payload_hash,
    }
    return {
        "pass": not detected,
        "detected": list(dict.fromkeys(detected)),
        "release_binding_hash": _canonical_hash(binding_core) if not detected else None,
        "release_binding": binding_core if not detected else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    preview = sub.add_parser("preview")
    preview.add_argument("--record", type=Path, required=True)
    preview.add_argument("--root", type=Path, default=Path.cwd())

    release = sub.add_parser("release")
    release.add_argument("--preview-receipt", type=Path, required=True)
    release.add_argument("--release-request", type=Path, required=True)
    release.add_argument("--root", type=Path, default=Path.cwd())

    args = ap.parse_args()
    try:
        if args.command == "preview":
            record = json.loads(args.record.read_text(encoding="utf-8-sig"))
            result = validate_preview(record, args.root)
        else:
            receipt = json.loads(args.preview_receipt.read_text(encoding="utf-8-sig"))
            request = json.loads(args.release_request.read_text(encoding="utf-8-sig"))
            result = validate_release(receipt, request, args.root)
    except Exception as exc:
        result = {
            "pass": False,
            "detected": [f"RESULT_PREVIEW_INPUT_UNREADABLE:{type(exc).__name__}"],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
