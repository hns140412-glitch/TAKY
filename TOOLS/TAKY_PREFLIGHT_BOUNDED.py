#!/usr/bin/env python3
"""Bounded TAKY2 preflight supervisor; never invokes a model or bypasses a gate."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ORCH = Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")
PREFLIGHT_TIMEOUT = 35
RELEASE_TIMEOUT = 18


def releasable_preinvoke(runtime, task_id):
    """Return a receipt only when exactly one authorized, unclaimed PENDING attempt exists."""
    receipts = runtime.get("preflight_receipts") or {}
    matches = [(rid, rec) for rid, rec in receipts.items()
               if isinstance(rec, dict) and rec.get("task_id") == task_id
               and rec.get("call_allowed") is True]
    if len(matches) != 1:
        return None
    rid = matches[0][0]
    if rid in (runtime.get("execution_calls") or {}):
        return None
    actives = [entry for entry in (runtime.get("active_attempts") or {}).values()
               if isinstance(entry, dict) and entry.get("receipt_id") == rid]
    if len(actives) != 1 or actives[0].get("status") != "PENDING":
        return None
    return rid


def safe_release(plan, env, runner=subprocess.run):
    """Only use the official signed state transition, with model claim detection."""
    task_id = plan.get("task_id")
    if not isinstance(task_id, str) or not task_id.startswith("external-review-"):
        return "NOT_TARGETED"
    try:
        sys.path.insert(0, str(ORCH))
        from TAKY2.state_store import load_bundle
        _, runtime, _ = load_bundle()
        rid = releasable_preinvoke(runtime, task_id)
        if not rid:
            return "NO_UNCLAIMED_RECEIPT_HOLD"
        result = runner(
            [sys.executable, "-B", "-m", "TAKY2.orchestrator", "release-uninvoked",
             rid, "WRAPPER_INTERRUPTED_BEFORE_CLAIM"],
            cwd=str(ORCH), env=env, shell=False, text=True,
            capture_output=True, encoding="utf-8", errors="replace",
            timeout=RELEASE_TIMEOUT)
        answer = json.loads(result.stdout)
        if (result.returncode == 0 and answer.get("allowed") is True
                and answer.get("state") == "PREINVOKE_RELEASED"
                and answer.get("receipt_id") == rid
                and answer.get("model_call_registered") is False):
            return "PREINVOKE_RELEASED"
        return "RELEASE_NOT_ATTESTED_HOLD"
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired, RuntimeError):
        return "RELEASE_UNVERIFIED_HOLD"


def run(plan_path, runner=subprocess.run):
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ORCH)
    try:
        proc = runner(
            [sys.executable, "-B", "-m", "TAKY2.orchestrator",
             "preflight", str(plan_path)],
            cwd=str(ORCH), env=env, shell=False, text=True, capture_output=True,
            encoding="utf-8", errors="replace", timeout=PREFLIGHT_TIMEOUT)
    except subprocess.TimeoutExpired:
        release = safe_release(plan, env)
        print(json.dumps({"allowed": False, "blocked_by": "PREFLIGHT_TIMEOUT",
                          "mode": "HOLD", "release_state": release,
                          "reason": "Preflight exceeded bounded timeout; no model invoked by this supervisor."},
                         ensure_ascii=False))
        return 124
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plan_json", type=Path)
    args = ap.parse_args()
    if not args.plan_json.is_file():
        print('{"allowed":false,"mode":"HOLD","reason":"PLAN_MISSING"}')
        return 2
    return run(args.plan_json)


if __name__ == "__main__":
    raise SystemExit(main())
