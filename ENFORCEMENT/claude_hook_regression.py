#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
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
    ("Bash", {"command": "git -C 'D:/Git PWA/SAVEY' push origin main"}, "ask"),
    ("PowerShell", {"command": "git -C \"D:/Git PWA/SAVEY\" merge feature-branch"}, "ask"),
    ("Bash", {"command": "git rebase main"}, "ask"),
    ("Bash", {"command": "netlify deploy --dir dist"}, "ask"),
    ("Bash", {"command": "npx netlify deploy --prod"}, "ask"),
    ("Bash", {"command": "gh pr merge 12"}, "ask"),
    ("mcp__GitHub__push_files", {"owner": "example", "repo": "sample", "branch": "main"}, "ask"),
    ("mcp__Netlify__deploy", {"site_id": "dummy", "draft": True}, "ask"),
    ("Bash", {"command": "git -c core.hooksPath=none push origin main"}, "ask"),
    ("Bash", {"command": "git --no-pager pull origin main"}, "ask"),
    ("Bash", {"command": "git cherry-pick abc123"}, "ask"),
    ("Bash", {"command": "curl https://api.anthropic.com/v1/messages"}, "ask"),
    ("PowerShell", {"command": "Invoke-RestMethod https://api.openai.com/v1/responses"}, "ask"),
    ("mcp__GitHub__merge_pull_request", {"pull_number": 1}, "ask"),
    ("Bash", {"command": "git commit -m 'local checkpoint'"}, None),
    ("Bash", {"command": "git status --short"}, None),
    ("Bash", {"command": "npm run build"}, None),
    ("mcp__scenario__model_run", {}, "ask"),
    ("mcp__example__delete_item", {"id": "1"}, "ask"),
    ("mcp__playwright__browser_navigate", {"url": "http://localhost/share/account"}, None),
    # Read-only operations must not require approval merely because a noun
    # contains "release", "deploy", "permission", or "account".
    ("mcp__GitHub__get_release", {"owner": "example", "repo": "demo", "release_id": "1"}, None),
    ("mcp__GitHub__list_releases", {"owner": "example", "repo": "demo"}, None),
    ("mcp__Netlify__get_deploy", {"deploy_id": "demo"}, None),
    ("mcp__Netlify__list_deploys", {"site_id": "demo"}, None),
    ("mcp__Google_Drive__get_permissions", {"file_id": "demo"}, None),
    ("mcp__Example__get_account", {"id": "demo"}, None),
    # Read-only names do not authorize an explicitly mutating operation.
    ("mcp__GitHub__get_release", {"operation": "delete"}, "ask"),
    ("mcp__Netlify__get_deploy", {"action": "publish"}, "ask"),
    ("mcp__Netlify__deploy", {"site_id": "demo"}, "ask"),
    ("mcp__Gmail__send_message", {"recipient": "example@example.com"}, "ask"),
]

def run_case(tool, tool_input):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "cwd": str(ROOT),
        "session_id": "TAKY-ISOLATED-PERMISSION-REGRESSION",
        "tool_input": tool_input,
    }
    # Never consume or alter a real Claude session's cost gate during tests.
    with tempfile.TemporaryDirectory(prefix="TAKY_HOOK_QA_") as isolated:
        env = {**os.environ, "HOME": isolated, "USERPROFILE": isolated}
        p = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            env=env,
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


def test_remote_cache_guides_without_blocking():
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
        assert b.returncode==0 and '"permissionDecision": "deny"' not in b.stdout
        assert "TAKY SOFT ROUTE GUIDANCE" in b.stdout
        assert '"additionalContext"' in b.stdout
        # Protected high-impact actions must still be gated past soft budget.
        high = dict(payload)
        high["tool_name"] = "mcp__Remote_Desktop_Commander__start_process"
        high["tool_input"] = {"command":"git push origin main"}
        c = subprocess.run([sys.executable,str(hook)],input=json.dumps(high),
                           text=True,capture_output=True,cwd=ROOT)
        assert c.returncode == 0 and '"permissionDecision": "ask"' in c.stdout
    finally:
        if old is None: cache.unlink(missing_ok=True)
        else: cache.write_text(old,encoding="utf-8")


def test_codex_companion_model_route_is_bounded_without_blocking_readonly_status():
    """Official plugin must not silently bypass the existing model-call budget."""
    import hashlib

    with tempfile.TemporaryDirectory(prefix="TAKY_CODEX_PLUGIN_GATE_") as isolated:
        env = {**os.environ, "HOME": isolated, "USERPROFILE": isolated,
               "TAKY_MAX_EXTERNAL_MODEL_CALLS_PER_PROMPT": "1"}
        session = "official-codex-plugin-shepherd-test"
        plugin = r'C:\Users\example\.claude\plugins\cache\openai-codex\codex\1.0.6\scripts\codex-companion.mjs'

        def invoke(event, command=None):
            payload = {"hook_event_name": event, "session_id": session,
                       "cwd": str(ROOT)}
            if command is not None:
                payload.update(tool_name="Bash", tool_input={"command": command})
            proc = subprocess.run([sys.executable, str(HOOK)],
                                  input=json.dumps(payload), text=True,
                                  capture_output=True, encoding="utf-8",
                                  errors="replace", check=True, env=env)
            return proc.stdout.strip()

        invoke("UserPromptSubmit")
        # Setup and status are local inspections and must remain available.
        for op in ("setup --json", "status --all"):
            assert '"permissionDecision": "deny"' not in invoke(
                "PreToolUse", f'node "{plugin}" {op}'
            )
        first = invoke("PreToolUse", f'node "{plugin}" review --wait')
        assert '"permissionDecision": "deny"' not in first, first
        second = invoke("PreToolUse", f'node "{plugin}" adversarial-review --wait')
        assert '"permissionDecision": "deny"' in second, second
        assert "REROUTE_REQUIRED" in second and "local deterministic" in second
        # Bounded model work must never prohibit local status inspection.
        assert '"permissionDecision": "deny"' not in invoke(
            "PreToolUse", f'node "{plugin}" status --all'
        )
        key = hashlib.sha256(session.encode("utf-8")).hexdigest()[:20]
        p = Path(isolated) / ".claude" / "taky" / "cost-gate-state" / f"{key}.json"
        state = json.loads(p.read_text(encoding="utf-8"))
        assert state["external_model_calls"] == 1


def test_codex_plugin_signed_route_and_verifier_boundary():
    """A signed verifier readiness is not permission for task/write/transfer."""
    import hashlib

    with tempfile.TemporaryDirectory(prefix="TAKY_PLUGIN_PREFLIGHT_") as isolated:
        env = {**os.environ, "HOME": isolated, "USERPROFILE": isolated,
               "TAKY_MAX_EXTERNAL_MODEL_CALLS_PER_PROMPT": "1"}
        session = "codex-signed-route-test"
        companion = r'C:\Users\example\.claude\plugins\cache\openai-codex\codex\1.0.6\scripts\codex-companion.mjs'

        def invoke(event, command=None, cwd=None, prompt=None, tool="Bash"):
            payload = {"hook_event_name": event, "session_id": session,
                       "cwd": str(cwd if cwd is not None else ROOT)}
            if prompt is not None:
                payload["prompt"] = prompt
            if command is not None:
                payload.update(tool_name=tool, tool_input={"command": command})
            p = subprocess.run([sys.executable, str(HOOK)],
                               input=json.dumps(payload, ensure_ascii=False),
                               text=True, capture_output=True, env=env,
                               encoding="utf-8", errors="replace", check=True)
            return json.loads(p.stdout) if p.stdout.strip() else {}

        invoke("UserPromptSubmit", prompt="코드 독립 검증")
        # No arbitrary model task may inherit the verifier-only signed route.
        for action in ("task --write", "transfer"):
            got = invoke("PreToolUse", f'node "{companion}" {action}')
            decision = got.get("hookSpecificOutput", {}).get("permissionDecision")
            assert decision == "deny", (action, got)
            assert "verifier-only" in got["hookSpecificOutput"]["permissionDecisionReason"]

        # An unregistered workspace must fail closed before using the budget.
        foreign = invoke("PreToolUse", f'node "{companion}" review --wait', cwd=isolated)
        assert foreign["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "signed Codex verifier route is HOLD" in foreign["hookSpecificOutput"]["permissionDecisionReason"]

        key = hashlib.sha256(session.encode()).hexdigest()[:20]
        state_path = Path(isolated)/".claude"/"taky"/"cost-gate-state"/f"{key}.json"
        before = json.loads(state_path.read_text(encoding="utf-8"))
        assert before["external_model_calls"] == 0

        from importlib.util import spec_from_file_location, module_from_spec
        # Match the production hook's trusted-tool import path.
        tools_path = str(ROOT / "TOOLS")
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        spec = spec_from_file_location("signed_route_probe", ROOT/"TOOLS"/"TAKY_GOVERNED_ROUTE_HEALTH.py")
        route = module_from_spec(spec)
        spec.loader.exec_module(route)
        health = route.signed_health("Codex", str(ROOT))
        ready = health.get("status") == "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES"
        accepted = invoke("PreToolUse", f'node "{companion}" review --wait',
                          tool="mcp__Remote_Desktop_Commander__start_process")
        accepted_decision = accepted.get("hookSpecificOutput", {}).get("permissionDecision")
        assert (accepted_decision != "deny") == ready, (health, accepted)
        current = json.loads(state_path.read_text(encoding="utf-8"))
        assert current["external_model_calls"] == (1 if ready else 0)
        assert current["remote_calls"] == 0


def test_cost_budget_follows_explicit_continue_not_new_task():
    """User follow-ups do not mint fresh external-model allowance."""
    import hashlib
    with tempfile.TemporaryDirectory(prefix="TAKY_BUDGET_CONTINUE_") as isolated:
        env = {**os.environ, "HOME": isolated, "USERPROFILE": isolated,
               "TAKY_MAX_EXTERNAL_MODEL_CALLS_PER_PROMPT": "1"}
        session = "bounded-same-task"
        command = "codex exec --sandbox read-only -C . sample-review"

        def invoke(event, prompt=None, tool_command=None):
            payload = {"hook_event_name": event, "session_id": session,
                       "cwd": str(ROOT)}
            if prompt is not None:
                payload["prompt"] = prompt
            if tool_command is not None:
                payload.update(tool_name="Bash", tool_input={"command": tool_command})
            result = subprocess.run([sys.executable, str(HOOK)],
                                    input=json.dumps(payload, ensure_ascii=False),
                                    text=True, capture_output=True, check=True,
                                    encoding="utf-8", errors="replace", env=env)
            return result.stdout

        invoke("UserPromptSubmit", prompt="검증 수행")
        first = invoke("PreToolUse", tool_command=command)
        assert '"permissionDecision": "deny"' not in first
        followup = invoke("UserPromptSubmit", prompt="ㄱ")
        assert "Remaining external-model call allowance=0/1" in followup
        second = invoke("PreToolUse", tool_command=command)
        assert '"permissionDecision": "deny"' in second
        assert "budget exhausted" in second
        invoke("UserPromptSubmit", prompt="새로운 작업 시작")
        third = invoke("PreToolUse", tool_command=command)
        assert '"permissionDecision": "deny"' not in third
        key = hashlib.sha256(session.encode()).hexdigest()[:20]
        state = json.loads((Path(isolated)/".claude"/"taky"/"cost-gate-state"/f"{key}.json").read_text(encoding="utf-8"))
        assert state["external_model_calls"] == 1


def test_direct_model_cli_on_remote_shell_uses_model_budget():
    """The remote terminal is not a model-cost or signed-CLI escape hatch."""
    import hashlib
    with tempfile.TemporaryDirectory(prefix="TAKY_REMOTE_MODEL_BUDGET_") as isolated:
        env = {**os.environ, "HOME": isolated, "USERPROFILE": isolated,
               "TAKY_MAX_EXTERNAL_MODEL_CALLS_PER_PROMPT": "1"}
        session = "remote-direct-model-meter"
        def invoke(event, command=None):
            payload = {"hook_event_name": event, "session_id": session,
                       "cwd": str(ROOT)}
            if command is not None:
                payload.update(tool_name="mcp__Remote_Desktop_Commander__start_process",
                               tool_input={"command": command})
            proc = subprocess.run([sys.executable, str(HOOK)],
                                  input=json.dumps(payload), text=True, capture_output=True,
                                  check=True, env=env, encoding="utf-8", errors="replace")
            return proc.stdout

        invoke("UserPromptSubmit")
        first = invoke("PreToolUse", r'& "C:\Users\example\bin\codex.cmd" exec --sandbox read-only review')
        assert '"permissionDecision": "deny"' not in first, first
        second = invoke("PreToolUse", "codex.exe app-server")
        assert '"permissionDecision": "deny"' in second, second
        assert "external-model call budget exhausted" in second
        diagnostic = invoke("PreToolUse", "codex login status")
        assert '"permissionDecision": "deny"' not in diagnostic
        key = hashlib.sha256(session.encode()).hexdigest()[:20]
        state = json.loads((Path(isolated)/".claude"/"taky"/"cost-gate-state"/f"{key}.json").read_text(encoding="utf-8"))
        assert state["external_model_calls"] == 1
        assert state["remote_calls"] == 1
