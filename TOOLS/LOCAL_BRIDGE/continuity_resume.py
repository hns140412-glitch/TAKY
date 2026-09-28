#!/usr/bin/env python3
"""Read-only TAKY continuity resume evidence pack. No chat interception or canonical write.

Uses existing EXECUTION_CHECKPOINT_PROTOCOL record/hash contract as a *reader*.
This is a snapshot/pointer projection, never a second CURRENT or a Handoff PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HEX = re.compile(r"^[0-9a-f]{40,64}$")
REQUIRED = ("checkpoint_version", "task_id", "namespace", "atomic_unit", "status",
            "done", "open", "next", "corrections", "source_refs", "updated_at")
LISTS = ("done", "open", "corrections", "source_refs")


def canonical_bytes(record):
    return (json.dumps(record, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def within(root, rel):
    """Refuse absolute/traversal/symlink escapes, including report source pointers."""
    rel_path = Path(rel)
    if rel_path.is_absolute() or any(p in ("..", "") for p in rel_path.parts):
        raise ValueError("UNSAFE_RELATIVE_PATH")
    base = root.resolve()
    path = (base / rel_path).resolve()
    if not path.is_relative_to(base) or path == base:
        raise ValueError("SOURCE_OUTSIDE_ROOT")
    return path


def verify_checkpoint(root, namespace, task_id):
    path = within(root, f"CURRENT/{namespace}/{task_id}.json")
    finding = {"namespace": namespace, "task_id": task_id, "path": str(path),
               "status": "BLOCKED", "issues": [], "source_hash": None,
               "checkpoint_hash": None, "snapshot": None}
    if not path.is_file():
        finding["issues"].append("CURRENT_CHECKPOINT_MISSING")
        return finding
    raw = path.read_bytes()
    finding["source_hash"] = sha256(raw)
    try:
        record = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(record, dict):
            raise ValueError("not an object")
    except (ValueError, UnicodeError) as exc:
        finding["issues"].append("CURRENT_CHECKPOINT_UNREADABLE")
        return finding
    for key in REQUIRED:
        if key not in record:
            finding["issues"].append("MISSING_" + key.upper())
    if record.get("checkpoint_version") != "1.0":
        finding["issues"].append("CHECKPOINT_VERSION_UNSUPPORTED")
    if record.get("namespace") != namespace or record.get("task_id") != task_id:
        finding["issues"].append("CHECKPOINT_IDENTITY_MISMATCH")
    if record.get("status") not in ("RUNNING", "BLOCKED", "COMPLETE"):
        finding["issues"].append("INVALID_STATUS")
    for key in LISTS:
        if not isinstance(record.get(key), list) or any(
            not isinstance(x, str) for x in record.get(key, []) if isinstance(record.get(key), list)
        ):
            finding["issues"].append("INVALID_" + key.upper())
    if not isinstance(record.get("next"), (str, type(None))):
        finding["issues"].append("INVALID_NEXT")
    try:
        datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, ValueError):
        finding["issues"].append("INVALID_UPDATED_AT")
    if not isinstance(record.get("atomic_unit"), str) or not record.get("atomic_unit", "").strip():
        finding["issues"].append("INVALID_ATOMIC_UNIT")
    unhashed = dict(record)
    stored = unhashed.pop("checkpoint_hash", None)
    expected = sha256(canonical_bytes(unhashed))
    finding["checkpoint_hash"] = stored
    if stored != expected:
        finding["issues"].append("CURRENT_CHECKPOINT_INTEGRITY_MISMATCH")
    if finding["issues"]:
        return finding
    finding["status"] = "LOCAL_INTEGRITY_VERIFIED"
    finding["snapshot"] = {
        key: record.get(key) for key in
        ("atomic_unit", "status", "done", "open", "next", "corrections",
         "source_refs", "updated_at", "parent_checkpoint")
    }
    return finding


def git_snapshot(repo, *, network=False):
    result = {"local_head": None, "branch": None, "dirty": None,
              "server_main_head": None, "live_freshness": "NOT_CHECKED",
              "issues": []}
    if repo is None:
        result["issues"].append("REPO_NOT_CONFIGURED")
        return result
    def run(args):
        call = subprocess.run(["git", "-C", str(repo)] + args,
                              capture_output=True, text=True, timeout=20, check=False)
        if call.returncode:
            raise RuntimeError("GIT_COMMAND_FAILED")
        return call.stdout.strip()
    try:
        result["local_head"] = run(["rev-parse", "HEAD"])
        result["branch"] = run(["branch", "--show-current"]) or "DETACHED"
        result["dirty"] = bool(run(["status", "--porcelain"]))
        if network:
            # Query only, never fetch/update local refs or worktrees.
            call = subprocess.run(["git", "-C", str(repo), "-c", "credential.interactive=never",
                                   "ls-remote", "--heads", "origin", "main"],
                                  capture_output=True, text=True, timeout=25, check=False)
            if call.returncode:
                result["live_freshness"] = "UNKNOWN"
                result["issues"].append("REMOTE_MAIN_UNAVAILABLE")
            else:
                columns = call.stdout.strip().split()
                if len(columns) == 2 and HEX.fullmatch(columns[0]) and columns[1] == "refs/heads/main":
                    result["server_main_head"] = columns[0]
                    result["live_freshness"] = "LOCAL_MATCHES_SERVER_MAIN" if columns[0] == result["local_head"] else "LOCAL_DIFFERS_FROM_SERVER_MAIN"
                else:
                    result["live_freshness"] = "UNKNOWN"
                    result["issues"].append("REMOTE_MAIN_UNRESOLVED")
    except (OSError, subprocess.TimeoutExpired, RuntimeError):
        result["issues"].append("LOCAL_GIT_UNAVAILABLE")
    return result


def generate(config, output, *, include_context=False, network=False):
    state_root = Path(config["state_root"]).expanduser().resolve()
    if not state_root.is_dir():
        raise ValueError("STATE_ROOT_UNAVAILABLE")
    tasks = config.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("EXPLICIT_TASK_SELECTION_REQUIRED")
    owners = config.get("owners", {})
    if not isinstance(owners, dict):
        raise ValueError("INVALID_OWNER_MAP")
    entries = []
    seen = set()
    for task in tasks:
        namespace, task_id = task["namespace"], task["task_id"]
        if not all(isinstance(s, str) and IDENT.fullmatch(s) for s in (namespace, task_id)):
            raise ValueError("INVALID_TASK_ID")
        if (namespace, task_id) in seen:
            raise ValueError("DUPLICATE_TASK")
        seen.add((namespace, task_id))
        entry = verify_checkpoint(state_root, namespace, task_id)
        owner = owners.get(namespace)
        if not isinstance(owner, dict):
            entry["issues"].append("OWNER_NOT_CONFIGURED")
            entry["owner"] = {"status": "UNKNOWN"}
        else:
            entry["owner"] = {"status": "CONFIGURED", "repo": owner.get("repo")}
            if not isinstance(owner.get("repo"), str) or not owner["repo"].strip():
                entry["issues"].append("OWNER_REPO_NOT_CONFIGURED")
                entry["owner"]["git"] = git_snapshot(None)
            else:
                entry["owner"]["git"] = git_snapshot(Path(owner["repo"]).expanduser(), network=network)
                entry["issues"].extend(entry["owner"]["git"]["issues"])
            owner_ref = owner.get("canonical_path")
            if not isinstance(owner_ref, str) or not owner_ref.strip():
                entry["issues"].append("CANONICAL_POINTER_MISSING")
            else:
                try:
                    canonical = within(Path(owner["repo"]).expanduser(), owner_ref)
                    entry["owner"]["canonical_path"] = str(canonical)
                    entry["owner"]["canonical_exists"] = canonical.is_file()
                    if not canonical.is_file():
                        entry["issues"].append("CANONICAL_SOURCE_UNAVAILABLE")
                    else:
                        entry["owner"]["canonical_sha256"] = sha256(canonical.read_bytes())
                except (ValueError, OSError):
                    entry["issues"].append("CANONICAL_POINTER_UNRECOVERABLE")
        # Explicit handoff only: never infer authority or "latest" from filename.
        handoff = task.get("handoff_relative_path")
        entry["handoff"] = {"status": "NOT_CONFIGURED"}
        if handoff:
            try:
                hp = within(state_root, handoff)
                entry["handoff"] = {"path": str(hp), "status": "SOURCE_AVAILABLE" if hp.is_file() else "SOURCE_UNAVAILABLE"}
                if hp.is_file():
                    entry["handoff"]["sha256"] = sha256(hp.read_bytes())
                else:
                    entry["issues"].append("HANDOFF_SOURCE_UNAVAILABLE")
            except (ValueError, OSError):
                entry["issues"].append("HANDOFF_POINTER_UNRECOVERABLE")
        if not include_context:
            entry["snapshot"] = None
            entry["context_export"] = "OPT_IN_REQUIRED"
        else:
            entry["context_export"] = "LOCAL_ONLY_REVIEW_BEFORE_SHARING"
        # A checkpoint may be valid locally while owner, live authority, or source coverage is unknown.
        entry["resume_gate"] = "REVIEW_REQUIRED" if not entry["issues"] else "BLOCKED"
        entries.append(entry)
    output = output.expanduser().resolve()
    if output == state_root or state_root in output.parents:
        raise ValueError("REPORT_MUST_BE_OUTSIDE_STATE_ROOT")
    if any(Path(o.get("repo", "")).expanduser().resolve() in output.parents for o in owners.values() if isinstance(o, dict) and o.get("repo")):
        raise ValueError("REPORT_MUST_BE_OUTSIDE_REPOSITORIES")
    output.mkdir(parents=True, exist_ok=False)
    payload = {"schema": "TAKY_CONTINUITY_READ_ONLY_V1", "generated_at": datetime.now(timezone.utc).isoformat(),
               "state_root": str(state_root), "scope": "EXPLICIT_TASKS_ONLY",
               "authority": "EVIDENCE_ONLY_NOT_CANONICAL", "automatic_chat_capture": False,
               "live_remote_requested": network, "content_export_requested": include_context,
               "overall": "REVIEW_REQUIRED" if all(not e["issues"] for e in entries) else "BLOCKED",
               "entries": entries}
    (output / "RESUME_EVIDENCE.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# TAKY targeted continuation evidence", "",
             "Not canonical. Not a lossless Handoff PASS. Verify owner/CURRENT/live HEAD and source recoverability before resume.",
             "No automatic ChatGPT capture or upload. All data stays local until explicitly shared.", ""]
    for e in entries:
        lines += [f"## {e['namespace']} / {e['task_id']}", f"- Gate: {e['resume_gate']}",
                  f"- Current integrity: {e['status']}", f"- Checkpoint: {e['checkpoint_hash']}",
                  f"- Local owner: {e['owner'].get('canonical_path', 'UNKNOWN')}",
                  f"- Git live freshness: {e['owner'].get('git', {}).get('live_freshness', 'UNKNOWN')}",
                  f"- Handoff: {e['handoff']['status']}",
                  f"- OPEN: {len(e['snapshot']['open']) if e['snapshot'] else 'NOT_EXPORTED'}",
                  "- Issues: " + (", ".join(e["issues"]) if e["issues"] else "none found in declared scope"), ""]
    (output / "CHATGPT_RESUME_NOTE.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--include-context", action="store_true", help="Export compact CURRENT data locally; review before sharing")
    p.add_argument("--live-remote", action="store_true", help="Query origin/main without fetch or pull")
    args = p.parse_args()
    try:
        cfg = json.loads(args.config.read_text(encoding="utf-8-sig"))
        result = generate(cfg, args.output, include_context=args.include_context, network=args.live_remote)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("BLOCKED:", type(exc).__name__, str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"overall": result["overall"], "output": str(args.output),
                      "tasks": len(result["entries"])}, ensure_ascii=False))
    return 0 if result["overall"] == "REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
