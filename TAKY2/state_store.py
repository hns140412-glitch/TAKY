from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time
import uuid
from typing import Any, Dict, Tuple

from .enforcement import stable_hash


STATE_DIR = Path(__file__).with_name("state")
AUTHORITY_PATH = STATE_DIR / "authority.json"
RUNTIME_PATH = STATE_DIR / "runtime.json"
RUNTIME_EXAMPLE_PATH = STATE_DIR / "runtime.example.json"
LOCK_PATH = STATE_DIR / "runtime.lock"
KEY_ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / ".taky2")) / "TAKY2"
RUNTIME_KEY_PATH = KEY_ROOT / "runtime.key"
ANCHOR_PATH = KEY_ROOT / "runtime.anchor.json"


class StateIntegrityError(RuntimeError):
    pass


class StateConflictError(RuntimeError):
    pass


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def authority_digest(authority: Dict[str, Any]) -> str:
    return stable_hash(authority)


def load_or_create_runtime_key(path: Path = RUNTIME_KEY_PATH) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        key = path.read_bytes()
        if len(key) < 32:
            raise StateIntegrityError("runtime key is invalid")
        return key

    key = secrets.token_bytes(32)
    try:
        fd = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0),
            0o600,
        )
    except FileExistsError:
        return load_or_create_runtime_key(path)
    try:
        os.write(fd, key)
        os.fsync(fd)
    finally:
        os.close(fd)
    return key


def _runtime_payload(runtime: Dict[str, Any]) -> bytes:
    body = dict(runtime)
    body.pop("runtime_mac", None)
    return _canonical(body)


def runtime_mac(runtime: Dict[str, Any], key: bytes) -> str:
    return hmac.new(key, _runtime_payload(runtime), hashlib.sha256).hexdigest()


def verify_runtime(runtime: Dict[str, Any], key: bytes) -> None:
    actual = runtime.get("runtime_mac")
    expected = runtime_mac(runtime, key)
    if not isinstance(actual, str) or not hmac.compare_digest(actual, expected):
        raise StateIntegrityError("runtime HMAC mismatch")


def sign_runtime(runtime: Dict[str, Any], key: bytes) -> Dict[str, Any]:
    signed = dict(runtime)
    signed["runtime_mac"] = runtime_mac(signed, key)
    return signed


def _anchor_payload(anchor: Dict[str, Any]) -> bytes:
    body = dict(anchor)
    body.pop("anchor_mac", None)
    return _canonical(body)


def sign_anchor(anchor: Dict[str, Any], key: bytes) -> Dict[str, Any]:
    signed = dict(anchor)
    signed["anchor_mac"] = hmac.new(
        key, _anchor_payload(signed), hashlib.sha256
    ).hexdigest()
    return signed


def verify_anchor(anchor: Dict[str, Any], key: bytes) -> None:
    actual = anchor.get("anchor_mac")
    expected = hmac.new(key, _anchor_payload(anchor), hashlib.sha256).hexdigest()
    if not isinstance(actual, str) or not hmac.compare_digest(actual, expected):
        raise StateIntegrityError("runtime anchor HMAC mismatch")


def _write_atomic_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _verify_anchor_pair(
    runtime: Dict[str, Any],
    key: bytes,
    anchor_path: Path,
) -> None:
    if not anchor_path.exists():
        raise StateIntegrityError("runtime anchor missing")
    anchor = _load_json(anchor_path)
    verify_anchor(anchor, key)
    if anchor.get("runtime_version") != runtime.get("runtime_version"):
        raise StateIntegrityError("runtime rollback/version mismatch")
    if anchor.get("runtime_mac") != runtime.get("runtime_mac"):
        raise StateIntegrityError("runtime rollback/MAC mismatch")


def load_bundle(
    authority_path: Path = AUTHORITY_PATH,
    runtime_path: Path = RUNTIME_PATH,
    *,
    runtime_key: bytes | None = None,
    anchor_path: Path = ANCHOR_PATH,
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    authority = _load_json(authority_path)
    runtime = _load_json(runtime_path)
    key = runtime_key or load_or_create_runtime_key()
    verify_runtime(runtime, key)
    _verify_anchor_pair(runtime, key, anchor_path)

    digest = authority_digest(authority)
    if runtime.get("authority_digest") != digest:
        raise StateIntegrityError("runtime authority_digest mismatch")

    trusted = dict(authority)
    trusted.update({
        "runtime": runtime.get("runtime", {}),
        "context": runtime.get("context", {}),
        "route_ledgers": runtime.get("route_ledgers", {}),
        "preflight_receipts": runtime.get("preflight_receipts", {}),
        "evidence_registry": runtime.get("evidence_registry", {}),
        "completion_registry": runtime.get("completion_registry", {}),
        "active_attempts": runtime.get("active_attempts", {}),
        "execution_outcomes": runtime.get("execution_outcomes", {}),
        "consumed_approvals": runtime.get("consumed_approvals", {}),
        "user_events": runtime.get("user_events", {}),
        "_runtime_version": runtime.get("runtime_version"),
        "_authority_digest": digest,
    })
    return trusted, runtime, digest


def initialize_runtime(
    authority_path: Path = AUTHORITY_PATH,
    example_path: Path = RUNTIME_EXAMPLE_PATH,
    runtime_path: Path = RUNTIME_PATH,
    *,
    runtime_key: bytes | None = None,
    anchor_path: Path = ANCHOR_PATH,
    overwrite: bool = False,
) -> Dict[str, Any]:
    if anchor_path.exists() and not overwrite:
        raise StateConflictError("runtime already initialized")
    if runtime_path.exists() and not overwrite:
        raise StateConflictError("runtime state already exists")

    authority = _load_json(authority_path)
    example = _load_json(example_path)
    example["runtime_version"] = 1
    example["authority_digest"] = authority_digest(authority)
    key = runtime_key or load_or_create_runtime_key()
    signed = sign_runtime(example, key)
    anchor = sign_anchor({
        "runtime_version": signed["runtime_version"],
        "runtime_mac": signed["runtime_mac"],
    }, key)
    _write_atomic_json(runtime_path, signed)
    _write_atomic_json(anchor_path, anchor)
    return signed


def _acquire_lock(path: Path, timeout_s: float = 3.0, stale_s: float = 30.0) -> int:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            return os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0),
            )
        except FileExistsError:
            try:
                age = time.time() - path.stat().st_mtime
                if age > stale_s:
                    path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise StateConflictError("runtime state lock timeout")
            time.sleep(0.05)


def save_runtime(
    runtime: Dict[str, Any],
    *,
    expected_version: int,
    authority_digest_value: str,
    runtime_path: Path = RUNTIME_PATH,
    lock_path: Path = LOCK_PATH,
    runtime_key: bytes | None = None,
    anchor_path: Path = ANCHOR_PATH,
) -> Dict[str, Any]:
    key = runtime_key or load_or_create_runtime_key()
    lock_fd = _acquire_lock(lock_path)
    try:
        current = _load_json(runtime_path)
        verify_runtime(current, key)
        _verify_anchor_pair(current, key, anchor_path)
        if current.get("runtime_version") != expected_version:
            raise StateConflictError("runtime version changed")

        updated = dict(runtime)
        updated["runtime_version"] = expected_version + 1
        updated["authority_digest"] = authority_digest_value
        updated = sign_runtime(updated, key)
        anchor = sign_anchor({
            "runtime_version": updated["runtime_version"],
            "runtime_mac": updated["runtime_mac"],
        }, key)

        # Cross-file update is fail-closed: a crash between these writes causes
        # runtime/anchor mismatch until repaired, never silent rollback.
        _write_atomic_json(runtime_path, updated)
        _write_atomic_json(anchor_path, anchor)
        return updated
    finally:
        os.close(lock_fd)
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass
