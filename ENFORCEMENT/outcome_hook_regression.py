#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "taky_outcome_hook.py"
TEST_LEDGER = Path(tempfile.gettempdir()) / f"taky-failure-ledger-test-{uuid.uuid4().hex}.jsonl"
TEST_STATE_DIR = Path(tempfile.gettempdir()) / f"taky-outcome-state-test-{uuid.uuid4().hex}"
TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)

def call(session_id, event, **extra):
    payload = {
        "session_id": session_id,
        "hook_event_name": event,
        "cwd": str(ROOT),
        **extra,
    }
    env = os.environ.copy()
    env["TAKY_FAILURE_LEDGER"] = str(TEST_LEDGER)
    env["TAKY_OUTCOME_STATE_DIR"] = str(TEST_STATE_DIR)
    env["TAKY_OUTCOME_STATE_TTL_DAYS"] = "1"
    env["TAKY_OUTCOME_STATE_MAX_FILES"] = "10"
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    stdout = proc.stdout.strip()
    return json.loads(stdout) if stdout else None

def expect(condition, message, failures):
    if not condition:
        failures.append(message)

def test_ui_gate(failures):
    sid = "ui-" + uuid.uuid4().hex
    start = call(sid, "UserPromptSubmit", prompt="확정 시안 기준으로 UI 구현하고 결과물까지 검증해")
    expect(start and start.get("hookSpecificOutput", {}).get("hookEventName") == "UserPromptSubmit",
           "UI prompt did not activate outcome context", failures)

    call(sid, "PostToolUse", tool_name="Edit", tool_input={"file_path": "src/App.tsx"})
    blocked = call(sid, "Stop")
    expect(blocked and blocked.get("decision") == "block",
           "UI change was allowed to stop without verification", failures)

    call(sid, "PostToolUse", tool_name="PowerShell",
         tool_input={"command": "npm run build"})
    call(sid, "PostToolUse", tool_name="mcp__playwright__browser_navigate",
         tool_input={"url": "http://localhost:3000"})
    still_blocked = call(sid, "Stop")
    expect(still_blocked and still_blocked.get("decision") == "block",
           "Browser navigation alone was incorrectly accepted as render verification", failures)

    call(sid, "PostToolUse", tool_name="mcp__playwright__browser_snapshot",
         tool_input={})
    passed = call(sid, "Stop")
    expect(passed is None, "UI gate did not clear after build + observed render evidence", failures)

def test_interaction_gate(failures):
    sid = "interaction-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="버튼 기능 구현하고 실제 동작까지 검증해")
    call(sid, "PostToolUse", tool_name="Edit", tool_input={"file_path": "src/Button.tsx"})
    call(sid, "PostToolUse", tool_name="PowerShell", tool_input={"command": "npm run build"})
    call(sid, "PostToolUse", tool_name="mcp__playwright__browser_snapshot", tool_input={})
    blocked = call(sid, "Stop")
    expect(blocked and blocked.get("decision") == "block",
           "Interactive UI passed without interaction evidence", failures)

    call(sid, "PostToolUse", tool_name="mcp__playwright__browser_click",
         tool_input={"ref": "button"})
    passed = call(sid, "Stop")
    expect(passed is None, "Interaction gate did not clear after click evidence", failures)

def test_revision_bound_verification(failures):
    sid = "revision-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="UI 구현하고 실제 결과까지 검증해")
    call(sid, "PostToolUse", tool_name="Edit", tool_input={"file_path": "src/App.tsx"})
    call(sid, "PostToolUse", tool_name="PowerShell", tool_input={"command": "npm run build"})
    call(sid, "PostToolUse", tool_name="mcp__playwright__browser_snapshot", tool_input={})
    passed = call(sid, "Stop")
    expect(passed is None, "Initial verified UI did not pass", failures)

    # A later edit must invalidate the earlier build/render evidence.
    call(sid, "PostToolUse", tool_name="Edit", tool_input={"file_path": "src/App.tsx"})
    blocked = call(sid, "Stop")
    expect(blocked and blocked.get("decision") == "block",
           "Post-verification edit incorrectly inherited the earlier PASS", failures)

def test_asset_gate(failures):
    sid = "asset-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="승인 원화 기준으로 이미지 에셋 제작해")
    call(sid, "PostToolUse", tool_name="Write", tool_input={"file_path": "asset.png"})
    blocked = call(sid, "Stop")
    expect(blocked and blocked.get("decision") == "block",
           "Asset change was allowed to stop without verification", failures)

    call(sid, "PostToolUse", tool_name="PowerShell",
         tool_input={"command": "Get-FileHash asset.png; magick identify asset.png"})
    passed = call(sid, "Stop")
    expect(passed is None, "Asset gate did not clear after hash/dimension evidence", failures)

def test_repeated_failure_gate(failures):
    sid = "fail-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="UI 구현하고 검증까지 해")
    action = {"command": "npm run build"}

    call(sid, "PostToolUse", tool_name="PowerShell", tool_input=action,
         tool_response="Process completed with exit code 1: build failed")
    second = call(sid, "PostToolUse", tool_name="PowerShell", tool_input=action,
                  tool_response="Process completed with exit code 1: build failed")
    expect(second and second.get("hookSpecificOutput", {}).get("hookEventName") == "PostToolUse",
           "Repeated failure did not trigger route-switch guidance", failures)

    denied = call(sid, "PreToolUse", tool_name="PowerShell", tool_input=action)
    decision = (denied or {}).get("hookSpecificOutput", {}).get("permissionDecision")
    expect(decision == "deny", "Third unchanged attempt was not denied", failures)

    alternate = call(sid, "PreToolUse", tool_name="PowerShell",
                     tool_input={"command": "npm run typecheck"})
    expect(alternate is None, "Materially different recovery route was incorrectly denied", failures)

def test_post_tool_use_failure_event(failures):
    sid = "failure-event-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="UI 구현하고 검증까지 해")
    action = {"command": "npm run build"}

    first = call(
        sid, "PostToolUseFailure", tool_name="PowerShell", tool_input=action,
        error="Exit code 1\nError: build failed",
    )
    expect(first is None, "First PostToolUseFailure should be recorded without forcing a reroute", failures)

    second = call(
        sid, "PostToolUseFailure", tool_name="PowerShell", tool_input=action,
        error="Exit code 1\nError: build failed",
    )
    event_name = (second or {}).get("hookSpecificOutput", {}).get("hookEventName")
    expect(event_name == "PostToolUseFailure",
           "Repeated PostToolUseFailure did not inject route-switch guidance", failures)

    denied = call(sid, "PreToolUse", tool_name="PowerShell", tool_input=action)
    decision = (denied or {}).get("hookSpecificOutput", {}).get("permissionDecision")
    expect(decision == "deny", "PostToolUseFailure history did not deny the third unchanged attempt", failures)


def test_stop_failure_persists_repeated_failure_memory(failures):
    sid = "stop-failure-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="코드 작업하고 검증해")
    call(
        sid, "StopFailure", error="rate_limit",
        error_details="429 Too Many Requests",
        last_assistant_message="API Error: Rate limit reached",
    )
    call(
        sid, "StopFailure", error="rate_limit",
        error_details="429 Too Many Requests",
        last_assistant_message="API Error: Rate limit reached",
    )

    sid2 = "stop-failure-recall-" + uuid.uuid4().hex
    recalled = call(sid2, "UserPromptSubmit", prompt="코드 작업 이어서 진행해")
    context = (recalled or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
    expect("Recent unresolved repeated-failure routes" in context,
           "Repeated StopFailure was not recalled on the next turn/session", failures)
    expect("429 Too Many Requests" not in context,
           "StopFailure durable memory leaked raw API error details", failures)


def test_cross_session_failure_memory(failures):
    sid1 = "memory-a-" + uuid.uuid4().hex
    action = {"command": "npm run build"}
    call(sid1, "UserPromptSubmit", prompt="UI 구현하고 검증해")
    call(sid1, "PostToolUse", tool_name="PowerShell", tool_input=action,
         tool_response="Process completed with exit code 1: build failed")
    call(sid1, "PostToolUse", tool_name="PowerShell", tool_input=action,
         tool_response="Process completed with exit code 1: build failed")

    sid2 = "memory-b-" + uuid.uuid4().hex
    recalled = call(sid2, "UserPromptSubmit", prompt="UI 작업 이어서 개선해")
    context = (recalled or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
    expect("Recent unresolved repeated-failure routes" in context,
           "Repeated failure was not recalled in a new session", failures)
    expect("npm run build" not in context,
           "Persistent failure memory leaked full command arguments", failures)

def test_failed_verification_not_counted(failures):
    sid = "verify-fail-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="UI 수정하고 실제 결과까지 검증해")
    call(sid, "PostToolUse", tool_name="Edit", tool_input={"file_path": "src/App.tsx"})
    call(sid, "PostToolUse", tool_name="PowerShell",
         tool_input={"command": "npm run build"},
         tool_response="Process completed with exit code 1: command failed")
    blocked = call(sid, "Stop")
    expect(blocked and blocked.get("decision") == "block",
           "Failed build was incorrectly counted as verification", failures)

def test_durable_bounded_state(failures):
    sid = "durable-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="민감한 원문은 저장하지 말고 UI 구현해")
    files = list(TEST_STATE_DIR.glob("*.json"))
    expect(bool(files), "Durable outcome state was not persisted", failures)
    if files:
        payload = json.loads(files[-1].read_text(encoding="utf-8"))
        expect("prompt_excerpt" not in payload, "Durable outcome state retained prompt text", failures)
        expect("updated_at" in payload, "Durable outcome state lacks update timestamp", failures)

    old = TEST_STATE_DIR / "old-expired.json"
    old.write_text("{}", encoding="utf-8")
    os.utime(old, (1, 1))
    call("cleanup-"+uuid.uuid4().hex, "UserPromptSubmit", prompt="UI 구현해")
    expect(not old.exists(), "Expired durable outcome state was not cleaned", failures)

def test_non_material(failures):
    sid = "plain-" + uuid.uuid4().hex
    call(sid, "UserPromptSubmit", prompt="git status 보여줘")
    passed = call(sid, "Stop")
    expect(passed is None, "Non-material task was incorrectly blocked", failures)

def main():
    failures = []
    test_ui_gate(failures)
    test_interaction_gate(failures)
    test_revision_bound_verification(failures)
    test_asset_gate(failures)
    test_repeated_failure_gate(failures)
    test_post_tool_use_failure_event(failures)
    test_stop_failure_persists_repeated_failure_memory(failures)
    test_cross_session_failure_memory(failures)
    test_failed_verification_not_counted(failures)
    test_durable_bounded_state(failures)
    test_non_material(failures)
    if failures:
        print("FAIL: " + " | ".join(failures))
        return 1
    print("PASS: TAKY outcome hook UI/asset/non-material regression")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
