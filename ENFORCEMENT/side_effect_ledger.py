#!/usr/bin/env python3
"""TAKY durable side-effect ledger.

Records material external/repository side effects separately from ordinary
checkpoint progress so resume/retry can fail closed before duplicating a
non-idempotent action.
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

from evidence_ref_validator import validate_ref

VERSION = "1.0"
STATUSES = {"PLANNED", "APPLYING", "APPLIED", "VERIFIED", "FAILED", "COMPENSATED"}
REPLAY_POLICIES = {"FORBID", "IDEMPOTENT_RETRY", "VERIFY_THEN_RETRY", "COMPENSATE"}
ALLOWED_STATUS_TRANSITIONS = {
    "PLANNED": {"PLANNED", "APPLYING", "APPLIED", "FAILED"},
    "APPLYING": {"APPLYING", "APPLIED", "FAILED"},
    "APPLIED": {"APPLIED", "VERIFIED", "COMPENSATED"},
    "VERIFIED": {"VERIFIED", "COMPENSATED"},
    "FAILED": {"FAILED", "APPLYING", "COMPENSATED"},
    "COMPENSATED": {"COMPENSATED", "PLANNED", "APPLYING"},
}
SAFE = re.compile(r"[^A-Za-z0-9._-]+")

REQUIRED = (
    "ledger_version",
    "effect_id",
    "task_id",
    "namespace",
    "action_kind",
    "action_payload_hash",
    "idempotency_key",
    "state_schema_version",
    "target_ref",
    "execution_status",
    "replay_policy",
    "updated_at",
)


def _slug(value: str) -> str:
    out = SAFE.sub("_", value.strip()).strip("._")
    if not out:
        raise ValueError("unsafe or empty path component")
    return out


def _parse_datetime(value: str) -> None:
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def record_hash(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in REQUIRED:
        if key not in record:
            failures.append(f"SIDE_EFFECT_MISSING_{key.upper()}")

    if record.get("ledger_version") != VERSION:
        failures.append("SIDE_EFFECT_LEDGER_VERSION_UNSUPPORTED")

    for key in (
        "effect_id",
        "task_id",
        "namespace",
        "action_kind",
        "action_payload_hash",
        "idempotency_key",
        "state_schema_version",
        "target_ref",
        "updated_at",
    ):
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"SIDE_EFFECT_INVALID_{key.upper()}")

    payload_hash = record.get("action_payload_hash")
    if isinstance(payload_hash, str) and not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", payload_hash):
        failures.append("SIDE_EFFECT_ACTION_PAYLOAD_HASH_INVALID")

    if record.get("execution_status") not in STATUSES:
        failures.append("SIDE_EFFECT_EXECUTION_STATUS_INVALID")
    if record.get("replay_policy") not in REPLAY_POLICIES:
        failures.append("SIDE_EFFECT_REPLAY_POLICY_INVALID")

    for key in ("before_state_ref", "before_state_hash", "after_state_ref", "after_state_hash"):
        value = record.get(key)
        if value is not None and not isinstance(value, str):
            failures.append(f"SIDE_EFFECT_INVALID_{key.upper()}")

    if record.get("execution_status") in {"APPLIED", "VERIFIED"}:
        if not any(record.get(k) for k in ("after_state_ref", "after_state_hash", "external_receipt")):
            failures.append("SIDE_EFFECT_APPLIED_WITHOUT_AFTER_EVIDENCE")

    approval_ref = record.get("approval_ref")
    if approval_ref is not None and not isinstance(approval_ref, str):
        failures.append("SIDE_EFFECT_APPROVAL_REF_INVALID")

    external_receipt = record.get("external_receipt")
    if external_receipt is not None and not isinstance(external_receipt, (str, dict)):
        failures.append("SIDE_EFFECT_EXTERNAL_RECEIPT_INVALID")

    compensation_ref = record.get("compensation_ref")
    if compensation_ref is not None and (
        not isinstance(compensation_ref, str) or not compensation_ref.strip()
    ):
        failures.append("SIDE_EFFECT_COMPENSATION_REF_INVALID")
    if record.get("execution_status") == "COMPENSATED":
        if record.get("replay_policy") != "COMPENSATE":
            failures.append("SIDE_EFFECT_COMPENSATED_POLICY_INVALID")
        if not compensation_ref:
            failures.append("SIDE_EFFECT_COMPENSATION_EVIDENCE_MISSING")

    try:
        if isinstance(record.get("updated_at"), str):
            _parse_datetime(record["updated_at"])
    except ValueError:
        failures.append("SIDE_EFFECT_UPDATED_AT_INVALID")

    return list(dict.fromkeys(failures))


def paths(state_root: Path, record: dict[str, Any]) -> tuple[Path, Path]:
    namespace = _slug(str(record["namespace"]))
    task_id = _slug(str(record["task_id"]))
    effect_id = _slug(str(record["effect_id"]))
    current = (
        state_root
        / "CURRENT"
        / "SIDE_EFFECTS"
        / namespace
        / task_id
        / f"{effect_id}.json"
    )
    stamp = str(record["updated_at"]).replace(":", "").replace("+", "_").replace("/", "_")
    status = _slug(str(record["execution_status"]))
    history = (
        state_root
        / "HISTORY"
        / "SIDE_EFFECTS"
        / namespace
        / task_id
        / effect_id
        / f"{stamp}__{status}.json"
    )
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


def _write_immutable(path: Path, payload: bytes) -> tuple[bool, str | None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            return (path.read_bytes() == payload, "SIDE_EFFECT_HISTORY_IMMUTABILITY_CONFLICT")
        except OSError:
            return (False, "SIDE_EFFECT_HISTORY_UNREADABLE")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return True, None


def _history_dir(state_root: Path, *, namespace: str, task_id: str, effect_id: str) -> Path:
    return (
        state_root
        / "HISTORY"
        / "SIDE_EFFECTS"
        / _slug(namespace)
        / _slug(task_id)
        / _slug(effect_id)
    )


def _stable_effect_claim_key(
    *,
    namespace: str,
    task_id: str,
    effect_id: str,
    idempotency_key: str,
    action_payload_hash: str,
    action_kind: str,
    target_ref: str,
    attempt_scope: str,
) -> str:
    identity = {
        "namespace": namespace,
        "task_id": task_id,
        "effect_id": effect_id,
        "idempotency_key": idempotency_key,
        "action_payload_hash": action_payload_hash,
        "action_kind": action_kind,
        "target_ref": target_ref,
        "attempt_scope": attempt_scope,
    }
    return record_hash(identity)


def _acquire_effect_lock(current: Path) -> tuple[Path | None, str | None]:
    current.parent.mkdir(parents=True, exist_ok=True)
    lock_path = current.with_name(current.name + ".lock")
    try:
        fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return None, "SIDE_EFFECT_CONCURRENT_WRITE"
    with os.fdopen(fd, "wb") as handle:
        handle.write(f"pid={os.getpid()}\n".encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    return lock_path, None


def _history_records(
    state_root: Path,
    *,
    namespace: str,
    task_id: str,
    effect_id: str,
) -> list[tuple[datetime, dict[str, Any]]]:
    """Integrity-valid HISTORY records for one effect, oldest first."""
    history_dir = _history_dir(
        state_root,
        namespace=namespace,
        task_id=task_id,
        effect_id=effect_id,
    )
    if not history_dir.exists():
        return []
    records: list[tuple[datetime, dict[str, Any]]] = []
    for path in history_dir.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            if _validate_existing_integrity(item):
                continue
            stamp = datetime.fromisoformat(str(item.get("updated_at")).replace("Z", "+00:00"))
        except Exception:
            continue
        records.append((stamp, item))
    records.sort(key=lambda entry: entry[0])
    return records


def _latest_history_record(
    state_root: Path,
    *,
    namespace: str,
    task_id: str,
    effect_id: str,
) -> dict[str, Any] | None:
    records = _history_records(
        state_root,
        namespace=namespace,
        task_id=task_id,
        effect_id=effect_id,
    )
    return records[-1][1] if records else None


def _validate_history_consistency(
    state_root: Path,
    current_record: dict[str, Any],
) -> list[str]:
    records = _history_records(
        state_root,
        namespace=str(current_record.get("namespace", "")),
        task_id=str(current_record.get("task_id", "")),
        effect_id=str(current_record.get("effect_id", "")),
    )
    if not records:
        return []

    # CURRENT must be the newest HISTORY record.
    latest_history = records[-1][1]
    current_hash = current_record.get("record_hash")
    if latest_history.get("record_hash") != current_hash:
        try:
            current_time = datetime.fromisoformat(
                str(current_record.get("updated_at")).replace("Z", "+00:00")
            )
        except Exception:
            return ["SIDE_EFFECT_HISTORY_TIME_INVALID"]
        if records[-1][0] > current_time:
            return ["SIDE_EFFECT_CURRENT_STALE_VS_HISTORY"]
        return ["SIDE_EFFECT_CURRENT_HISTORY_DIVERGENCE"]

    # The time-ordered HISTORY must form a valid transition chain. Reachability
    # alone cannot order records because the status graph has cycles
    # (COMPENSATED -> APPLYING -> APPLIED -> COMPENSATED).
    for (_, previous), (_, following) in zip(records, records[1:]):
        if not _validate_transition(previous, following):
            continue
        if previous.get("record_hash") != current_hash and not _validate_transition(
            current_record, previous
        ):
            return ["SIDE_EFFECT_HISTORY_FORWARD_DESCENDANT"]
        return ["SIDE_EFFECT_CURRENT_HISTORY_DIVERGENCE"]
    return []


def _claim_execution(
    state_root: Path,
    *,
    namespace: str,
    task_id: str,
    effect_id: str,
    claim_key: str,
    decision: str,
) -> tuple[bool, str]:
    claim_dir = (
        state_root
        / "HISTORY"
        / "SIDE_EFFECT_CLAIMS"
        / _slug(namespace)
        / _slug(task_id)
        / _slug(effect_id)
    )
    claim_dir.mkdir(parents=True, exist_ok=True)
    claim_name = hashlib.sha256(claim_key.encode("utf-8")).hexdigest() + ".json"
    claim_path = claim_dir / claim_name
    payload = canonical_bytes({
        "namespace": namespace,
        "task_id": task_id,
        "effect_id": effect_id,
        "claim_key": claim_key,
        "decision": decision,
        "claimed_at": datetime.now().astimezone().isoformat(),
    })
    try:
        fd = os.open(str(claim_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False, str(claim_path)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            claim_path.unlink()
        except OSError:
            pass
        raise
    return True, str(claim_path)


def release_claim(state_root: Path, claim_path_value: object) -> dict[str, Any]:
    if not isinstance(claim_path_value, str) or not claim_path_value.strip():
        return {"pass": False, "detected": ["SIDE_EFFECT_CLAIM_PATH_INVALID"]}
    claim_path = Path(claim_path_value).resolve()
    claim_root = (state_root / "HISTORY" / "SIDE_EFFECT_CLAIMS").resolve()
    try:
        claim_path.relative_to(claim_root)
    except ValueError:
        return {"pass": False, "detected": ["SIDE_EFFECT_CLAIM_PATH_OUTSIDE_ROOT"]}
    if not claim_path.exists():
        return {"pass": True, "detected": [], "released": False}
    try:
        claim_path.unlink()
    except OSError:
        return {"pass": False, "detected": ["SIDE_EFFECT_CLAIM_RELEASE_FAILED"]}
    return {"pass": True, "detected": [], "released": True}


def _validate_existing_integrity(existing: dict[str, Any]) -> list[str]:
    failures = validate(existing)
    stored_hash = existing.get("record_hash")
    unhashed = dict(existing)
    unhashed.pop("record_hash", None)
    if stored_hash != record_hash(unhashed):
        failures.append("SIDE_EFFECT_CURRENT_INTEGRITY_MISMATCH")
    return list(dict.fromkeys(failures))


def _validate_transition(existing: dict[str, Any], record: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    immutable_fields = (
        "namespace",
        "task_id",
        "effect_id",
        "idempotency_key",
        "action_payload_hash",
        "action_kind",
        "target_ref",
        "state_schema_version",
        "replay_policy",
    )
    for key in immutable_fields:
        if existing.get(key) != record.get(key):
            failures.append(f"SIDE_EFFECT_{key.upper()}_MISMATCH")

    old_status = existing.get("execution_status")
    new_status = record.get("execution_status")
    if existing.get("compensation_ref") and not (
        new_status == "COMPENSATED" and old_status != "COMPENSATED"
    ):
        for key in ("compensation_ref", "compensation_evidence"):
            if existing.get(key) != record.get(key):
                failures.append(f"SIDE_EFFECT_{key.upper()}_MISMATCH")
    allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        failures.append("SIDE_EFFECT_STATUS_TRANSITION_INVALID")

    if new_status == "COMPENSATED" and old_status != "COMPENSATED":
        if existing.get("replay_policy") != "COMPENSATE":
            failures.append("SIDE_EFFECT_COMPENSATION_POLICY_MISMATCH")
        if not record.get("compensation_ref"):
            failures.append("SIDE_EFFECT_COMPENSATION_EVIDENCE_MISSING")

    if old_status == "COMPENSATED" and new_status in {"PLANNED", "APPLYING"}:
        if not existing.get("compensation_ref"):
            failures.append("SIDE_EFFECT_COMPENSATED_REOPEN_WITHOUT_EVIDENCE")

    return list(dict.fromkeys(failures))


def _allow_with_claim(
    state_root: Path,
    *,
    namespace: str,
    task_id: str,
    effect_id: str,
    claim_key: str,
    decision: str,
    current_path: Path,
    ledger_record: dict[str, Any] | None,
    reserve: bool,
) -> dict[str, Any]:
    if not reserve:
        return {
            "pass": True,
            "detected": [],
            "decision": decision,
            "current_path": str(current_path),
            "claim_path": None,
            "claim_required": True,
            "ledger_record": ledger_record,
        }
    claimed, claim_path = _claim_execution(
        state_root,
        namespace=namespace,
        task_id=task_id,
        effect_id=effect_id,
        claim_key=claim_key,
        decision=decision,
    )
    if not claimed:
        return {
            "pass": False,
            "detected": ["SIDE_EFFECT_EXECUTION_ALREADY_CLAIMED"],
            "decision": "BLOCK_CONCURRENT_DUPLICATE",
            "current_path": str(current_path),
            "claim_path": claim_path,
            "ledger_record": ledger_record,
        }
    return {
        "pass": True,
        "detected": [],
        "decision": decision,
        "current_path": str(current_path),
        "claim_path": claim_path,
        "claim_required": False,
        "ledger_record": ledger_record,
    }


def _compensation_identity(record: dict[str, Any], state_root: Path) -> tuple[str | None, list[str]]:
    """Use the existing evidence owner to verify pinned, locally recoverable bytes."""
    evidence = record.get("compensation_evidence")
    if not isinstance(evidence, dict) or evidence.get("source_kind") != "repo_file":
        return None, ["SIDE_EFFECT_COMPENSATION_EVIDENCE_UNVERIFIABLE"]
    if evidence.get("source_id") != record.get("compensation_ref"):
        return None, ["SIDE_EFFECT_COMPENSATION_EVIDENCE_REF_MISMATCH"]
    try:
        verified, reason = validate_ref(evidence, state_root)
    except (OSError, ValueError, RuntimeError):
        verified, reason = False, "UNREADABLE"
    if not verified:
        return None, [f"SIDE_EFFECT_COMPENSATION_EVIDENCE_INVALID:{reason}"]
    # Neither path aliases, source labels nor record timestamps grant a new attempt.
    return "COMPENSATION:sha256:" + evidence["sha256"].lower(), []


def persist(record: dict[str, Any], state_root: Path, append_history: bool = True) -> dict[str, Any]:
    failures = validate(record)
    if record.get("execution_status") == "COMPENSATED" or record.get("compensation_ref"):
        _, evidence_failures = _compensation_identity(record, state_root)
        failures.extend(evidence_failures)
    if failures:
        return {"pass": False, "detected": failures}

    current, history = paths(state_root, record)
    enriched = dict(record)
    enriched["record_hash"] = record_hash(record)
    payload = canonical_bytes(enriched)

    lock_path, lock_error = _acquire_effect_lock(current)
    if lock_error:
        return {
            "pass": False,
            "detected": [lock_error],
            "current_path": str(current),
        }

    try:
        current_snapshot: bytes | None = None
        if current.exists():
            try:
                current_snapshot = current.read_bytes()
                existing = json.loads(current_snapshot.decode("utf-8"))
            except Exception:
                return {
                    "pass": False,
                    "detected": ["SIDE_EFFECT_CURRENT_UNREADABLE"],
                    "current_path": str(current),
                }
            existing_failures = _validate_existing_integrity(existing)
            existing_failures.extend(_validate_history_consistency(state_root, existing))
            existing_failures.extend(_validate_transition(existing, record))
            if existing_failures:
                return {
                    "pass": False,
                    "detected": list(dict.fromkeys(existing_failures)),
                    "current_path": str(current),
                }
        else:
            history_dir = _history_dir(
                state_root,
                namespace=str(record["namespace"]),
                task_id=str(record["task_id"]),
                effect_id=str(record["effect_id"]),
            )
            if history_dir.exists() and any(history_dir.glob("*.json")):
                return {
                    "pass": False,
                    "detected": ["SIDE_EFFECT_CURRENT_MISSING_HISTORY_PRESENT"],
                    "current_path": str(current),
                    "history_dir": str(history_dir),
                }

        if append_history:
            history_ok, history_error = _write_immutable(history, payload)
            if not history_ok:
                return {
                    "pass": False,
                    "detected": [history_error or "SIDE_EFFECT_HISTORY_IMMUTABILITY_CONFLICT"],
                    "current_path": str(current),
                    "history_path": str(history),
                }

        try:
            observed_snapshot = current.read_bytes() if current.exists() else None
        except OSError:
            return {
                "pass": False,
                "detected": ["SIDE_EFFECT_CURRENT_CAS_UNREADABLE"],
                "current_path": str(current),
                "history_path": str(history) if append_history else None,
            }
        if observed_snapshot != current_snapshot:
            return {
                "pass": False,
                "detected": ["SIDE_EFFECT_CURRENT_CAS_MISMATCH"],
                "current_path": str(current),
                "history_path": str(history) if append_history else None,
            }

        _atomic_write(current, payload)

        return {
            "pass": True,
            "detected": [],
            "current_path": str(current),
            "history_path": str(history) if append_history else None,
            "record_hash": enriched["record_hash"],
        }
    finally:
        if lock_path is not None:
            try:
                lock_path.unlink()
            except OSError:
                pass


def guard(
    state_root: Path,
    *,
    namespace: str,
    task_id: str,
    effect_id: str,
    idempotency_key: str,
    action_payload_hash: str,
    action_kind: str,
    target_ref: str,
    reserve: bool = True,
) -> dict[str, Any]:
    current = (
        state_root
        / "CURRENT"
        / "SIDE_EFFECTS"
        / _slug(namespace)
        / _slug(task_id)
        / f"{_slug(effect_id)}.json"
    )

    if not current.exists():
        history_dir = _history_dir(
            state_root,
            namespace=namespace,
            task_id=task_id,
            effect_id=effect_id,
        )
        if history_dir.exists() and any(history_dir.glob("*.json")):
            return {
                "pass": False,
                "detected": ["SIDE_EFFECT_CURRENT_MISSING_HISTORY_PRESENT"],
                "decision": "RECOVER_BEFORE_EXECUTION",
                "current_path": str(current),
                "history_dir": str(history_dir),
                "ledger_record": None,
            }
        return _allow_with_claim(
            state_root,
            namespace=namespace,
            task_id=task_id,
            effect_id=effect_id,
            claim_key=_stable_effect_claim_key(
                namespace=namespace,
                task_id=task_id,
                effect_id=effect_id,
                idempotency_key=idempotency_key,
                action_payload_hash=action_payload_hash,
                action_kind=action_kind,
                target_ref=target_ref,
                attempt_scope="INITIAL",
            ),
            decision="ALLOW_FIRST_EXECUTION",
            current_path=current,
            ledger_record=None,
            reserve=reserve,
        )

    try:
        record = json.loads(current.read_text(encoding="utf-8"))
    except Exception:
        return {
            "pass": False,
            "detected": ["SIDE_EFFECT_CURRENT_UNREADABLE"],
            "decision": "BLOCK",
            "current_path": str(current),
        }

    failures = _validate_existing_integrity(record)
    if record.get("namespace") != namespace:
        failures.append("SIDE_EFFECT_NAMESPACE_MISMATCH")
    if record.get("task_id") != task_id:
        failures.append("SIDE_EFFECT_TASK_ID_MISMATCH")
    if record.get("effect_id") != effect_id:
        failures.append("SIDE_EFFECT_EFFECT_ID_MISMATCH")
    if record.get("idempotency_key") != idempotency_key:
        failures.append("SIDE_EFFECT_IDEMPOTENCY_KEY_MISMATCH")
    if record.get("action_payload_hash") != action_payload_hash:
        failures.append("SIDE_EFFECT_ACTION_PAYLOAD_HASH_MISMATCH")
    if record.get("action_kind") != action_kind:
        failures.append("SIDE_EFFECT_ACTION_KIND_MISMATCH")
    if record.get("target_ref") != target_ref:
        failures.append("SIDE_EFFECT_TARGET_REF_MISMATCH")

    failures.extend(_validate_history_consistency(state_root, record))

    compensation_identity = None
    if record.get("execution_status") == "COMPENSATED" or record.get("compensation_ref"):
        compensation_identity, evidence_failures = _compensation_identity(record, state_root)
        failures.extend(evidence_failures)

    if failures:
        return {
            "pass": False,
            "detected": list(dict.fromkeys(failures)),
            "decision": "BLOCK",
            "current_path": str(current),
            "ledger_record": record,
        }

    status = record["execution_status"]
    policy = record["replay_policy"]

    if status == "PLANNED":
        return _allow_with_claim(
            state_root,
            namespace=namespace,
            task_id=task_id,
            effect_id=effect_id,
            claim_key=_stable_effect_claim_key(
                namespace=namespace,
                task_id=task_id,
                effect_id=effect_id,
                idempotency_key=idempotency_key,
                action_payload_hash=action_payload_hash,
                action_kind=action_kind,
                target_ref=target_ref,
                attempt_scope=compensation_identity or "INITIAL",
            ),
            decision="ALLOW_INITIAL_EXECUTION",
            current_path=current,
            ledger_record=record,
            reserve=reserve,
        )

    if status == "APPLYING":
        return {
            "pass": False,
            "detected": ["SIDE_EFFECT_EXECUTION_INDETERMINATE"],
            "decision": "VERIFY_BEFORE_RETRY",
            "current_path": str(current),
            "ledger_record": record,
        }

    if status in {"APPLIED", "VERIFIED"}:
        if policy == "IDEMPOTENT_RETRY":
            return _allow_with_claim(
                state_root,
                namespace=namespace,
                task_id=task_id,
                effect_id=effect_id,
                claim_key=str(record.get("record_hash")),
                decision="ALLOW_IDEMPOTENT_RETRY",
                current_path=current,
                ledger_record=record,
                reserve=reserve,
            )
        if policy == "VERIFY_THEN_RETRY":
            return {
                "pass": False,
                "detected": ["SIDE_EFFECT_VERIFICATION_REQUIRED_BEFORE_RETRY"],
                "decision": "VERIFY_BEFORE_RETRY",
                "current_path": str(current),
                "ledger_record": record,
            }
        if policy == "COMPENSATE":
            return {
                "pass": False,
                "detected": ["SIDE_EFFECT_COMPENSATION_REQUIRED_BEFORE_RETRY"],
                "decision": "COMPENSATE_BEFORE_RETRY",
                "current_path": str(current),
                "ledger_record": record,
            }
        return {
            "pass": False,
            "detected": ["SIDE_EFFECT_DUPLICATE_EXECUTION_FORBIDDEN"],
            "decision": "BLOCK_DUPLICATE",
            "current_path": str(current),
            "ledger_record": record,
        }

    if status == "FAILED":
        if policy == "IDEMPOTENT_RETRY":
            return _allow_with_claim(
                state_root,
                namespace=namespace,
                task_id=task_id,
                effect_id=effect_id,
                claim_key=str(record.get("record_hash")),
                decision="ALLOW_IDEMPOTENT_RETRY",
                current_path=current,
                ledger_record=record,
                reserve=reserve,
            )
        return {
            "pass": False,
            "detected": ["SIDE_EFFECT_FAILED_RETRY_POLICY_BLOCK"],
            "decision": "BLOCK",
            "current_path": str(current),
            "ledger_record": record,
        }

    if status == "COMPENSATED":
        return _allow_with_claim(
            state_root,
            namespace=namespace,
            task_id=task_id,
            effect_id=effect_id,
            claim_key=_stable_effect_claim_key(
                namespace=namespace,
                task_id=task_id,
                effect_id=effect_id,
                idempotency_key=idempotency_key,
                action_payload_hash=action_payload_hash,
                action_kind=action_kind,
                target_ref=target_ref,
                attempt_scope=compensation_identity,
            ),
            decision="ALLOW_NEW_ATTEMPT_AFTER_COMPENSATION",
            current_path=current,
            ledger_record=record,
            reserve=reserve,
        )

    return {
        "pass": False,
        "detected": ["SIDE_EFFECT_STATE_UNHANDLED"],
        "decision": "BLOCK",
        "current_path": str(current),
        "ledger_record": record,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write")
    write.add_argument("--record", type=Path, required=True)
    write.add_argument("--state-root", type=Path, default=Path.cwd())
    write.add_argument("--no-history", action="store_true")

    check = sub.add_parser("guard")
    check.add_argument("--state-root", type=Path, default=Path.cwd())
    check.add_argument("--namespace", required=True)
    check.add_argument("--task-id", required=True)
    check.add_argument("--effect-id", required=True)
    check.add_argument("--idempotency-key", required=True)
    check.add_argument("--action-payload-hash", required=True)
    check.add_argument("--action-kind", required=True)
    check.add_argument("--target-ref", required=True)

    args = ap.parse_args()
    if args.command == "write":
        try:
            record = json.loads(args.record.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            result = {"pass": False, "detected": [f"SIDE_EFFECT_RECORD_UNREADABLE:{type(exc).__name__}"]}
        else:
            result = persist(record, args.state_root, append_history=not args.no_history)
    else:
        result = guard(
            args.state_root,
            namespace=args.namespace,
            task_id=args.task_id,
            effect_id=args.effect_id,
            idempotency_key=args.idempotency_key,
            action_payload_hash=args.action_payload_hash,
            action_kind=args.action_kind,
            target_ref=args.target_ref,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
