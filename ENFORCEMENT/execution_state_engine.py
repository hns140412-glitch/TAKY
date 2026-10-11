#!/usr/bin/env python3
"""TAKY execution state engine.

Owns task lifecycle transitions and rework routing for controlled repository runs.
It is intentionally small and deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# Legacy Codex-named states remain accepted for compatibility.
# Executor-neutral aliases allow Claude/Codex/other adapters to share one lifecycle.
STATE_ALIASES = {
    "ASSIGNED_TO_EXECUTOR": "ASSIGNED_TO_CODEX",
    "EXECUTOR_DONE": "CODEX_DONE",
}

ALLOWED_TRANSITIONS = {
    "READY": {"ASSIGNED_TO_CODEX"},
    "ASSIGNED_TO_CODEX": {"IN_PROGRESS"},
    "IN_PROGRESS": {"CODEX_DONE"},
    "CODEX_DONE": {"TAKY_REVIEW"},
    "TAKY_REVIEW": {"REWORK", "HUMAN_APPROVAL"},
    "REWORK": {"ASSIGNED_TO_CODEX", "IN_PROGRESS"},
    "HUMAN_APPROVAL": {"MERGED"},
    "MERGED": {"DEPLOYED"},
    "DEPLOYED": set(),
}
SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(value: str) -> str:
    out = SAFE.sub("_", value.strip()).strip("._")
    if not out:
        raise ValueError("unsafe or empty path component")
    return out


def _canonical_bytes(value: dict) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _payload_hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def approval_context(record: dict, current: str, requested: str) -> tuple[dict, list[str]]:
    failures: list[str] = []
    task_id = str(record.get("task_id", "")).strip()
    target_ref = str(record.get("transition_target_ref", "")).strip()
    action_payload = record.get("transition_action_payload")

    if not task_id:
        failures.append("APPROVAL_CONTEXT_TASK_ID_MISSING")
    if not target_ref:
        failures.append("APPROVAL_CONTEXT_TARGET_REF_MISSING")
    if not isinstance(action_payload, dict) or not action_payload:
        failures.append("APPROVAL_CONTEXT_ACTION_PAYLOAD_MISSING")
        action_payload_hash = None
    else:
        action_payload_hash = _payload_hash(action_payload)

    context = {
        "task_id": task_id,
        "from_state": current,
        "to_state": requested,
        "target_ref": target_ref,
        "action_kind": "STATE_TRANSITION",
        "action_payload_hash": action_payload_hash,
    }
    context["approval_context_hash"] = (
        "sha256:" + hashlib.sha256(_canonical_bytes(context)).hexdigest()
    )
    return context, failures


def _consume_transition_approval(
    state_root: Path,
    approval: dict,
) -> dict:
    task_id = str(approval.get("task_id", "")).strip()
    approval_id = str(approval.get("approval_id", "")).strip()
    context_hash = str(approval.get("approval_context_hash", "")).strip()
    if not task_id or not approval_id or not context_hash:
        return {
            "pass": False,
            "detected": ["TRANSITION_APPROVAL_CONSUMPTION_IDENTITY_INVALID"],
        }

    receipt_dir = (
        state_root
        / "HISTORY"
        / "TRANSITION_APPROVAL_CONSUMPTIONS"
        / _slug(task_id)
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_key = _payload_hash({
        "task_id": task_id,
        "approval_id": approval_id,
        "approval_context_hash": context_hash,
    }).split(":", 1)[1]
    receipt_path = receipt_dir / f"{receipt_key}.json"
    payload = {
        "task_id": task_id,
        "approval_id": approval_id,
        "approver_ref": approval.get("approver_ref"),
        "approval_context_hash": context_hash,
        "from_state": approval.get("from_state"),
        "to_state": approval.get("to_state"),
        "target_ref": approval.get("target_ref"),
        "action_payload_hash": approval.get("action_payload_hash"),
        "consumed_at": datetime.now(timezone.utc).isoformat(),
    }
    raw = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    try:
        fd = os.open(str(receipt_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return {
            "pass": False,
            "detected": ["TRANSITION_APPROVAL_ALREADY_CONSUMED"],
            "receipt_path": str(receipt_path),
        }
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            receipt_path.unlink()
        except OSError:
            pass
        raise
    return {
        "pass": True,
        "detected": [],
        "receipt_path": str(receipt_path),
        "receipt_hash": _payload_hash(payload),
    }


def validate_transition_approval(
    record: dict,
    current: str,
    requested: str,
) -> tuple[dict | None, dict, list[str]]:
    context, failures = approval_context(record, current, requested)
    evidence = record.get("human_approval_evidence")
    if not evidence:
        return None, context, failures
    if not isinstance(evidence, dict):
        failures.append("HUMAN_APPROVAL_EVIDENCE_INVALID")
        return None, context, failures

    approval_id = evidence.get("approval_id")
    approver_ref = evidence.get("approver_ref")
    decision = str(evidence.get("decision", "")).strip().upper()

    if not isinstance(approval_id, str) or not approval_id.strip():
        failures.append("APPROVAL_ID_MISSING")
    if not isinstance(approver_ref, str) or not approver_ref.strip():
        failures.append("APPROVER_REF_MISSING")
    if decision != "APPROVE":
        failures.append("APPROVAL_DECISION_NOT_APPROVED")

    if evidence.get("task_id") != context["task_id"]:
        failures.append("APPROVAL_EVIDENCE_TASK_ID_MISMATCH")
    if str(evidence.get("from_state", "")).strip().upper() != current:
        failures.append("APPROVAL_EVIDENCE_FROM_STATE_MISMATCH")
    if str(evidence.get("to_state", "")).strip().upper() != requested:
        failures.append("APPROVAL_EVIDENCE_TO_STATE_MISMATCH")
    if evidence.get("target_ref") != context["target_ref"]:
        failures.append("APPROVAL_EVIDENCE_TARGET_REF_MISMATCH")
    if evidence.get("action_kind") != context["action_kind"]:
        failures.append("APPROVAL_EVIDENCE_ACTION_KIND_MISMATCH")
    if evidence.get("action_payload_hash") != context["action_payload_hash"]:
        failures.append("APPROVAL_EVIDENCE_ACTION_PAYLOAD_HASH_MISMATCH")
    if evidence.get("approval_context_hash") != context["approval_context_hash"]:
        failures.append("APPROVAL_EVIDENCE_CONTEXT_HASH_MISMATCH")

    normalized = {
        "approval_id": approval_id.strip() if isinstance(approval_id, str) else None,
        "approver_ref": approver_ref.strip() if isinstance(approver_ref, str) else None,
        "decision": decision,
        "evidence_level": "BOUND_RECORD_ONLY",
        "identity_authenticated": False,
        **context,
    }
    return normalized, context, failures


def transition(record: dict, state_root: Path | None = None) -> dict:
    current_raw = str(record.get("current_state", "")).strip().upper()
    requested_raw = str(record.get("requested_state", "")).strip().upper()
    current = STATE_ALIASES.get(current_raw, current_raw)
    requested = STATE_ALIASES.get(requested_raw, requested_raw)
    if not current or not requested:
        return {"pass": False, "detected": ["STATE_TRANSITION_INCOMPLETE"]}

    if requested not in ALLOWED_TRANSITIONS.get(current, set()):
        return {
            "pass": False,
            "detected": [f"FORBIDDEN_STATE_TRANSITION:{current}->{requested}"],
            "current_state": current,
        }

    if requested == "REWORK":
        defects = record.get("defects")
        if not isinstance(defects, list) or not defects:
            return {
                "pass": False,
                "detected": ["REWORK_WITHOUT_DEFECT_EVIDENCE"],
                "current_state": current,
            }

    approval_verified = None
    approval_consumption = None
    # High-impact transition policy is trusted code, not caller-controlled input.
    # A task record may describe approval metadata but cannot disable the human gate.
    approval_required = requested in {"MERGED", "DEPLOYED"}
    if approval_required:
        missing_code = (
            "HUMAN_APPROVAL_MISSING:merge"
            if requested == "MERGED"
            else "HUMAN_APPROVAL_MISSING:production_deploy"
        )
        if not record.get("human_approval_evidence"):
            context, context_failures = approval_context(record, current, requested)
            return {
                "pass": False,
                "detected": [missing_code, *context_failures],
                "current_state": current,
                "required_approval_context": context,
            }

        approval_verified, context, approval_failures = validate_transition_approval(
            record,
            current,
            requested,
        )
        if approval_failures:
            return {
                "pass": False,
                "detected": approval_failures,
                "current_state": current,
                "required_approval_context": context,
            }
        if state_root is None:
            return {
                "pass": False,
                "detected": ["TRANSITION_STATE_ROOT_REQUIRED"],
                "current_state": current,
                "required_approval_context": context,
            }
        approval_consumption = _consume_transition_approval(
            state_root,
            approval_verified or {},
        )
        if not approval_consumption.get("pass"):
            return {
                "pass": False,
                "detected": list(approval_consumption.get("detected", [])),
                "current_state": current,
                "approval_verified": approval_verified,
                "approval_consumption": approval_consumption,
            }

    return {
        "pass": True,
        "detected": [],
        "previous_state": current,
        "current_state": requested,
        "approval_verified": approval_verified,
        "approval_consumption": approval_consumption,
        "rework": {
            "required": requested == "REWORK",
            "defects": record.get("defects", []) if requested == "REWORK" else [],
            "acceptance_delta": record.get("acceptance_delta", []) if requested == "REWORK" else [],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    ap.add_argument("--state-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    data = json.loads(args.record.read_text(encoding="utf-8"))
    result = transition(data, args.state_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
