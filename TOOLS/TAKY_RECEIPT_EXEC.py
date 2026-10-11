from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ORCH = Path(r"D:\Git PWA\TAKY-2.0-ORCH")


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ORCH)
    return subprocess.run(
        args,
        cwd=str(ORCH),
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Receipt-bound TAKY local executor")
    ap.add_argument("--plan-json", required=True)
    ap.add_argument("--invocation-json", required=True)
    ap.add_argument("--executor-id", default="TAKY_REMOTE_RECEIPT_EXECUTOR")
    ns = ap.parse_args()

    plan = _load(ns.plan_json)
    invocation = _load(ns.invocation_json)

    pre = _run([sys.executable, "-m", "TAKY2.orchestrator", "preflight", ns.plan_json])
    try:
        pre_obj = json.loads(pre.stdout)
    except Exception:
        print(pre.stdout, end="")
        print(pre.stderr, end="", file=sys.stderr)
        return pre.returncode or 2

    if not pre_obj.get("allowed") or not pre_obj.get("receipt_id"):
        print(json.dumps(pre_obj, ensure_ascii=False, indent=2))
        return pre.returncode or 2

    receipt_id = pre_obj["receipt_id"]
    call = plan.get("call")
    if invocation.get("call") != call:
        print(json.dumps({
            "allowed": False,
            "state": "INVOCATION_PLAN_MISMATCH",
            "receipt_id": receipt_id,
        }, ensure_ascii=False))
        return 2

    exe = _run([
        sys.executable, "-m", "TAKY2.orchestrator", "execute",
        receipt_id, ns.invocation_json, "--executor-id", ns.executor_id,
    ])
    try:
        exe_obj = json.loads(exe.stdout)
    except Exception:
        print(exe.stdout, end="")
        print(exe.stderr, end="", file=sys.stderr)
        return exe.returncode or 2

    out = {
        "allowed": bool(exe_obj.get("allowed")),
        "state": exe_obj.get("state"),
        "receipt_id": receipt_id,
        "verification_state": "UNVERIFIED",
        "result": exe_obj.get("result"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
