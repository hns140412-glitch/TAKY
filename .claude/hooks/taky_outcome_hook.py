#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

raw_stdin = sys.stdin.buffer.read()
data = json.loads(raw_stdin.decode("utf-8-sig", errors="replace")) if raw_stdin else {}
event = data.get("hook_event_name", "")
session_seed = str(
    data.get("session_id")
    or data.get("transcript_path")
    or data.get("cwd")
    or "taky-default"
)
session_key = hashlib.sha256(session_seed.encode("utf-8", "ignore")).hexdigest()[:20]
learning_dir = Path.home() / ".claude" / "taky"
state_dir = Path(os.environ.get("TAKY_OUTCOME_STATE_DIR") or (learning_dir / "outcome-gate-state"))
state_dir.mkdir(parents=True, exist_ok=True)
state_path = state_dir / f"{session_key}.json"

STATE_TTL_DAYS = max(1, int(os.environ.get("TAKY_OUTCOME_STATE_TTL_DAYS") or 14))
STATE_MAX_FILES = max(10, int(os.environ.get("TAKY_OUTCOME_STATE_MAX_FILES") or 120))

def cleanup_state_dir():
    try:
        now = time.time()
        files = [p for p in state_dir.glob("*.json") if p.is_file()]
        for p in files:
            try:
                if now - p.stat().st_mtime > STATE_TTL_DAYS * 86400:
                    p.unlink(missing_ok=True)
            except Exception:
                pass
        files = sorted(
            [p for p in state_dir.glob("*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for p in files[STATE_MAX_FILES:]:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass

cleanup_state_dir()

learning_dir.mkdir(parents=True, exist_ok=True)
failure_ledger = Path(os.environ.get("TAKY_FAILURE_LEDGER") or (learning_dir / "failure-learning.jsonl"))
failure_ledger.parent.mkdir(parents=True, exist_ok=True)

def project_key():
    raw = str(data.get("cwd") or "").replace("\\", "/").lower()
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16]

DESIGN_WORDS = {
    "design", "ui", "ux", "visual", "mockup", "screen", "layout", "asset",
    "image", "illustration", "presentation", "artifact", "render",
    "디자인", "시안", "화면", "비주얼", "에셋", "이미지", "일러스트",
    "문서", "발표", "결과물", "렌더", "구현", "제작", "만들", "개선", "보완",
}
MATERIAL_WORDS = DESIGN_WORDS | {
    "implement", "build", "fix", "refactor", "code", "app", "pwa", "feature",
    "report", "document", "ppt", "pptx", "pdf", "docx", "xlsx",
    "기능", "코드", "앱", "보고서", "자료", "수정", "완성", "적용", "연동",
}
INTERACTION_WORDS = {
    "interaction", "interactive", "click", "tap", "button", "flow", "navigation", "input",
    "form", "modal", "dialog", "toggle", "drag", "swipe", "function", "feature",
    "상호작용", "클릭", "터치", "버튼", "동작", "기능", "전환", "입력", "폼", "모달",
    "토글", "드래그", "스와이프", "네비게이션", "흐름", "플로우",
}
UI_EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx",
           ".ts", ".tsx", ".vue", ".svelte"}
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".ico"}
ARTIFACT_EXTS = {".pdf", ".pptx", ".docx", ".xlsx", ".xlsm"}
CODE_EXTS = UI_EXTS | {".py", ".ps1", ".sh", ".json", ".yaml", ".yml"}

def load_state():
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_state(state):
    state = dict(state)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = state_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(state_path)

def prompt_value():
    for key in ("prompt", "user_prompt", "message"):
        value = data.get(key)
        if isinstance(value, str):
            return value
    return ""
def tool_path(tool_input):
    if not isinstance(tool_input, dict):
        return ""
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""

def add_unique(state, key, value):
    items = state.setdefault(key, [])
    if value and value not in items:
        items.append(value)
        del items[40:]

def emit_context(hook_event, text):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "additionalContext": text,
        }
    }, ensure_ascii=False))

def action_signature(tool, tool_input):
    raw = json.dumps({"tool": tool, "input": tool_input}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:24]

def response_text():
    value = data.get("tool_response")
    if value is None:
        value = data.get("tool_result")
    if value is None:
        value = data.get("response")
    if value is None and isinstance(data.get("error"), str):
        parts = [
            data.get("error"),
            data.get("error_details"),
            data.get("last_assistant_message"),
        ]
        return "\n".join(str(part) for part in parts if part)
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(value)

def response_failed(text):
    if not text:
        return False
    lower = text.lower()
    hard = (
        '"is_error": true', '"success": false', '"error":', "traceback (most recent call last)",
        "permission denied", "access is denied", "fatal error", "process completed with exit code 1",
        "process completed with exit code 2", "command failed", "enoent", "eperm"
    )
    return any(x in lower for x in hard)

def classify_failure(text):
    lower = (text or "").lower().replace("_", " ")
    if any(x in lower for x in (
        "permission denied", "access is denied", "eperm", "unauthorized", "forbidden",
        "authentication failed", "oauth org not allowed", "account on hold",
    )):
        return "ACCESS"
    if any(x in lower for x in ("module not found", "package not found", "command not found", "dependency", "missing module")):
        return "DEPENDENCY"
    if any(x in lower for x in ("enoent", "no such file", "not found", "invalid path", "cannot find path", "invalid request")):
        return "INPUT"
    if any(x in lower for x in ("rate limit", "quota", "billing", "payment", "credits", "usage limit")):
        return "COST"
    if any(x in lower for x in ("approval", "requires explicit user", "authority", "not authorized")):
        return "AUTHORITY"
    if any(x in lower for x in (
        "port", "address already in use", "connection refused", "timeout", "timed out",
        "environment", "overloaded", "server error", "cloud credential error",
    )):
        return "ENVIRONMENT"
    if any(x in lower for x in ("exit code", "traceback", "fatal error", "command failed", '"error":')):
        return "RUNTIME"
    return "UNKNOWN"

def action_label(tool, tool_input):
    if not isinstance(tool_input, dict):
        return tool
    path = tool_path(tool_input)
    if path:
        return f"{tool}:{Path(path).name}"
    command = str(tool_input.get("command") or tool_input.get("cmd") or "").strip()
    if command:
        # Persistent learning must not retain command arguments, paths, tokens, or secrets.
        executable = command.split()[0] if command.split() else "command"
        executable = Path(executable.strip("'\"")).name or "command"
        return f"{tool}:{executable[:80]}"
    return tool

def append_failure_event(kind, state, tool="", tool_input=None, cause="", failed_sig="", new_sig=""):
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "project": project_key(),
        "session": session_key,
        "kind": kind,
        "cause": cause,
        "failed_sig": failed_sig,
        "new_sig": new_sig,
        "action": action_label(tool, tool_input or {}),
        "error_fingerprint": hashlib.sha256(str(state.get("last_failure") or "").encode("utf-8", "ignore")).hexdigest()[:16],
    }
    with failure_ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def recent_unresolved_failures():
    if not failure_ledger.exists():
        return []
    try:
        lines = failure_ledger.read_text(encoding="utf-8").splitlines()[-300:]
    except Exception:
        return []
    events = []
    for line in lines:
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("project") == project_key():
            events.append(rec)
    resolved = {rec.get("failed_sig") for rec in events if rec.get("kind") == "RECOVERY_ROUTE"}
    seen = set()
    result = []
    for rec in reversed(events):
        if rec.get("kind") != "REPEATED_FAILURE":
            continue
        sig = rec.get("failed_sig")
        if not sig or sig in resolved or sig in seen:
            continue
        seen.add(sig)
        result.append({"cause": rec.get("cause", "UNKNOWN"), "action": rec.get("action", ""), "sig": sig})
        if len(result) >= 3:
            break
    return result

def deny_repeat(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))

def block_stop(reason):
    sys.stderr.write(reason)
    sys.stderr.flush()
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "rewakeSummary": "TAKY 결과 검증 게이트",
    }, ensure_ascii=False))

if event == "UserPromptSubmit":
    prompt = prompt_value()
    lower = prompt.lower()
    design = any(word in lower for word in DESIGN_WORDS)
    material = design or any(word in lower for word in MATERIAL_WORDS)
    interaction_expected = any(word in lower for word in INTERACTION_WORDS)
    state = {
        "design_intent": design,
        "material_intent": material,
        "interaction_expected": interaction_expected,
        "touched_ui": [],
        "touched_asset": [],
        "touched_artifact": [],
        "touched_code": [],
        "browser_verified": False,
        "browser_render_verified": False,
        "browser_interaction_verified": False,
        "code_verified": False,
        "asset_verified": False,
        "artifact_observed": False,
        "stop_blocks": 0,
        "failure_counts": {},
        "stop_failure_counts": {},
        "last_failure": "",
        "last_failed_sig": "",
        "last_failure_cause": "",
        "route_switch_required": False,
    }
    save_state(state)
    if material:
        prior = recent_unresolved_failures()
        prior_text = ""
        if prior:
            prior_text = " Recent unresolved repeated-failure routes: " + "; ".join(
                f"{item['cause']}:{item['action']}[{item['sig']}]" for item in prior
            ) + ". Do not repeat them unchanged."
        emit_context(
            "UserPromptSubmit",
            "TAKY Outcome Gate active. Execute HUMAN INTENT -> THINK AGAIN -> KEEP YOUR KEY -> "
            "FIND A WAY/SOLVE -> YOU'RE THE KEY -> VERIFY/CORRECT/CONTINUE. "
            "Recover approved/current context before redesigning; produce the actual result, inspect the integrated "
            "output, correct material deltas, and do not make the user the debugger. "
            "Memory may recover context but is not authority." + prior_text
        )
    sys.exit(0)

if event == "PreToolUse":
    state = load_state()
    if not state:
        sys.exit(0)
    tool = str(data.get("tool_name") or "")
    tool_input = data.get("tool_input") or {}
    sig = action_signature(tool, tool_input)
    failures = state.get("failure_counts") or {}
    if int(failures.get(sig, 0)) >= 2:
        deny_repeat(
            "TAKY Anti-Loop Gate: the same action has already failed twice. "
            "Do not repeat it unchanged. Classify the failure cause, change the execution path/tool/input, "
            "or gather new evidence first. USER != DEBUGGER."
        )
    sys.exit(0)

if event in {"PostToolUse", "PostToolUseFailure"}:
    state = load_state()
    tool = str(data.get("tool_name") or "")
    tool_lower = tool.lower()
    tool_input = data.get("tool_input") or {}
    path = tool_path(tool_input)
    suffix = Path(path).suffix.lower() if path else ""
    result_text = response_text()
    failed = event == "PostToolUseFailure" or response_failed(result_text)

    if tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        if suffix in UI_EXTS:
            add_unique(state, "touched_ui", path)
            # Any post-verification UI edit invalidates previous render/interaction evidence.
            state["browser_verified"] = False
            state["browser_render_verified"] = False
            state["browser_interaction_verified"] = False
            state["code_verified"] = False
        if suffix in ASSET_EXTS:
            add_unique(state, "touched_asset", path)
            state["asset_verified"] = False
        if suffix in ARTIFACT_EXTS:
            add_unique(state, "touched_artifact", path)
            state["artifact_observed"] = False
        if suffix in CODE_EXTS:
            add_unique(state, "touched_code", path)
            state["code_verified"] = False

    if not failed and any(token in tool_lower for token in ("playwright", "chrome-devtools", "browser", "screenshot")):
        render_tokens = ("screenshot", "snapshot", "dom", "accessibility", "evaluate", "inspect")
        interaction_tokens = ("click", "tap", "fill", "type", "press", "select", "hover", "drag", "swipe", "submit")
        if any(token in tool_lower for token in render_tokens):
            state["browser_render_verified"] = True
            state["browser_verified"] = True
        if any(token in tool_lower for token in interaction_tokens):
            state["browser_interaction_verified"] = True

    command = str(tool_input.get("command") or tool_input.get("cmd") or "").lower()
    if not failed and re.search(r"(npm|pnpm|yarn|bun)\s+(run\s+)?(build|test|lint|typecheck)|pytest|vitest|jest|playwright\s+test|tsc\b", command):
        state["code_verified"] = True
    if not failed and re.search(r"get-filehash|sha256|certutil.+hashfile|magick\s+identify|identify\s+|ffprobe|dimensions?|image\.open", command):
        state["asset_verified"] = True
    if not failed and tool in {"Read", "Grep"} and suffix in ARTIFACT_EXTS:
        state["artifact_observed"] = True
    if not failed and any(token in tool_lower for token in ("pdf", "ppt", "slide", "document", "spreadsheet")) and "read" in tool_lower:
        state["artifact_observed"] = True

    sig = action_signature(tool, tool_input)
    failures = state.setdefault("failure_counts", {})
    if failed:
        failures[sig] = int(failures.get(sig, 0)) + 1
        state["last_failure"] = result_text[-800:]
        state["last_failed_sig"] = sig
        state["last_failure_cause"] = classify_failure(result_text)
        if failures[sig] >= 2:
            state["route_switch_required"] = True
            append_failure_event(
                "REPEATED_FAILURE", state, tool, tool_input,
                cause=state["last_failure_cause"], failed_sig=sig
            )
            save_state(state)
            emit_context(
                event,
                "TAKY Anti-Loop Gate: this exact action has failed repeatedly. "
                f"Classified cause: {state['last_failure_cause']}. "
                "STOP repeating the same path. Switch to a materially different route/tool/input, or isolate the root "
                "cause with new evidence. Ask the user only if a genuine human-only decision or permission is required."
            )
            sys.exit(0)
    else:
        if state.get("route_switch_required") and sig != state.get("last_failed_sig"):
            append_failure_event(
                "RECOVERY_ROUTE", state, tool, tool_input,
                cause=state.get("last_failure_cause", "UNKNOWN"),
                failed_sig=state.get("last_failed_sig", ""), new_sig=sig
            )
            state["route_switch_required"] = False
        failures.pop(sig, None)

    save_state(state)
    sys.exit(0)

if event == "StopFailure":
    state = load_state()
    if not state:
        sys.exit(0)
    error_type = str(data.get("error") or "unknown")
    result_text = response_text()
    cause = classify_failure(result_text or error_type)
    sig = action_signature("StopFailure", {"error": error_type})
    failures = state.setdefault("stop_failure_counts", {})
    failures[sig] = int(failures.get(sig, 0)) + 1
    state["last_failure"] = (result_text or error_type)[-800:]
    state["last_failed_sig"] = sig
    state["last_failure_cause"] = cause
    if failures[sig] >= 2:
        state["route_switch_required"] = True
        append_failure_event(
            "REPEATED_FAILURE", state, "StopFailure", {"error": error_type},
            cause=cause, failed_sig=sig
        )
    save_state(state)
    sys.exit(0)

if event == "Stop":
    if data.get("stop_hook_active"):
        sys.exit(0)

    state = load_state()
    if not state or not state.get("material_intent"):
        sys.exit(0)

    missing = []
    if state.get("touched_ui") and not state.get("browser_render_verified"):
        missing.append("actual UI/browser render evidence (screenshot/snapshot/DOM observation)")
    if state.get("touched_ui") and state.get("interaction_expected") and not state.get("browser_interaction_verified"):
        missing.append("actual interaction evidence for the required click/input/transition flow")
    if state.get("touched_code") and not state.get("code_verified"):
        missing.append("representative build/test/typecheck evidence")
    if state.get("touched_asset") and not state.get("asset_verified"):
        missing.append("asset existence/hash/dimension/format evidence")
    if state.get("touched_artifact") and not state.get("artifact_observed"):
        missing.append("generated artifact open/render inspection")

    if missing and int(state.get("stop_blocks", 0)) < 3:
        state["stop_blocks"] = int(state.get("stop_blocks", 0)) + 1
        attempt = int(state["stop_blocks"])
        save_state(state)
        if attempt == 1:
            action = "Run the smallest applicable verification and correct the material delta."
        elif attempt == 2:
            action = (
                "The first verification path did not close the gap. Classify the root cause and switch to a materially "
                "different route/tool/input; do not repeat the same failed action unchanged."
            )
        else:
            action = (
                "Escalate to independent verification/recovery. If the gap still cannot be closed, preserve failure "
                "evidence and finish as BLOCKED/HOLD or UNVERIFIED with the exact blocker; do not loop."
            )
        block_stop(
            "TAKY Outcome Gate: do not stop at implementation-only state. Missing: "
            + "; ".join(missing) + ". " + action
            + " USER != DEBUGGER."
        )
        sys.exit(0)
    if missing:
        # Avoid an infinite Stop loop. Three escalation passes are enough:
        # verify -> route switch/root cause -> independent recovery.
        # It may now stop only if it truthfully reports UNVERIFIED/BLOCKED/HOLD.
        sys.stderr.write(
            "TAKY Outcome Gate: verification is still incomplete. Final status must remain UNVERIFIED/BLOCKED/HOLD; "
            "do not claim VERIFIED/PASS.\n"
        )
        sys.stderr.flush()
    else:
        # Keep session state after a PASS. The user/model may continue editing in the same
        # session, and any later material edit must invalidate the affected evidence.
        state["stop_blocks"] = 0
        state["last_verified_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
    sys.exit(0)

sys.exit(0)
