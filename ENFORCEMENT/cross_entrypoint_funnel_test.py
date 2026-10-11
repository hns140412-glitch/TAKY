from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(r"D:\Git PWA\TAKY")
TOOLS = ROOT / "TOOLS"


def test_codex_canonical_entrypoint_uses_receipt_executor():
    text = (TOOLS / "TAKY_CODEX.ps1").read_text(encoding="utf-8-sig")
    assert "TAKY_RECEIPT_EXEC.py" in text
    assert "--plan-json" in text
    assert "--invocation-json" in text


def test_codex_shim_reroutes_execution_but_preserves_metadata_commands():
    text = (TOOLS / "TAKY_CODEX_SHIM.ps1").read_text(encoding="utf-8-sig")
    assert "TAKY_PLAN_JSON" in text
    assert "TAKY_INVOCATION_JSON" in text
    assert "TAKY REROUTE_REQUIRED" in text
    assert "login" in text
    assert "--version" in text
    assert "AppData\\Roaming\\npm\\codex.cmd" in text


def test_model_review_bypasses_user_shim_only_inside_canonical_wrapper():
    text = (TOOLS / "TAKY_MODEL_REVIEW.ps1").read_text(encoding="utf-8-sig")
    assert "$realCodex=" in text
    assert "$appCodex=" in text
    assert "$routeTool='codex-ephemeral'" in text
    assert "$codexBinary,'exec'" in text
    assert "'--ephemeral'" in text
    assert "'--ignore-user-config'" in text
    assert "TAKY2.orchestrator preflight" in text
    assert "TAKY2.orchestrator execute" in text
    assert "$rc -eq 124" in text
    assert "record-failure $pre.receipt_id ENVIRONMENT" in text
    assert "2> $preErrPath" in text
    assert "2> $execErrPath" in text
    assert "execute stdout was not valid JSON; receipt released as ENVIRONMENT" in text


def test_global_claude_settings_have_taky_hooks_without_losing_existing_surface():
    settings = json.loads(
        (Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8-sig")
    )
    hooks = settings.get("hooks", {})
    assert set((
        "SessionStart","PreCompact","PreToolUse","UserPromptSubmit",
        "PostToolUse","PostToolUseFailure","Stop","StopFailure",
    )).issubset(hooks)
    blob = json.dumps(hooks, ensure_ascii=False)
    assert "D:/Git PWA/TAKY/.claude/hooks/taky_hook.py" in blob
    assert "D:/Git PWA/TAKY/.claude/hooks/taky_outcome_hook.py" in blob
    assert "enabledPlugins" in settings
    assert "statusLine" in settings


def test_project_claude_settings_cover_failure_events():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
    hooks = settings.get("hooks", {})
    assert "PostToolUseFailure" in hooks
    assert "StopFailure" in hooks
    blob = json.dumps(hooks, ensure_ascii=False)
    assert "taky_outcome_hook.py" in blob


def test_powershell_json_stream_separation_is_behavioral():
    code = (
        "import json,sys;"
        "print(json.dumps({'ok': True}));"
        "print('diagnostic-on-stderr', file=sys.stderr)"
    )
    script = r"""
$errPath = [IO.Path]::GetTempFileName()
try {
  $stdout = (& python -c $env:TAKY_STREAM_TEST_CODE 2> $errPath | Out-String)
  $rc = $LASTEXITCODE
  if ($rc -ne 0) { exit $rc }
  $obj = $stdout | ConvertFrom-Json
  $stderr = Get-Content -LiteralPath $errPath -Raw
  if (-not $obj.ok) { exit 31 }
  if ($stderr -notmatch 'diagnostic-on-stderr') { exit 32 }
  Write-Output 'PASS'
} finally {
  Remove-Item -LiteralPath $errPath -Force -ErrorAction SilentlyContinue
}
"""
    env = dict(__import__("os").environ)
    env["TAKY_STREAM_TEST_CODE"] = code
    cp = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        text=True, capture_output=True, env=env,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr
    assert "PASS" in cp.stdout
