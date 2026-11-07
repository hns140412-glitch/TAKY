#!/usr/bin/env python3
"""TAKY delta collector: PostToolUse hook (Local/Collector = deterministic, local-first).

Idea taken from replay-theater (anthropics/claude-code-playground): record what
Claude did without ever changing or blocking it. Here the record feeds the
CURRENT DELTA rule: each edit, commit, push and deploy is appended to
~/.taky/delta/<YYYYMMDD>.jsonl, so the session can draft its DELTA from
facts instead of memory.  `python3 taky_delta.py --draft [jsonl]` prints a draft.
"""
import datetime as dt
import json
import os
import re
import sys

WATCH_BASH = re.compile(r"\b(git\s+(commit|push|merge|tag)|gh\s+pr\s+(create|merge)|netlify\s+deploy|npm\s+(test|run\s+build))\b")


def log_dir(event):
    return os.path.join(os.environ.get("TAKY_HOME") or os.path.join(os.path.expanduser("~"), ".taky"), "delta")


def record(event):
    tool = event.get("tool_name", "")
    ti = event.get("tool_input") or {}
    resp = event.get("tool_response") or {}
    rec = None
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        rec = {"kind": "edit", "tool": tool, "file": ti.get("file_path") or ti.get("notebook_path")}
    elif tool == "Bash" and WATCH_BASH.search(str(ti.get("command", ""))):
        out = resp.get("stdout", "") if isinstance(resp, dict) else str(resp)
        rec = {"kind": "command", "command": str(ti["command"])[:300],
               "exit": resp.get("exitCode", resp.get("exit_code")) if isinstance(resp, dict) else None,
               "tail": str(out)[-300:]}
    if rec is None:
        return None
    rec["ts"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec["session"] = event.get("session_id", "")[:12]
    rec["project"] = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ""
    return rec


def draft(path):
    edits, cmds = {}, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["kind"] == "edit":
                edits[r["file"]] = edits.get(r["file"], 0) + 1
            else:
                cmds.append(r)
    day = os.path.basename(path).split(".")[0]
    print(f"DELTA {day} (자동 초안 · 수집기 기록 기준, 검증 상태는 사람이 확인)")
    print(f"- 수정 파일 {len(edits)}개: " + ", ".join(sorted(os.path.basename(k or '?') for k in edits)[:12]))
    for c in cmds:
        print(f"- {c['ts']} `{c['command'][:90]}` exit={c.get('exit')}")
    print("- OPEN: (작성자가 채움)  · 상태 사다리: APPLIED != VERIFIED")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--draft":
        path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
            os.environ.get("TAKY_HOME") or os.path.join(os.path.expanduser("~"), ".taky"), "delta", dt.date.today().strftime("%Y%m%d") + ".jsonl")
        draft(path)
        return 0
    try:
        event = json.load(sys.stdin)
        rec = record(event)
        if rec:
            d = log_dir(event)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, dt.date.today().strftime("%Y%m%d") + ".jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # a collector must never break the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
