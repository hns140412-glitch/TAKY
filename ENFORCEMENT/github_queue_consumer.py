#!/usr/bin/env python3
"""TAKY GitHub Issue queue consumer.

Consumes GitHub issues/issue_comment event payloads. It never executes comment
content. It validates the immutable dispatch envelope, receipt/result bindings,
and returns a small action plan for the workflow to publish back to the issue.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from executor_transport import sha256_json, validate_receipt
from executor_cycle import run as run_executor_cycle
from github_issue_executor_queue import parse_issue, parse_comment

QUEUE_PREFIX = "[TAKY EXECUTOR QUEUE]"
CANCELLATION_AUTHOR_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}

def validate_envelope(envelope: dict) -> list[str]:
    failures: list[str] = []
    task = envelope.get("task_contract")
    if not isinstance(task, dict):
        return ["DISPATCH_TASK_CONTRACT_MISSING"]
    if envelope.get("task_id") != task.get("task_id"):
        failures.append("DISPATCH_TASK_ID_MISMATCH")
    expected = str(envelope.get("task_contract_sha256", "")).strip()
    actual = sha256_json(task)
    if expected != actual:
        failures.append("DISPATCH_ENVELOPE_TAMPERED")
    if str(envelope.get("transport", "")).upper() != "GITHUB_ISSUE_QUEUE":
        failures.append("DISPATCH_TRANSPORT_NOT_GITHUB_QUEUE")
    if str(envelope.get("provider", "")).upper() != "CODEX":
        failures.append("DISPATCH_PROVIDER_UNSUPPORTED")
    return failures

def validate_cancellation(envelope: dict, issue: dict, comment: dict, cancellation: dict) -> list[str]:
    failures: list[str] = []
    if cancellation.get("task_id") != envelope.get("task_id"):
        failures.append("CANCELLATION_TASK_ID_MISMATCH")
    if cancellation.get("task_contract_sha256") != envelope.get("task_contract_sha256"):
        failures.append("CANCELLATION_CONTRACT_HASH_MISMATCH")
    if str(cancellation.get("decision", "")).strip().upper() != "CANCEL":
        failures.append("CANCELLATION_DECISION_INVALID")
    for key in ("cancellation_id", "authority_ref", "reason"):
        value = cancellation.get(key)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"CANCELLATION_{key.upper()}_MISSING")

    issue_number = issue.get("number")
    if cancellation.get("queue_issue_number") != issue_number:
        failures.append("CANCELLATION_QUEUE_ISSUE_MISMATCH")

    user = comment.get("user") or comment.get("author") or {}
    actor_login = user.get("login") if isinstance(user, dict) else None
    association = str(
        comment.get("author_association")
        or comment.get("authorAssociation")
        or ""
    ).strip().upper()
    if not actor_login or cancellation.get("authority_ref") != actor_login:
        failures.append("CANCELLATION_AUTHORITY_ACTOR_MISMATCH")
    if association not in CANCELLATION_AUTHOR_ASSOCIATIONS:
        failures.append("CANCELLATION_AUTHORITY_NOT_REPOSITORY_TRUSTED")
    return failures


def _comment(kind: str, data: dict, source_comment_id=None, issue_ack: bool=False) -> str:
    markers = [f"<!-- TAKY_QUEUE_CONSUMER:{kind} -->"]
    if issue_ack:
        markers.append("<!-- TAKY_QUEUE_ISSUE_ACK -->")
    if source_comment_id is not None:
        markers.append(f"<!-- TAKY_QUEUE_SOURCE_COMMENT:{source_comment_id} -->")
    return (
        "\n".join(markers)
        + "\n"
        + f"**TAKY Queue Consumer — {kind}**\n\n"
        + "```json\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n```\n"
    )

def consume(event: dict) -> dict:
    issue = event.get("issue") or {}
    title = str(issue.get("title", ""))
    if not title.startswith(QUEUE_PREFIX):
        return {"pass": True, "action": "IGNORE_NON_QUEUE", "comment": None}

    parsed_issue = parse_issue(str(issue.get("body", "")))
    if not parsed_issue.get("pass"):
        data = {"detected": parsed_issue.get("detected", [])}
        return {"pass": False, "action": "REJECT_QUEUE", "comment": _comment("REJECTED", data, issue_ack=True)}

    envelope = parsed_issue["envelope"]
    failures = validate_envelope(envelope)
    if failures:
        return {
            "pass": False,
            "action": "REJECT_QUEUE",
            "comment": _comment("REJECTED", {"task_id": envelope.get("task_id"), "detected": failures}, issue_ack=True),
        }

    event_name = str(event.get("_event_name") or "")
    if event_name == "issues":
        data = {
            "task_id": envelope.get("task_id"),
            "provider": envelope.get("provider"),
            "contract_sha256": envelope.get("task_contract_sha256"),
            "status": "WAITING_EXECUTOR_RECEIPT",
            "external_executor_invocation_verified": False,
        }
        return {"pass": True, "action": "QUEUE_READY", "comment": _comment("QUEUE_READY", data, issue_ack=True)}

    comment = event.get("comment") or {}
    source_comment_id = comment.get("id")
    parsed = parse_comment(str(comment.get("body", "")))
    if not parsed.get("pass"):
        return {"pass": True, "action": "IGNORE_NON_MACHINE_COMMENT", "comment": None}

    receipt = parsed.get("receipt")
    result = parsed.get("result")
    cancellation = parsed.get("cancellation")

    if cancellation is not None:
        failures = validate_cancellation(envelope, issue, comment, cancellation)
        kind = "TASK_CANCELLED" if not failures else "CANCELLATION_REJECTED"
        data = {
            "task_id": envelope.get("task_id"),
            "cancellation_id": cancellation.get("cancellation_id"),
            "authority_ref": cancellation.get("authority_ref"),
            "reason": cancellation.get("reason"),
            "detected": failures,
        }
        return {
            "pass": not failures,
            "action": kind,
            "comment": _comment(kind, data, source_comment_id=source_comment_id),
            "close_issue": not failures,
        }

    if receipt is not None:
        checked = validate_receipt(envelope, receipt)
        kind = "RECEIPT_ACCEPTED" if checked["pass"] else "RECEIPT_REJECTED"
        data = {
            "task_id": envelope.get("task_id"),
            "executor_run_id": receipt.get("executor_run_id"),
            "status": receipt.get("status"),
            "detected": checked.get("detected", []),
        }
        return {
            "pass": bool(checked["pass"]),
            "action": kind,
            "comment": _comment(kind, data, source_comment_id=source_comment_id),
        }

    if result is not None:
        cycle = run_executor_cycle(envelope, result)
        decision = ((cycle.get("review") or {}).get("review_decision"))
        kind = "RESULT_TO_HUMAN_APPROVAL" if decision == "HUMAN_APPROVAL" else (
            "RESULT_TO_REWORK" if decision == "REWORK" else "RESULT_REJECTED"
        )
        data = {
            "task_id": envelope.get("task_id"),
            "review_decision": decision,
            "next_action": cycle.get("next_action"),
            "detected": cycle.get("detected", []),
            "transition": cycle.get("transition"),
        }
        return {
            "pass": kind != "RESULT_REJECTED",
            "action": kind,
            "comment": _comment(kind, data, source_comment_id=source_comment_id),
        }

    return {"pass": True, "action": "IGNORE_EMPTY_MACHINE_COMMENT", "comment": None}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", type=Path, required=True)
    ap.add_argument("--event-name", required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    event = json.loads(args.event.read_text(encoding="utf-8"))
    event["_event_name"] = args.event_name
    out = consume(event)
    if args.output:
        args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
