#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "taky_hook.py"

CASES = [
    ("Edit", {"file_path": "TAKY.md"}, "ask"),
    ("Edit", {"file_path": "HANDOFF/x.md"}, None),
    ("NotebookEdit", {"notebook_path": "MASTER/review.ipynb"}, "ask"),
    ("Read", {"file_path": ".env"}, "ask"),
    ("PowerShell", {"command": "Get-Content .env"}, "ask"),
    ("Bash", {"command": "cat .env"}, "ask"),
    ("PowerShell", {"command": "Set-Content TAKY.md test"}, "ask"),
    ("PowerShell", {"command": "[IO.File]::WriteAllText('TAKY.md','changed')"}, "ask"),
    ("PowerShell", {"command": "New-Item MASTER/probe.txt -ItemType File"}, "ask"),
    ("Bash", {"command": "echo changed > .claude/hooks/taky_hook.py"}, "ask"),
    ("Bash", {"command": "tee .claude/hooks/taky_hook.py < patch.txt"}, "ask"),
    ("Bash", {"command": "sed -i 's/a/b/' TAKY.md"}, "ask"),
    ("Bash", {"command": "python -c \"open('TAKY.md','w').write('x')\""}, "ask"),
    ("Bash", {"command": "git log origin/master/..HEAD"}, None),
    ("Bash", {"command": "git diff -- TAKY.md"}, None),
    ("Bash", {"command": "git status; printf changed > MASTER/VALIDATION_RULES.md"}, "ask"),
    ("PowerShell", {"command": "Get-Content TAKY.md; Set-Content TAKY.md changed"}, "ask"),
    ("PowerShell", {"command": "Get-Content TAKY.md | Set-Content MASTER/probe.md"}, "ask"),
    ("Bash", {"command": "git diff -- TAKY.md $(python -c 'print(1)')"}, "ask"),
    ("Bash", {"command": "git push origin main"}, "ask"),
    ("Bash", {"command": "gh pr merge 12"}, "ask"),
    ("mcp__scenario__model_run", {}, "ask"),
    ("mcp__example__delete_item", {"id": "1"}, "ask"),
    ("mcp__playwright__browser_navigate", {"url": "http://localhost/share/account"}, None),
]

def run_case(tool, tool_input):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "cwd": str(ROOT),
        "tool_input": tool_input,
    }
    p = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    out = p.stdout.strip()
    if not out:
        return None
    data = json.loads(out)
    return data["hookSpecificOutput"]["permissionDecision"]

def main():
    failures = []
    for tool, tool_input, expected in CASES:
        actual = run_case(tool, tool_input)
        if actual != expected:
            failures.append(f"{tool}: expected={expected!r} actual={actual!r}")
    if failures:
        print("FAIL: " + " | ".join(failures))
        return 1
    print(f"PASS: Claude hook regression {len(CASES)}/{len(CASES)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


def _run_hook(payload):
    import subprocess, json
    hook = ROOT / ".claude" / "hooks" / "taky_hook.py"
    cp = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    return cp

def test_cost_dry_run_budget_runtime():
    session = "cost-gate-regression"
    prompt = _run_hook({
        "hook_event_name": "UserPromptSubmit",
        "session_id": session,
        "cwd": str(ROOT),
        "prompt": "검토하고 최소 호출로 실행",
    })
    assert prompt.returncode == 0
    assert "TAKY DRY_RUN_PLAN active" in prompt.stdout

    first = _run_hook({
        "hook_event_name": "PreToolUse",
        "session_id": session,
        "cwd": str(ROOT),
        "tool_name": "Bash",
        "tool_input": {"command": "codex exec --sandbox read-only -C . review"},
    })
    assert first.returncode == 0
    assert '"permissionDecision": "deny"' not in first.stdout

    second = _run_hook({
        "hook_event_name": "PreToolUse",
        "session_id": session,
        "cwd": str(ROOT),
        "tool_name": "Bash",
        "tool_input": {"command": "codex exec --sandbox read-only -C . review-again"},
    })
    assert second.returncode == 0
    assert '"permissionDecision": "deny"' in second.stdout
    assert "external-model call budget exhausted" in second.stdout



def test_existing_session_pretool_bootstraps_cost_gate():
    import subprocess, json
    session = "existing-session-cost-bootstrap"
    state_dir = Path.home() / ".claude" / "taky" / "cost-gate-state"
    import hashlib
    key = hashlib.sha256(session.encode("utf-8")).hexdigest()[:20]
    state_path = state_dir / f"{key}.json"
    state_path.unlink(missing_ok=True)

    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": session,
        "cwd": str(ROOT),
        "tool_name": "mcp__Remote_Desktop_Commander__read_file",
        "tool_input": {"path": "D:/Git PWA/TAKY/TAKY.md"},
    }
    hook = ROOT / ".claude" / "hooks" / "taky_hook.py"
    first = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True, capture_output=True, cwd=ROOT,
    )
    assert first.returncode == 0
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["bootstrap"] == "PRETOOL_EXISTING_SESSION_FAILSAFE"
    assert state["remote_calls"] == 1


def test_remote_cache_tightens_budget():
    import json, subprocess, hashlib
    from datetime import datetime, timezone
    cache = Path.home() / "TAKY_TMP" / "runtime-log" / "remote-usage.json"
    old = cache.read_text(encoding="utf-8") if cache.exists() else None
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({
            "schema":"TAKY_REMOTE_USAGE_CACHE_V1","remaining_pct":9,
            "checked_at":datetime.now(timezone.utc).isoformat(),"source":"test",
        }),encoding="utf-8")
        session="remote-cache-budget-regression"
        key=hashlib.sha256(session.encode("utf-8")).hexdigest()[:20]
        state=Path.home()/".claude"/"taky"/"cost-gate-state"/f"{key}.json"
        state.unlink(missing_ok=True)
        hook=ROOT/".claude"/"hooks"/"taky_hook.py"
        payload={
            "hook_event_name":"PreToolUse","session_id":session,"cwd":str(ROOT),
            "tool_name":"mcp__Remote_Desktop_Commander__read_file",
            "tool_input":{"path":"D:/Git PWA/TAKY/TAKY.md"},
        }
        a=subprocess.run([sys.executable,str(hook)],input=json.dumps(payload),text=True,capture_output=True,cwd=ROOT)
        b=subprocess.run([sys.executable,str(hook)],input=json.dumps(payload),text=True,capture_output=True,cwd=ROOT)
        assert a.returncode==0 and '"permissionDecision": "deny"' not in a.stdout
        assert b.returncode==0 and '"permissionDecision": "deny"' in b.stdout
    finally:
        if old is None: cache.unlink(missing_ok=True)
        else: cache.write_text(old,encoding="utf-8")
