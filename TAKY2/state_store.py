from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time
import uuid
from typing import Any, Callable, Dict, Tuple

from .enforcement import (
    ACCOUNT_AUTH_SOURCE,
    ACCOUNT_IDENTITY_PROVIDER,
    BINDING_FIELDS,
    stable_hash,
)


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
        "execution_calls": runtime.get("execution_calls", {}),
        "consumed_approvals": runtime.get("consumed_approvals", {}),
        "user_events": runtime.get("user_events", {}),
        "authority_rebind_history": runtime.get("authority_rebind_history", []),
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


_ACCOUNT_BINDING_IMMUTABLE_FIELDS = (
    "account",
    "identity_provider",
    "principal_id",
    "family_id",
    "self_member_id",
    "source",
    "verified_by",
    "first_bound_evidence_ref",
    "first_bound_session_id",
)


def _validated_account_binding(runtime: Dict[str, Any]) -> Dict[str, Any] | None:
    section = runtime.get("runtime", {})
    if not isinstance(section, dict):
        raise StateIntegrityError("runtime section must be an object")
    binding = section.get("account_attestation")
    if binding is None:
        return None
    if not isinstance(binding, dict):
        raise StateIntegrityError("account binding must be an object")
    if binding.get("verified") is not True:
        raise StateIntegrityError("account binding must be verified")
    if binding.get("binding_mode") != "FIRST_AUTH_RUNTIME":
        raise StateIntegrityError("account binding mode is invalid")
    required = tuple(binding.get(field) for field in _ACCOUNT_BINDING_IMMUTABLE_FIELDS)
    if not all(isinstance(value, str) and value.strip() for value in required):
        raise StateIntegrityError("account binding is incomplete")
    if any(value != value.strip() for value in required):
        raise StateIntegrityError("account binding immutable fields must be canonical")
    if not isinstance(binding.get("evidence_ref"), str) or not binding.get("evidence_ref").strip():
        raise StateIntegrityError("account binding evidence_ref missing")
    if not isinstance(binding.get("session_id"), str) or not binding.get("session_id").strip():
        raise StateIntegrityError("account binding session_id missing")
    if binding["evidence_ref"] != binding["evidence_ref"].strip():
        raise StateIntegrityError("account binding evidence_ref must be canonical")
    if binding["session_id"] != binding["session_id"].strip():
        raise StateIntegrityError("account binding session_id must be canonical")
    if binding.get("source") != ACCOUNT_AUTH_SOURCE:
        raise StateIntegrityError("account binding source is not trusted")
    if binding.get("identity_provider") != ACCOUNT_IDENTITY_PROVIDER:
        raise StateIntegrityError("account binding identity provider is not trusted")
    verifier_token = binding["verified_by"].casefold()
    if verifier_token in {
        binding["account"].casefold(),
        binding["principal_id"].casefold(),
        binding["self_member_id"].casefold(),
    }:
        raise StateIntegrityError("account principal/member cannot self-verify binding")
    return binding


def _validate_account_binding_transition(
    current: Dict[str, Any],
    candidate: Dict[str, Any],
) -> None:
    existing = _validated_account_binding(current)
    proposed = _validated_account_binding(candidate)
    if existing is None:
        return
    if proposed is None:
        raise StateIntegrityError("account binding cannot be cleared after first authentication")
    for field in _ACCOUNT_BINDING_IMMUTABLE_FIELDS:
        if proposed.get(field) != existing.get(field):
            raise StateIntegrityError(f"account binding immutable field changed: {field}")


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

        _validate_account_binding_transition(current, runtime)

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


def _key_amend_diff(
    current_authority: Dict[str, Any],
    new_authority: Dict[str, Any],
    user_event: Dict[str, Any],
) -> list[Dict[str, Any]]:
    current_key = current_authority.get("key", {})
    new_key = new_authority.get("key", {})
    if not isinstance(current_key, dict) or not isinstance(new_key, dict):
        raise StateIntegrityError("authority key must be an object")

    diffs: list[Dict[str, Any]] = []
    authorized_deletions = user_event.get("authorized_key_deletions", [])
    if not isinstance(authorized_deletions, list):
        raise StateIntegrityError("authorized_key_deletions must be a list")

    for name in sorted(BINDING_FIELDS):
        old_field = current_key.get(name)
        new_field = new_key.get(name)
        if stable_hash(old_field) == stable_hash(new_field):
            continue

        if new_field is None:
            if name not in authorized_deletions:
                raise StateIntegrityError(f"KEY_AMEND deletion not authorized: {name}")
            diffs.append({
                "field": name,
                "change": "DELETE",
                "old_version": old_field.get("version") if isinstance(old_field, dict) else None,
                "new_version": None,
            })
            continue

        if not isinstance(new_field, dict):
            raise StateIntegrityError(f"KEY_AMEND field must be structured: {name}")
        new_version = new_field.get("version")
        new_scope = new_field.get("scope")
        provenance = new_field.get("provenance")
        source_ref = new_field.get("source_ref")
        if provenance not in {"USER_STATED", "USER_CONFIRMED"}:
            raise StateIntegrityError(f"KEY_AMEND USER provenance required: {name}")
        if not isinstance(source_ref, str) or not source_ref.strip():
            raise StateIntegrityError(f"KEY_AMEND source_ref missing: {name}")
        source_registry = new_authority.get("source_registry", {})
        source = source_registry.get(source_ref) if isinstance(source_registry, dict) else None
        if not isinstance(source, dict) or source.get("actor") != "USER":
            raise StateIntegrityError(f"KEY_AMEND source_ref is not trusted USER evidence: {name}")
        if not isinstance(new_version, int) or new_version < 1:
            raise StateIntegrityError(f"KEY_AMEND version missing: {name}")
        if not isinstance(new_scope, str) or not new_scope.strip():
            raise StateIntegrityError(f"KEY_AMEND scope missing: {name}")

        old_version = old_field.get("version") if isinstance(old_field, dict) else None
        if isinstance(old_version, int):
            if new_version != old_version + 1:
                raise StateIntegrityError(f"KEY_AMEND version must increment exactly once: {name}")
        elif new_version != 1:
            raise StateIntegrityError(f"new KEY_AMEND field must start at version 1: {name}")

        diffs.append({
            "field": name,
            "change": "UPDATE" if old_field is not None else "ADD",
            "old_version": old_version,
            "new_version": new_version,
            "old_scope": old_field.get("scope") if isinstance(old_field, dict) else None,
            "new_scope": new_scope,
            "old_hash": stable_hash(old_field),
            "new_hash": stable_hash(new_field),
        })

    if diffs and user_event.get("key_amend") is not True:
        raise StateIntegrityError("explicit KEY_AMEND authorization required")
    return diffs


def stage_authority_rebind(
    runtime: Dict[str, Any],
    *,
    current_authority: Dict[str, Any],
    new_authority: Dict[str, Any],
    user_event: Dict[str, Any],
    event_verifier: Callable[[Dict[str, Any]], bool],
    verifier_id: str,
) -> Dict[str, Any]:
    old_digest = runtime.get("authority_digest")
    current_digest = authority_digest(current_authority)
    new_digest = authority_digest(new_authority)
    if not isinstance(old_digest, str) or not old_digest:
        raise StateIntegrityError("current authority digest missing")
    if old_digest != current_digest:
        raise StateIntegrityError("current authority does not match bound digest")
    if old_digest == new_digest:
        raise StateConflictError("authority digest is unchanged")
    if not callable(event_verifier) or event_verifier(user_event) is not True:
        raise StateIntegrityError("authority rebind USER event verification failed")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise StateIntegrityError("authority rebind verifier_id required")
    if (
        user_event.get("actor") != "USER"
        or user_event.get("kind") != "authority_rebind"
        or user_event.get("explicit") is not True
        or user_event.get("authorized_new_digest") != new_digest
    ):
        raise StateIntegrityError("explicit USER authority rebind authorization required")
    event_ref = user_event.get("event_ref")
    if not isinstance(event_ref, str) or not event_ref.strip():
        raise StateIntegrityError("authority rebind event_ref required")
    key_diff = _key_amend_diff(current_authority, new_authority, user_event)

    updated = dict(runtime)
    if updated.get("authority_rebind_request"):
        raise StateConflictError("authority rebind request already staged")
    updated["authority_rebind_request"] = {
        "old_digest": old_digest,
        "new_digest": new_digest,
        "event_ref": event_ref.strip(),
        "actor": "USER",
        "explicit": True,
        "verified_by": verifier_id.strip(),
        "key_amend": bool(key_diff),
        "key_diff": key_diff,
    }
    return updated


def rebind_authority(
    authority_path: Path = AUTHORITY_PATH,
    runtime_path: Path = RUNTIME_PATH,
    *,
    lock_path: Path = LOCK_PATH,
    runtime_key: bytes | None = None,
    anchor_path: Path = ANCHOR_PATH,
) -> Dict[str, Any]:
    key = runtime_key or load_or_create_runtime_key()
    runtime = _load_json(runtime_path)
    verify_runtime(runtime, key)
    _verify_anchor_pair(runtime, key, anchor_path)

    old_digest = runtime.get("authority_digest")
    new_authority = _load_json(authority_path)
    new_digest = authority_digest(new_authority)
    if old_digest == new_digest:
        raise StateConflictError("authority already bound")

    request = runtime.get("authority_rebind_request")
    if not isinstance(request, dict):
        raise StateIntegrityError("staged authority rebind request missing")
    if (
        request.get("old_digest") != old_digest
        or request.get("new_digest") != new_digest
        or request.get("actor") != "USER"
        or request.get("explicit") is not True
        or not isinstance(request.get("verified_by"), str)
        or not request.get("verified_by")
        or not isinstance(request.get("key_diff", []), list)
    ):
        raise StateIntegrityError("authority rebind request does not match authority change")

    updated = dict(runtime)
    updated.pop("runtime_mac", None)
    updated.pop("authority_rebind_request", None)
    history = list(updated.get("authority_rebind_history", []))
    history.append({
        "old_digest": old_digest,
        "new_digest": new_digest,
        "event_ref": request.get("event_ref"),
        "verified_by": request.get("verified_by"),
        "key_amend": bool(request.get("key_amend")),
        "key_diff": list(request.get("key_diff", [])),
    })
    updated["authority_rebind_history"] = history

    return save_runtime(
        updated,
        expected_version=runtime["runtime_version"],
        authority_digest_value=new_digest,
        runtime_path=runtime_path,
        lock_path=lock_path,
        runtime_key=key,
        anchor_path=anchor_path,
    )
