"""Hidden, bounded Windows Task Scheduler entrypoint for existing TAKY/Reason.

No standalone service, network credentials, new model executor, or CURRENT writes.
Runs only messages referring to preprepared local work, through the original
TAKY receipt and authorization gates.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
LOCAL = REPO / ".local"
PYTHON = Path(sys.executable).with_name("python.exe")
INGRESS = REPO / "ENFORCEMENT" / "reason_queue_ingress.py"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
COMMAND = [str(PYTHON), "-B", str(INGRESS), "--repo-root", str(REPO),
           "--drain", "--max-messages", "4", "--execute"]
TIMEOUT_SECONDS = 3600


def _status(result: dict) -> dict:
    observations = result.get("observations")
    if not isinstance(observations, list):
        observations = []
    return {
        "state": result.get("status"),
        "transport_failure_code": result.get("transport_failure_code"),
        "transport_exit_code": result.get("transport_exit_code"),
        "transport_error_detail": result.get("transport_error_detail"),
        "messages_observed": result.get("messages_observed"),
        "messages_dispatched": result.get("messages_dispatched"),
        "messages_recovered": result.get("messages_recovered"),
        "queue_statuses": [item.get("queue_status") for item in observations
                           if isinstance(item, dict)],
    }


def run_dependency_progress(repo: Path) -> dict:
    from taky_dependency_recovery import recover_deferred_once
    return recover_deferred_once(repo,max_receipts=30)


def run_canonical_progress(repo: Path) -> dict:
    """Reuse TAKY's existing safe local executor, bounded to two per tick.

    Preserve all gates in TAKY_ORCHESTRATION_ADVANCE; this is not a second
    executor or a model/provider permission.
    """
    tools_root=repo/"TOOLS"
    if (not tools_root.is_dir() or tools_root.is_symlink()
            or getattr(tools_root,"is_junction",lambda:False)()
            or tools_root.resolve().parent != repo.resolve()):
        raise ValueError("CANONICAL_LOCAL_OWNER_NOT_PINNED")
    if str(tools_root) not in sys.path:
        sys.path.insert(0,str(tools_root))
    from TAKY_ORCHESTRATION_ADVANCE import continue_local, DEFAULT_BOARD, EVIDENCE
    result=continue_local(DEFAULT_BOARD,EVIDENCE,max_actions=2)
    if (not isinstance(result,dict) or
            result.get("schema")!="TAKY_LOCAL_CONTINUATION_V1" or
            result.get("no_model_calls") is not True or
            result.get("portfolio_done_claimed") is not False or
            len(result.get("actions",[]))>2):
        raise ValueError("CANONICAL_LOCAL_RESULT_UNTRUSTED")
    return result


def main() -> int:
    if not INGRESS.is_file() or not PYTHON.is_file():
        return 2
    # Unblock formerly held canonical read-only work on changed verified
    # dependency evidence. This never invokes Claude/Codex or modifies CURRENT.
    try:
        dependency = run_dependency_progress(REPO)
    except Exception:
        dependency = {"status":"DEPENDENCY_WATCH_UNAVAILABLE",
                      "new_attempts":0,"uncertain":1}
    # Read-only canonical progress even with an empty Reason inbox.
    # Tests inject the pump; production always uses the original owner.
    try:
        local_work=run_canonical_progress(REPO)
    except Exception as exc:
        local_work={"status":"CANONICAL_LOCAL_PROGRESS_REQUIRES_RECOVERY",
                    "error_class":type(exc).__name__,"actions":[]}
    try:
        completed = subprocess.run(
            COMMAND, cwd=REPO, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=TIMEOUT_SECONDS,
            creationflags=FLAGS,
        )
        try:
            result = json.loads(completed.stdout)
        except (TypeError, ValueError):
            result = {"status": "INGRESS_OUTPUT_UNVERIFIED"}
        if not isinstance(result, dict):
            result = {"status": "INGRESS_OUTPUT_UNVERIFIED"}
        status = _status(result)
        status["exit_code"] = completed.returncode
    except (OSError, subprocess.TimeoutExpired):
        status = {"state": "INGRESS_OUTCOME_UNKNOWN_RECONCILE",
                  "exit_code": 2}
    # The watcher is silent unless a *new* dependency-state action occurred.
    status["dependency_resume_attempts"] = dependency.get("new_attempts",0)
    status["dependency_uncertain"] = dependency.get("uncertain",0)
    status["canonical_local_actions"] = [
        {"work_id":a.get("task_id"),"state":a.get("status")}
        for a in local_work.get("actions",[]) if isinstance(a,dict)]
    status["canonical_local_state"]=local_work.get("status")
    if (status.get("state") != "REASON_BURST_DRAINED_NO_MORE_MESSAGES"
            or status.get("messages_observed", 0) > 0
            or status["dependency_resume_attempts"] > 0
            or status["dependency_uncertain"] > 0
            or bool(status["canonical_local_actions"])
            or status["canonical_local_state"] != "BOUNDED_LOCAL_CONTINUATION_FINISHED"):
        if (not LOCAL.is_dir() or LOCAL.is_symlink()
                or getattr(LOCAL,"is_junction",lambda:False)()
                or LOCAL.resolve().parent != REPO.resolve()):
            return 2
        log = LOCAL / "taky-reason-ingress-runs.jsonl"
        if (log.is_symlink() or getattr(log,"is_junction",lambda:False)()
                or (log.exists() and not log.is_file())):
            return 2
        line = {"schema": "TAKY_REASON_RUN_OBSERVATION_V1",
                "at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                **status}
        try:
            flags=(os.O_WRONLY|os.O_CREAT|os.O_APPEND|
                   getattr(os,"O_NOFOLLOW",0))
            fd=os.open(log,flags,0o600)
            with os.fdopen(fd,"a",encoding="utf-8") as stream:
                observed=os.fstat(stream.fileno())
                actual=os.stat(log,follow_symlinks=False)
                if ((observed.st_dev,observed.st_ino)!=
                        (actual.st_dev,actual.st_ino)):
                    return 2
                stream.write(json.dumps(line,ensure_ascii=False)+"\n")
        except OSError:
            return 2
    return 0 if (status.get("exit_code") == 0
                 and status.get("canonical_local_state")=="BOUNDED_LOCAL_CONTINUATION_FINISHED"
                 and dependency.get("status")=="BOUNDED_DEPENDENCY_OBSERVATION"
                 and status.get("state") in {
                     "REASON_BURST_DRAINED_NO_MORE_MESSAGES",
                     "REASON_BURST_LIMIT_REACHED",
                 }) else 2


if __name__ == "__main__":
    raise SystemExit(main())
