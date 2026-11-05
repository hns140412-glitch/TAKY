"""Reason Network one-shot intake into the existing TAKY bounded queue.

No polling loop, new agent runner, implicit startup, or user-supplied commands.
A local message only selects a TAKY-prepared manifest in .local/. The existing
runtime_orchestrator owns authorization, provider execution and evidence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from runtime_orchestrator import _trusted_steering_local_dir, run_bounded_goal_queue

MESSAGE_HEADER = re.compile(
    r'<reason-message from="([A-Za-z0-9_.-]{1,64}/[A-Za-z0-9_.-]{1,64})" '
    r'agent="([A-Za-z0-9_.-]{1,40})" id="([A-Z0-9]{20,40})">'
)
SIGNAL = re.compile(r"TAKY_GOAL_SIGNAL_V1 queue=([A-Za-z0-9_.-]{4,80})")
ALLOWED_AGENTS = {"cli", "claude-code", "codex", "claude", "reason"}
SESSION = "taky-goal-inbox"
PERSON = "taky-local"


def parse_reason_message(output: str) -> dict | None:
    """Parse one exact framed, one-line control message; reject extra commands."""
    if not isinstance(output, str) or len(output) > 8192:
        return None
    lines = output.splitlines()
    if len(lines) < 3:
        return None
    found = MESSAGE_HEADER.fullmatch(lines[0])
    if not found or found.group(2) not in ALLOWED_AGENTS:
        return None
    if not found.group(1).startswith(PERSON + "/"):
        return None
    try:
        close = lines.index("</reason-message>", 1)
    except ValueError:
        return None
    if close != 2 or lines.count("</reason-message>") != 1:
        return None
    match = SIGNAL.fullmatch(lines[1])
    if not match:
        return None
    return {"sender": found.group(1), "agent": found.group(2),
            "message_id": found.group(3), "queue_id": match.group(1)}


def reason_binary() -> Path:
    return (Path(os.environ.get("LOCALAPPDATA", ""))
            / "TAKY" / "reason_network_evaluation" / "bin"
            / "reason-network.exe")


def taky_only_transport_workdir() -> Path | None:
    """Reason runs only under its TAKY-owned local C: workspace.

    Never widen the ancestor D: folder-deny policy, or grant other
    repositories permission by enabling a drive or shared workspace.
    """
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    root = Path(local) / "TAKY" / "reason_network_evaluation"
    folder = root / "TAKY_ONLY_TRANSPORT"
    try:
        if (not folder.is_dir() or folder.is_symlink()
                or getattr(folder, "is_junction", lambda: False)()
                or folder.resolve().parent != root.resolve()
                or folder.resolve().drive.casefold() == Path(__file__).resolve().drive.casefold()):
            return None
        return folder.resolve()
    except (OSError, ValueError):
        return None


def verified_local_team(exe: Path, *, runner=subprocess.run) -> bool:
    """The network is private to this PC and TAKY's isolated transport folder."""
    workspace = taky_only_transport_workdir()
    if not exe.is_file() or workspace is None:
        return False
    try:
        result = runner([str(exe), "team", "--json"], capture_output=True,
                        text=True, stdin=subprocess.DEVNULL, timeout=5,
                        cwd=workspace,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0:
            return False
        info = json.loads(result.stdout)
        members = info.get("members")
        return (
            info.get("person") == PERSON
            and info.get("team_name") == "TAKY-LOCAL-PRIVATE"
            and isinstance(members, list) and len(members) == 1
            and isinstance(members[0], dict)
            and members[0].get("person") == PERSON
            and members[0].get("machine") == info.get("machine")
        )
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return False


def _recorded_reason_result(local: Path, message: dict,
                            manifest_hash: str) -> dict | None:
    """Recover a previously persisted *observation*, never model DONE."""
    import hashlib
    result_path = local / ("taky-reason-result-" + message["message_id"] + ".json")
    if result_path.is_symlink() or not result_path.is_file():
        return None
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
        if (data.get("schema") != "TAKY_REASON_RESULT_V1"
                or data.get("message_id") != message["message_id"]
                or data.get("queue_id") != message["queue_id"]
                or data.get("sender") != message["sender"]
                or data.get("manifest_sha256") != manifest_hash
                or not isinstance(data.get("queue"), dict)):
            return None
        return data
    except (OSError, ValueError, TypeError, UnicodeError):
        return None


def _dispatch_idempotent(local: Path, manifest: Path, message: dict,
                         queue_executor) -> dict:
    """Durable Reason intake claim precedes every potential model call.

    A concurrent or interrupted claim is reconciled using existing evidence.
    No automatic reexecution of an ambiguous attempt, and no extra gate owner.
    """
    import hashlib
    import secrets
    source_bytes = manifest.read_bytes()
    manifest_hash = hashlib.sha256(source_bytes).hexdigest()
    # A stable same-byte snapshot is validated again before any provider
    # invocation. The mutable intake pathname is never passed to the worker.
    snapshot = local / ("taky-intake-snapshot-" + message["message_id"] + ".json")
    if snapshot.is_symlink():
        return {"status": "REASON_MANIFEST_SNAPSHOT_UNTRUSTED",
                "dispatched": False}
    try:
        with snapshot.open("xb") as stream:
            stream.write(source_bytes)
    except FileExistsError:
        if snapshot.read_bytes() != source_bytes:
            return {"status": "REASON_MANIFEST_CHANGED_RECONCILE",
                    "dispatched": False}
    if (run_bounded_goal_queue(snapshot, local.parent, validate_only=True)
            .get("status") != "QUEUE_INPUT_VERIFIED_NOT_DISPATCHED"):
        return {"status": "REASON_MANIFEST_SNAPSHOT_INVALID",
                "dispatched": False}
    claim = local / ("taky-reason-claim-" + message["message_id"] + ".json")
    result_path = local / ("taky-reason-result-" + message["message_id"] + ".json")
    header = {
        "schema": "TAKY_REASON_CLAIM_V1",
        "message_id": message["message_id"],
        "queue_id": message["queue_id"],
        "sender": message["sender"],
        "manifest_sha256": manifest_hash,
    }
    first = False
    try:
        with claim.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps({**header, "state": "OUTCOME_UNKNOWN"},
                                    ensure_ascii=False) + "\n")
        first = True
    except FileExistsError:
        try:
            previous = json.loads(claim.read_text(encoding="utf-8"))
            if (claim.is_symlink() or any(previous.get(k) != v
                    for k,v in header.items())):
                return {"status": "REASON_CLAIM_BINDING_MISMATCH",
                        "dispatched": False}
        except (OSError, ValueError, TypeError):
            return {"status": "REASON_CLAIM_UNTRUSTED", "dispatched": False}
    except OSError:
        return {"status": "REASON_CLAIM_PERSIST_FAILED", "dispatched": False}
    if not first:
        recovered = _recorded_reason_result(local, message, manifest_hash)
        if recovered:
            return {"status": "REASON_PRIOR_RESULT_REUSED",
                    "dispatched": False, "recovered": True,
                    "queue": recovered["queue"],
                    "local_result_receipt": str(result_path.relative_to(local.parent))}
        return {"status": "REASON_OUTCOME_UNKNOWN_RECONCILE",
                "dispatched": False,
                "next_safe_action": "CHECK_EXISTING_CLAIM_AND_RUNTIME_NO_BLIND_RETRY"}

    try:
        queue = queue_executor(snapshot, local.parent)
        if not isinstance(queue, dict):
            return {"status": "REASON_RESULT_UNVERIFIED",
                    "dispatched": True}
        result = {"schema": "TAKY_REASON_RESULT_V1", **{
            k: header[k] for k in ("message_id","queue_id","sender",
                                   "manifest_sha256")},
                  "queue": queue}
        with result_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        replacement = claim.with_name(claim.name + "." + secrets.token_hex(6) + ".tmp")
        try:
            with replacement.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps({**header, "state": "RECORDED"},
                                        ensure_ascii=False) + "\n")
            os.replace(replacement, claim)
        finally:
            replacement.unlink(missing_ok=True)
        return {"status": "REASON_PREPARED_QUEUE_DISPATCHED",
                "dispatched": True, "queue": queue,
                "local_result_receipt": str(result_path.relative_to(local.parent))}
    except Exception as error:
        return {"status": "REASON_OUTCOME_UNKNOWN_RECONCILE",
                "error_class":type(error).__name__,
                "dispatched": True,
                "next_safe_action": "INSPECT_LOCAL_QUEUE_RECEIPT_NO_BLIND_RETRY"}


def route_message(repo_root: Path, raw: str, *, execute: bool = False,
                  identity_check=None, queue_executor=None) -> dict:
    """Route an authenticated local signal, never freeform remote instructions."""
    message = parse_reason_message(raw)
    if message is None:
        return {"status": "REASON_SIGNAL_UNTRUSTED", "dispatched": False}
    verified = identity_check or (lambda: verified_local_team(reason_binary()))
    if not verified():
        return {"status": "REASON_IDENTITY_UNVERIFIED", "dispatched": False}
    repo = repo_root.resolve()
    local = _trusted_steering_local_dir(repo)
    if local is None:
        return {"status": "REASON_LOCAL_VAULT_UNTRUSTED", "dispatched": False}
    manifest = local / ("taky-intake-" + message["queue_id"] + ".json")
    try:
        if manifest.is_symlink():
            return {"status": "REASON_PREPARED_MANIFEST_INVALID",
                    "queue_id": message["queue_id"], "dispatched": False}
        if not manifest.is_file():
            from taky_prepared_goal import resolve_prepared_goal
            return {"queue_id": message["queue_id"],
                    **resolve_prepared_goal(repo, local, message["queue_id"],
                                            message["message_id"])}
        if (manifest.resolve().parent != local
                or manifest.stat().st_size > 65536):
            return {"status": "REASON_PREPARED_MANIFEST_INVALID",
                    "queue_id": message["queue_id"], "dispatched": False}
        prepared = json.loads(manifest.read_text(encoding="utf-8"))
        if (not isinstance(prepared, dict)
                or prepared.get("schema") not in {
                    "TAKY_GOAL_QUEUE_V1", "TAKY_GOAL_QUEUE_V2"
                }
                or prepared.get("queue_id") != message["queue_id"]):
            return {"status": "REASON_PREPARED_MANIFEST_INVALID",
                    "queue_id": message["queue_id"], "dispatched": False}
    except (OSError, ValueError, UnicodeError):
        return {"status": "REASON_PREPARED_MANIFEST_INVALID",
                "queue_id": message["queue_id"], "dispatched": False}
    verified_queue = run_bounded_goal_queue(manifest, repo, validate_only=True)
    if verified_queue.get("status") != "QUEUE_INPUT_VERIFIED_NOT_DISPATCHED":
        return {"status": "REASON_PREPARED_MANIFEST_INVALID",
                "queue_id": message["queue_id"],
                "validation_state": verified_queue.get("status"),
                "dispatched": False}
    summary = {"schema": "TAKY_REASON_GOAL_INTAKE_V1",
               "status": "REASON_PREPARED_QUEUE_READY",
               "queue_id": message["queue_id"],
               "message_id": message["message_id"],
               "sender": message["sender"],
               "dispatched": False}
    if not execute:
        return summary
    run = queue_executor or run_bounded_goal_queue
    disposition = _dispatch_idempotent(local, manifest, message, run)
    return {**summary, **disposition}


def receive_once(repo_root: Path, *, wait_seconds: int = 1,
                 execute: bool = False, runner=subprocess.run,
                 identity_check=None, queue_executor=None) -> dict:
    """Bounded wait (1..30 s) and exactly one message; never an idle loop."""
    if type(wait_seconds) is not int or not 1 <= wait_seconds <= 30:
        return {"status": "REASON_WAIT_INVALID", "dispatched": False}
    exe = reason_binary()
    workspace = taky_only_transport_workdir()
    if workspace is None:
        return {"status": "REASON_TAKY_ONLY_SCOPE_UNAVAILABLE",
                "dispatched": False}
    trusted = (verified_local_team(exe, runner=runner)
               if identity_check is None else identity_check())
    if not trusted:
        return {"status": "REASON_IDENTITY_UNVERIFIED", "dispatched": False}
    if not exe.is_file():
        return {"status": "REASON_BINARY_MISSING", "dispatched": False}
    try:
        result = runner(
            [str(exe), "listen", "--as", SESSION, "--wait", str(wait_seconds)],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=wait_seconds + 5, cwd=workspace,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return {"status": "REASON_LISTEN_UNAVAILABLE", "dispatched": False}
    if result.returncode != 0:
        return {"status": "REASON_LISTEN_UNAVAILABLE",
                "reason_exit_code": result.returncode,
                "reason_stderr_preview": (getattr(result, "stderr", "") or "")[:220],
                "dispatched": False}
    if (not result.stdout.strip()
            or result.stdout.strip().startswith("No messages in ")):
        return {"status": "REASON_NO_MESSAGE", "dispatched": False}
    return route_message(repo_root, result.stdout, execute=execute,
                         identity_check=lambda: True,
                         queue_executor=queue_executor)


def drain_ready_messages(repo_root: Path, *, max_messages: int = 4,
                         execute: bool = False, intake=None) -> dict:
    """A bounded, nonresident burst: stop on idle, never busy-wait.

    No owner is added: receive_once validates local team and each message,
    while run_bounded_goal_queue remains the sole work executor.
    """
    if type(max_messages) is not int or not 1 <= max_messages <= 8:
        return {"status": "REASON_BURST_INVALID_LIMIT", "messages_observed": 0}
    receive = intake or receive_once
    observations = []
    transport_failure_code = None
    transport_exit_code = None
    transport_error_detail = None
    terminal_status = "REASON_BURST_LIMIT_REACHED"
    for _ in range(max_messages):
        try:
            outcome = receive(repo_root, wait_seconds=1, execute=execute)
        except Exception:
            terminal_status = "REASON_BURST_RECEIVER_UNAVAILABLE"
            break
        if not isinstance(outcome, dict):
            terminal_status = "REASON_BURST_RECEIVER_UNAVAILABLE"
            break
        status = outcome.get("status")
        if status == "REASON_NO_MESSAGE":
            terminal_status = "REASON_BURST_DRAINED_NO_MORE_MESSAGES"
            break
        if status in {"REASON_IDENTITY_UNVERIFIED", "REASON_BINARY_MISSING",
                      "REASON_LISTEN_UNAVAILABLE", "REASON_WAIT_INVALID",
                      "REASON_TAKY_ONLY_SCOPE_UNAVAILABLE"}:
            terminal_status = "REASON_BURST_TRANSPORT_UNAVAILABLE"
            transport_failure_code = status
            transport_exit_code = outcome.get("reason_exit_code")
            transport_error_detail = outcome.get("reason_stderr_preview")
            break
        observations.append({
            "status": status,
            "queue_id": outcome.get("queue_id"),
            "message_id": outcome.get("message_id"),
            "dispatched": outcome.get("dispatched") is True,
            "recovered": outcome.get("recovered") is True,
            "next_safe_action": outcome.get("next_safe_action"),
            "queue_status": (
                outcome["queue"].get("status")
                if isinstance(outcome.get("queue"), dict) else None
            ),
        })
    return {"schema": "TAKY_REASON_BURST_OBSERVATION_V1",
            "status": terminal_status,
            "messages_observed": len(observations),
            "messages_dispatched": sum(1 for item in observations
                                       if item["dispatched"]),
            "messages_recovered": sum(1 for item in observations
                                      if item["recovered"]),
            "observations": observations,
            "transport_failure_code": transport_failure_code,
            "transport_exit_code": transport_exit_code,
            "transport_error_detail": transport_error_detail,
            "resident_service": False, "goals_verified_done": 0}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="One-shot TAKY/Reason goal intake")
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--wait-seconds", type=int, default=1)
    ap.add_argument("--drain", action="store_true",
                    help="Drain at most eight queued local Reason messages; stop on idle")
    ap.add_argument("--max-messages", type=int, default=4)
    ap.add_argument("--execute", action="store_true",
                    help="Run only TAKY-prepared local manifests through existing gates")
    args = ap.parse_args(argv)
    if args.drain:
        if args.wait_seconds != 1:
            ap.error("--drain uses a fixed one-second idle stop")
        out = drain_ready_messages(args.repo_root,
                                   max_messages=args.max_messages,
                                   execute=args.execute)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out.get("status") in {
            "REASON_BURST_DRAINED_NO_MORE_MESSAGES",
            "REASON_BURST_LIMIT_REACHED",
        } else 2
    out = receive_once(args.repo_root, wait_seconds=args.wait_seconds,
                       execute=args.execute)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("status") in {
        "REASON_PREPARED_QUEUE_READY", "REASON_PREPARED_QUEUE_DISPATCHED",
        "REASON_PRIOR_RESULT_REUSED",
        "REASON_GOAL_ROUTED_TO_CANONICAL_WORK", "REASON_GOAL_PLAN_REUSED",
        "REASON_NO_MESSAGE",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
