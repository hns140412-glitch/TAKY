#!/usr/bin/env python3
"""TAKY atomic CURRENT checkpoint writer / resume guard.

Stdlib-only repository utility. It validates compact checkpoint records,
writes CURRENT atomically, and appends immutable minimal HISTORY evidence.
It does not claim hosted ChatGPT auto-invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED = (
    "checkpoint_version",
    "task_id",
    "namespace",
    "atomic_unit",
    "status",
    "done",
    "open",
    "next",
    "corrections",
    "source_refs",
    "updated_at",
)
ALLOWED_STATUS = {"RUNNING", "BLOCKED", "COMPLETE"}
SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(value: str) -> str:
    out = SAFE.sub("_", value.strip()).strip("._")
    if not out:
        raise ValueError("unsafe or empty path component")
    return out


def _parse_datetime(value: str) -> None:
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in REQUIRED:
        if key not in record:
            failures.append(f"MISSING_{key.upper()}")

    if record.get("checkpoint_version") != "1.0":
        failures.append("CHECKPOINT_VERSION_UNSUPPORTED")
    for key in ("task_id", "namespace", "atomic_unit", "updated_at"):
        if key in record and (not isinstance(record[key], str) or not record[key].strip()):
            failures.append(f"INVALID_{key.upper()}")
    if record.get("status") not in ALLOWED_STATUS:
        failures.append("INVALID_STATUS")
    for key in ("done", "open", "corrections", "source_refs"):
        value = record.get(key)
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            failures.append(f"INVALID_{key.upper()}")
    if "next" in record and record["next"] is not None and not isinstance(record["next"], str):
        failures.append("INVALID_NEXT")
    try:
        if isinstance(record.get("updated_at"), str):
            _parse_datetime(record["updated_at"])
    except ValueError:
        failures.append("INVALID_UPDATED_AT")
    return failures


def canonical_bytes(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def checkpoint_hash(record: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(record)).hexdigest()


def paths(repo_root: Path, record: dict[str, Any]) -> tuple[Path, Path]:
    namespace = _slug(str(record["namespace"]))
    task_id = _slug(str(record["task_id"]))
    current = repo_root / "CURRENT" / namespace / f"{task_id}.json"
    stamp = str(record["updated_at"]).replace(":", "").replace("+", "_").replace("/", "_")
    unit = _slug(str(record["atomic_unit"]))
    history = repo_root / "HISTORY" / "CHECKPOINTS" / namespace / task_id / f"{stamp}__{unit}.json"
    return current, history


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def persist(record: dict[str, Any], state_root: Path, append_history: bool = True) -> dict[str, Any]:
    failures = validate(record)
    if failures:
        return {"pass": False, "detected": failures}

    current, history = paths(state_root, record)
    enriched = dict(record)
    enriched["checkpoint_hash"] = checkpoint_hash(record)
    payload = canonical_bytes(enriched)

    # Check immutable history before mutating CURRENT. A conflicting history
    # identity must never advance the active resume pointer.
    if append_history and history.exists():
        existing = history.read_bytes()
        if existing != payload:
            return {
                "pass": False,
                "detected": ["HISTORY_IMMUTABILITY_CONFLICT"],
                "current_path": str(current),
                "history_path": str(history),
            }

    _atomic_write(current, payload)
    if append_history and not history.exists():
        _atomic_write(history, payload)

    return {
        "pass": True,
        "detected": [],
        "current_path": str(current),
        "history_path": str(history) if append_history else None,
        "checkpoint_hash": enriched["checkpoint_hash"],
    }


def guard(
    state_root: Path,
    namespace: str,
    task_id: str,
    expected_atomic_unit: str | None = None,
) -> dict[str, Any]:
    current = state_root / "CURRENT" / _slug(namespace) / f"{_slug(task_id)}.json"
    if not current.exists():
        return {"pass": False, "detected": ["CURRENT_CHECKPOINT_MISSING"], "current_path": str(current)}
    try:
        record = json.loads(current.read_text(encoding="utf-8"))
    except Exception:
        return {"pass": False, "detected": ["CURRENT_CHECKPOINT_UNREADABLE"], "current_path": str(current)}

    failures = validate(record)
    if expected_atomic_unit is not None and record.get("atomic_unit") != expected_atomic_unit:
        failures.append("CURRENT_CHECKPOINT_STALE_OR_WRONG_UNIT")

    return {
        "pass": not failures,
        "detected": failures,
        "current_path": str(current),
        "checkpoint": record,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write")
    write.add_argument("--record", type=Path, required=True)
    write.add_argument("--repo-root", type=Path, default=Path.cwd())
    write.add_argument("--state-root", type=Path)
    write.add_argument("--no-history", action="store_true")

    check = sub.add_parser("guard")
    check.add_argument("--namespace", required=True)
    check.add_argument("--task-id", required=True)
    check.add_argument("--expected-atomic-unit")
    check.add_argument("--repo-root", type=Path, default=Path.cwd())
    check.add_argument("--state-root", type=Path)

    args = ap.parse_args()

    env_state_root = os.environ.get("TAKY_STATE_ROOT")
    state_root = (
        args.state_root
        if args.state_root is not None
        else Path(env_state_root).expanduser()
        if env_state_root
        else args.repo_root
    ).resolve()

    if args.command == "write":
        record = json.loads(args.record.read_text(encoding="utf-8"))
        result = persist(record, state_root, append_history=not args.no_history)
        result["state_root"] = str(state_root)
    else:
        result = guard(
            state_root,
            namespace=args.namespace,
            task_id=args.task_id,
            expected_atomic_unit=args.expected_atomic_unit,
        )
        result["state_root"] = str(state_root)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
