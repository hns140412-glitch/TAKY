#!/usr/bin/env python3
"""One-shot bounded local continuation tick (intended: Task Scheduler every 30 min).

WORK_ID INT-001. Runs, in order, as separate processes:
  1. TOOLS/TAKY_CONVERSATION_REFRESH_LOCAL.py          (timeout 150s)
  2. TOOLS/TAKY_ORCHESTRATION_ADVANCE.py --continue    (timeout 180s)
Each JSON receipt is validated fail-closed. Only writes the private
latest.json receipt (atomic) under Workbench 00_CONTROL/PRIVATE_CONTINUATION_30M.

Not coding, not account-wide chat recovery, no model/paid calls, no
push/merge/deploy, no CURRENT edits, never claims portfolio DONE.
Task Scheduler registration is done separately by TAKY.

Exit codes: 0 TICK_OK / CHECK_ONLY_OK / SKIPPED_BUSY, 2 HOLD.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import msvcrt
except ImportError:  # non-Windows (tests/dev only)
    msvcrt = None
    import fcntl

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
WORKBENCH = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
CONTROL_DIR = WORKBENCH / "00_CONTROL" / "PRIVATE_CONTINUATION_30M"
REGISTRY = WORKBENCH / "01_BACKLOG_AND_ADOPTION" / "70_EXECUTION_QUEUE" / "TASK_REGISTER.json"
WORK_ID = "INT-001"
REGISTRY_SCHEMA = "TAKY_WORKBENCH_BACKLOG_V1"
REFRESH_TIMEOUT = 150
ADVANCE_TIMEOUT = 180
EXPORT_ONLY = "EXPORT_SOURCES_ONLY_NOT_ACCOUNT_COMPLETE"
LIMITATIONS = [
    "Runs only registered read-only local work; not coding.",
    "Native chat coverage is authorized export sources only, not account-complete chat recovery.",
    "No model/paid API calls, push, merge, deploy, or CURRENT edits; never claims portfolio DONE.",
]


class Hold(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Hold("JSON_UNREADABLE:%s:%s" % (Path(path).name, type(exc).__name__))


def preflight(repo, registry):
    """Read-only verification of STATE/MASTER, registry schema, unique IDs, INT-001."""
    for rel, marker in (("STATE.md", "TAKY CANONICAL RUNTIME STATE"),
                        ("MASTER/MASTER_LOGIC.md", "MASTER LOGIC")):
        p = Path(repo) / rel
        try:
            head = p.read_text(encoding="utf-8")[:4000]
        except OSError:
            raise Hold("CANONICAL_UNREADABLE:" + rel)
        if marker not in head:
            raise Hold("CANONICAL_MARKER_MISSING:" + rel)
    reg = read_json(registry)
    if not isinstance(reg, dict) or reg.get("schema") != REGISTRY_SCHEMA:
        raise Hold("REGISTRY_SCHEMA_INVALID")
    tasks = reg.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise Hold("REGISTRY_TASKS_INVALID")
    ids = []
    for t in tasks:
        tid = t.get("id") if isinstance(t, dict) else None
        if not isinstance(tid, str) or not tid.strip():
            raise Hold("REGISTRY_TASK_ID_INVALID")
        ids.append(tid)
    if len(set(ids)) != len(ids):
        raise Hold("REGISTRY_DUPLICATE_IDS")
    if WORK_ID not in ids:
        raise Hold("REGISTRY_MISSING_" + WORK_ID)
    for s in (HERE / "TAKY_CONVERSATION_REFRESH_LOCAL.py", HERE / "TAKY_ORCHESTRATION_ADVANCE.py"):
        if not s.is_file():
            raise Hold("TOOL_MISSING:" + s.name)
    return {"state_master": "OK", "registry_schema": REGISTRY_SCHEMA,
            "registry_task_count": len(ids), "work_id_present": WORK_ID}


def run_json(cmd, timeout, label):
    """Run a separate process; return (parsed last-line JSON, duration_s)."""
    t0 = time.monotonic()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
                           errors="replace", timeout=timeout, check=False, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise Hold("%s_TIMEOUT_%ds" % (label, timeout))
    except OSError as exc:
        raise Hold("%s_SPAWN_FAILED:%s" % (label, type(exc).__name__))
    dur = round(time.monotonic() - t0, 2)
    if r.returncode != 0:
        raise Hold("%s_EXIT_%s:%s" % (label, r.returncode, (r.stderr or "")[-200:].strip()))
    lines = (r.stdout or "").strip().splitlines()
    try:
        data = json.loads(lines[-1]) if lines else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise Hold(label + "_RECEIPT_NOT_JSON")
    return data, dur


def validate_refresh(d):
    ok = (d.get("mode") == "LOCAL_DERIVED_REFRESH"
          and type(d.get("paid_api_calls")) is int and d["paid_api_calls"] == 0
          and d.get("canonical_modified") is False
          and d.get("git_push_merge_deploy") is False
          and d.get("native_chat_coverage") == EXPORT_ONLY)
    if not ok:
        raise Hold("REFRESH_RECEIPT_INVALID")


def validate_advance(d):
    ok = (d.get("schema") == "TAKY_LOCAL_CONTINUATION_V1"
          and d.get("no_model_calls") is True
          and d.get("portfolio_done_claimed") is False
          and d.get("no_push_merge_deploy") is True
          and isinstance(d.get("actions"), list))
    if not ok:
        raise Hold("ADVANCE_RECEIPT_INVALID")


NONPRODUCTIVE_MARKERS = ("CHECK", "NEEDS_RECOVERY", "HOLD", "BLOCKED", "SKIP", "NOOP")


def progress_fields(actions, advance):
    """Honest progress labels; TICK_OK only means transport succeeded. Read-only, no side effects."""
    productive = [a for a in actions
                  if not any(m in str(a.get("status") or "").upper() for m in NONPRODUCTIVE_MARKERS)]
    if not actions:
        status = "NO_PRODUCT_PROGRESS"
    elif productive:
        status = "READONLY_ACTIONS_EXECUTED"
    else:
        status = "READONLY_CHECKS_ONLY"
    out = {"progress_status": status, "action_count": len(actions),
           "actual_product_implementation": False}
    unbound = advance.get("remaining_unbound") or 0
    dep_wait = advance.get("remaining_dep_wait") or 0
    if not actions and (unbound or dep_wait):
        out["blocked_progress_reason"] = ("NO_ACTIONS; remaining_unbound=%s remaining_dep_wait=%s"
                                          % (unbound, dep_wait))
        out["next_action"] = ("TAKY_INTERNAL_ROUTING: PENDING_IMPLEMENTATION - bind unbound work "
                              "to an internal TAKY owner/executor and resolve dependency holds; "
                              "not user review; no automatic Claude/Codex call; permissions and "
                              "approvals unchanged")
    return out


def tick(repo, registry, py=sys.executable):
    pre = preflight(repo, registry)
    refresh, d1 = run_json([py, "-B", str(HERE / "TAKY_CONVERSATION_REFRESH_LOCAL.py")],
                           REFRESH_TIMEOUT, "REFRESH")
    validate_refresh(refresh)
    adv, d2 = run_json([py, "-B", str(HERE / "TAKY_ORCHESTRATION_ADVANCE.py"), "--continue"],
                       ADVANCE_TIMEOUT, "ADVANCE")
    validate_advance(adv)
    actions = [{"work_id": a.get("task_id"), "status": a.get("status")}
               for a in adv["actions"] if isinstance(a, dict)]
    return {"preflight": pre,
            "refresh": {"mode": refresh["mode"], "duration_s": d1,
                        "stage_count": len(refresh.get("stages") or []),
                        "native_chat_coverage": refresh["native_chat_coverage"]},
            "advance": {"schema": adv["schema"], "status": adv.get("status"), "duration_s": d2,
                        "remaining_ready": adv.get("remaining_ready"),
                        "remaining_unbound": adv.get("remaining_unbound"),
                        "remaining_dep_wait": adv.get("remaining_dep_wait")},
            "work_ids": [a["work_id"] for a in actions],
            "actions": actions,
            "needs_recovery": sum(a["status"] == "LOCAL_EXECUTION_NEEDS_RECOVERY" for a in actions),
            **progress_fields(actions, adv)}


class Lock:
    """Nonblocking inter-process lock (msvcrt on Windows). acquire() -> bool."""

    def __init__(self, path):
        self.path, self.fh = Path(path), None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, "a+b")
        try:
            fh.seek(0)
            if msvcrt:
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self.fh = fh
        return True

    def release(self):
        if not self.fh:
            return
        try:
            self.fh.seek(0)
            if msvcrt:
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        finally:
            self.fh.close()
            self.fh = None


def write_atomic(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + ".%d.tmp" % os.getpid())
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None, control_dir=CONTROL_DIR, registry=REGISTRY, repo=REPO):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args(argv)
    control_dir = Path(control_dir)
    if args.check_only:
        try:
            pre = preflight(repo, registry)
        except Hold as exc:
            print(json.dumps({"status": "HOLD", "reason": str(exc), "mode": "CHECK_ONLY",
                              "writes": False}, ensure_ascii=False))
            return 2
        print(json.dumps({"status": "CHECK_ONLY_OK", "mode": "CHECK_ONLY", "writes": False,
                          "preflight": pre}, ensure_ascii=False))
        return 0
    lock = Lock(control_dir / "tick.lock")
    if not lock.acquire():
        print(json.dumps({"status": "SKIPPED_BUSY", "writes": False}, ensure_ascii=False))
        return 0
    started = now()
    t0 = time.monotonic()
    receipt = {"schema": "TAKY_WORK_CONTINUATION_30M_RECEIPT_V1", "work_id": WORK_ID,
               "started_at": started, "source_limitations": LIMITATIONS,
               "no_model_calls": True, "paid_api_calls": 0, "portfolio_done_claimed": False,
               "git_push_merge_deploy": False, "canonical_modified": False,
               "actual_product_implementation": False}
    try:
        try:
            receipt.update(tick(repo, registry))
            receipt["status"] = "TICK_OK"
            code = 0
        except Hold as exc:
            receipt.update(status="HOLD", reason=str(exc)[:400])
            code = 2
        receipt["total_duration_s"] = round(time.monotonic() - t0, 2)
        receipt["finished_at"] = now()
        write_atomic(control_dir / "latest.json", receipt)
    finally:
        lock.release()
    print(json.dumps({"status": receipt["status"], "work_ids": receipt.get("work_ids", []),
                      "reason": receipt.get("reason")}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
