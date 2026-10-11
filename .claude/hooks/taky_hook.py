import json
import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sys

raw_stdin = sys.stdin.buffer.read()
data = json.loads(raw_stdin.decode("utf-8-sig", errors="replace")) if raw_stdin else {}
event = data.get("hook_event_name", "")

# Context pressure is written by Claude statusline and consumed here.
# This is shepherding: reroute to smaller context; never dead-end execution.
try:
    _repo_root = Path(__file__).resolve().parents[2]
    _enforcement_dir = _repo_root / "ENFORCEMENT"
    if str(_enforcement_dir) not in sys.path:
        sys.path.insert(0, str(_enforcement_dir))
    from claude_context_pressure import read_fresh_state, guidance_for
except Exception:
    read_fresh_state = lambda **_: {}
    guidance_for = lambda *_args, **_kwargs: ""

def _context_pressure_guidance():
    try:
        state = read_fresh_state()
        mode = state.get("mode")
        pct = state.get("used_percentage")
        if mode in {"LIGHT", "COMPACT"}:
            return guidance_for(mode, pct) + " Use the taky-context-manager skill when available."
    except Exception:
        pass
    return ""


COST_MAX_EXTERNAL_MODEL_CALLS = max(0, int(os.environ.get("TAKY_MAX_EXTERNAL_MODEL_CALLS_PER_PROMPT") or 1))
COST_MAX_REMOTE_CALLS = max(1, int(os.environ.get("TAKY_MAX_REMOTE_CALLS_PER_PROMPT") or 3))

def _session_key():
    seed = str(
        data.get("session_id")
        or data.get("transcript_path")
        or data.get("cwd")
        or "taky-default"
    )
    return hashlib.sha256(seed.encode("utf-8", "ignore")).hexdigest()[:20]

def _cached_remote_limit(default_limit):
    p = Path.home() / "TAKY_TMP" / "runtime-log" / "remote-usage.json"
    try:
        item = json.loads(p.read_text(encoding="utf-8"))
        pct = item.get("remaining_pct")
        checked = item.get("checked_at")
        if not isinstance(pct, (int, float)):
            return default_limit, None
        # Stale cache is display-only; do not tighten execution from old quota data.
        if isinstance(checked, str):
            try:
                ts = datetime.fromisoformat(checked.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
                if age > 21600:
                    return default_limit, pct
            except Exception:
                pass
        if pct <= 10:
            return min(default_limit, 1), pct
        if pct <= 25:
            return min(default_limit, 2), pct
        return default_limit, pct
    except Exception:
        return default_limit, None

def _cost_state_path():
    d = Path.home() / ".claude" / "taky" / "cost-gate-state"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_session_key()}.json"

def _load_cost_state():
    p = _cost_state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_cost_state(state):
    p = _cost_state_path()
    state = dict(state)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)

def _emit_prompt_context(text):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text,
        }
    }, ensure_ascii=False))

def _cost_class(tool_name, input_data):
    command = str(input_data.get("command") or input_data.get("cmd") or "")
    hay = (tool_name + " " + command).lower()
    if "remote_desktop_commander" in tool_name.lower():
        return "REMOTE"
    if re.search(r"(^|\s)(codex)(\.exe)?\s+exec\b", command, re.I):
        return "EXTERNAL_MODEL"
    if re.search(r"(^|\s)(gemini)(\.exe)?\b", command, re.I):
        return "EXTERNAL_MODEL"
    if re.search(r"(^|\s)(claude)(\.exe)?\s+(-p|--print)\b", command, re.I):
        return "EXTERNAL_MODEL"
    if tool_name.lower() in {
        "mcp__scenario__model_run",
        "mcp__scenario__workflow_run",
    }:
        return "EXTERNAL_MODEL"
    return ""

# Minimal lifecycle continuity receipt. This never stores session content, raw IDs, or paths,
# and failure here must never block Claude Code execution.
if event in {"SessionStart", "PreCompact"}:
    try:
        repo_root = Path(__file__).resolve().parents[2]
        enforcement_dir = repo_root / "ENFORCEMENT"
        if str(enforcement_dir) not in sys.path:
            sys.path.insert(0, str(enforcement_dir))
        from claude_lifecycle_receipt import persist_receipt
        persist_receipt(data)
    except Exception:
        pass

if event == "UserPromptSubmit":
    state = {
        "schema": "TAKY_COST_DRY_RUN_V1",
        "external_model_calls": 0,
        "remote_calls": 0,
        "max_external_model_calls": COST_MAX_EXTERNAL_MODEL_CALLS,
        "max_remote_calls": _cached_remote_limit(COST_MAX_REMOTE_CALLS)[0],
        "dry_run_plan": {
            "necessity_first": True,
            "reuse_first": True,
            "local_first": True,
            "batch_required": True,
            "retry_same_path": False,
            "fallback": "HOLD_OR_REROUTE",
        },
    }
    remote_limit, remote_pct = _cached_remote_limit(COST_MAX_REMOTE_CALLS)
    state["max_remote_calls"] = remote_limit
    state["remote_remaining_pct"] = remote_pct
    _save_cost_state(state)
    pressure = _context_pressure_guidance()
    context_text = (
        "TAKY DRY_RUN_PLAN active: NECESSITY -> REUSE -> LOCAL -> LOWEST SUFFICIENT -> "
        f"BATCH. Additional external-model calls budget={COST_MAX_EXTERNAL_MODEL_CALLS}; "
        f"Remote MCP budget={COST_MAX_REMOTE_CALLS}. Batch related reads/actions before executing. "
        "If the bounded budget is insufficient, reroute/reuse or report HOLD instead of silently multiplying calls."
    )
    if pressure:
        context_text += " " + pressure
    _emit_prompt_context(context_text)
    sys.exit(0)

if event == "SessionStart":
    msg = "TAKY runtime: THINK AGAIN -> KEEP YOUR KEY -> FIND A WAY -> YOU'RE THE KEY -> VERIFY/CORRECT/CONTINUE. Use the smallest sufficient context and execution path. Recover useful prior context with Claude-Mem when available, but MEMORY IS A ROUTING AID, NOT AUTHORITY; verify against CURRENT/owner before acting. For GROW, resolve DOMAIN/GROW_DOMAIN_REGISTRY.json -> shared_core.current_index before interpreting any older open/next field. Do not make the user repeat recoverable decisions or act as debugger. For material design/results, produce the actual integrated artifact/runtime, inspect it, correct material deltas, and distinguish IMPLEMENTED from VERIFIED. Claude is executor, TAKY owns authority; SAVEY prefers subscription/local paths and requires human approval for paid API, production deploy, push, merge, or irreversible actions. USER != DEBUGGER."
    key_names = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"]
    active_keys = [name for name in key_names if os.environ.get(name)]
    if active_keys:
        msg += " SAVEY WARNING: provider API key(s) are active in this shell: " + ", ".join(active_keys) + ". Do not use them as fallback."
    pressure = _context_pressure_guidance()
    if pressure:
        msg += " " + pressure
    root = Path(data.get("cwd") or ".")
    skill_dir = root / ".claude" / "skills"
    if skill_dir.exists() and len(list(skill_dir.glob("netlify-*"))) > 1:
        msg += " REGRESSION WARNING: multiple Netlify auto-skills reappeared; route through netlify-router and archive extras."
    print(msg)
    sys.exit(0)

tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}

cost_state = _load_cost_state()
cost_class = _cost_class(tool, tool_input)
if event == "PreToolUse" and cost_class and not cost_state:
    # Existing Claude sessions may have loaded hook registrations before the
    # UserPromptSubmit cost hook was added. Fail-safe by creating the bounded
    # budget on the first costly tool event instead of leaving the route open.
    cost_state = {
        "schema": "TAKY_COST_DRY_RUN_V1",
        "external_model_calls": 0,
        "remote_calls": 0,
        "max_external_model_calls": COST_MAX_EXTERNAL_MODEL_CALLS,
        "max_remote_calls": _cached_remote_limit(COST_MAX_REMOTE_CALLS)[0],
        "dry_run_plan": {
            "necessity_first": True,
            "reuse_first": True,
            "local_first": True,
            "batch_required": True,
            "retry_same_path": False,
            "fallback": "HOLD_OR_REROUTE",
        },
        "bootstrap": "PRETOOL_EXISTING_SESSION_FAILSAFE",
    }
    _save_cost_state(cost_state)
if event == "PreToolUse" and cost_class and cost_state:
    if cost_class == "EXTERNAL_MODEL":
        used = int(cost_state.get("external_model_calls", 0))
        limit = int(cost_state.get("max_external_model_calls", COST_MAX_EXTERNAL_MODEL_CALLS))
        if used >= limit:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason":
                        "TAKY REROUTE_REQUIRED (non-terminal): external-model call budget exhausted for the current bounded DRY_RUN_PLAN. "
                        "Reuse current evidence/context, batch the review request, use local deterministic verification, "
                        "or HOLD/REROUTE. Do not multiply reviewer/model calls."
                }
            }, ensure_ascii=False))
            sys.exit(0)
        cost_state["external_model_calls"] = used + 1
        _save_cost_state(cost_state)
    elif cost_class == "REMOTE":
        used = int(cost_state.get("remote_calls", 0))
        limit = int(cost_state.get("max_remote_calls", COST_MAX_REMOTE_CALLS))
        if used >= limit:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason":
                        "TAKY REROUTE_REQUIRED (non-terminal): Remote MCP DRY_RUN_PLAN budget exhausted for the current route. "
                        "Batch related reads/commands into one remote process, reuse collected evidence, "
                        "or HOLD/REROUTE instead of issuing another fragmented remote call."
                }
            }, ensure_ascii=False))
            sys.exit(0)
        cost_state["remote_calls"] = used + 1
        _save_cost_state(cost_state)

def decide(kind, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason
        }
    }, ensure_ascii=False))
    sys.exit(0)

raw_path = str(tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path") or "")
cwd = Path(data.get("cwd") or ".").resolve()
try:
    resolved_path = Path(raw_path)
    if raw_path and not resolved_path.is_absolute():
        resolved_path = cwd / resolved_path
    path = str(resolved_path.resolve()).replace("\\", "/").lower()
except Exception:
    path = raw_path.replace("\\", "/").lower()

protected_authority_paths = ["/taky.md", "/master/", "/.claude/settings", "/.mcp.json", "/.claude/hooks/", "/agents.md", "/claude.md"]

if tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
    if "/.git/" in path or path.endswith("/.git"):
        decide("deny", "TAKY hard gate: direct edits inside .git are prohibited.")
    if any(x in path for x in ["/.env", "credentials", "secret", "token.json"]):
        decide("deny", "TAKY hard gate: credential/secret files must not be edited by the agent.")
    if any(x in path for x in protected_authority_paths):
        decide("ask", "TAKY authority/config change: user approval is required before modifying this file.")

if tool in {"Read", "Grep"} and any(x in path for x in ["/.env", "credentials", "secret", "token.json", "/.ssh/", "/.aws/"]):
    decide("ask", "TAKY secret-read gate: explicit user approval is required before reading credential or secret material.")

command = str(tool_input.get("command") or tool_input.get("cmd") or "")
haystack = (tool + " " + command + " " + json.dumps(tool_input, ensure_ascii=False)).lower()
command_lower = command.lower()
command_path_text = command_lower.replace("\\", "/")

if tool in {"Bash", "PowerShell"}:
    protected_shell_markers = [
        "taky.md", "agents.md", "claude.md", ".mcp.json",
        ".claude/settings", ".claude/hooks/", "master/",
    ]
    shell_secret_patterns = [
        r"(^|[/\s'\"=])\.env($|[/\s'\".;])",
        r"credentials", r"token\.json", r"id_rsa", r"/\.ssh/", r"/\.aws/",
    ]
    if any(re.search(p, command_path_text, re.I) for p in shell_secret_patterns):
        decide("ask", "TAKY secret shell-access gate: explicit user approval is required before shell access to credential or secret material.")

    if any(marker in command_path_text for marker in protected_shell_markers):
        read_only_patterns = [
            r"^\s*git\s+(status|diff|log|show|branch|rev-parse)\b",
            r"^\s*(rg|grep|findstr|select-string)\b",
            r"^\s*(cat|type|get-content|gc|more|less|head|tail)\b",
        ]
        shell_compound_or_expansion = bool(
            re.search(r"[;&|><\r\n]|\$\(|`", command, re.I)
        )
        recognized_single_read = any(
            re.search(p, command_lower, re.I) for p in read_only_patterns
        )
        if shell_compound_or_expansion or not recognized_single_read:
            decide("ask", "TAKY authority/config shell gate: protected governance/config reads must be a single read-only command with no chaining, redirection, pipeline, or command substitution; explicit user approval is required otherwise.")

ask_patterns = [
    r"\bgit\s+push\b", r"\bgh\s+pr\s+merge\b", r"\bgh\s+release\s+create\b",
    r"\bnetlify\s+deploy\b.*--prod", r"\bnetlify\s+deploy\b.*\bprod\b",
    r"\bnpm\s+publish\b", r"\bgit\s+reset\s+--hard\b", r"\bgit\s+clean\s+-[^\s]*f",
    r"\bgit\s+branch\s+-d\b", r"\brm\s+-rf\b", r"\bremove-item\b.*-recurse.*-force",
    r"\bopenai\s+", r"api\.openai\.com", r"api\.anthropic\.com",
    r"openai_api_key", r"anthropic_api_key", r"gemini_api_key", r"google_api_key",
    r"\b(cat|type|get-content|gc|more|less|head|tail|cp|copy|copy-item|scp)\b[^|;&]*(/|\\|\s)\.env\b",
    r"\b(cat|type|get-content|gc|more|less|head|tail|cp|copy|copy-item|scp)\b[^|;&]*(credentials|token\.json|id_rsa)",
    r"\b(set-content|out-file|add-content|copy-item|move-item|remove-item|del|erase)\b[^|;&]*(taky\.md|agents\.md|claude\.md|\.mcp\.json|\.claude[/\\](settings|hooks)|master[/\\])"
]
if any(re.search(p, haystack, re.I | re.S) for p in ask_patterns):
    decide("ask", "TAKY/SAVEY gate: this action can publish, destroy, spend API money, or change remote state. Explicit user approval is required.")

if "netlify" in tool.lower() and any(x in haystack for x in ["deploy", "publish", "production", "prod"]):
    decide("ask", "TAKY deploy gate: Netlify production/publish actions require explicit user approval.")

if "github" in tool.lower() and any(x in haystack for x in ["merge", "delete", "release", "force"]):
    decide("ask", "TAKY GitHub gate: merge/delete/release/force actions require explicit user approval.")

if tool.lower() in {"mcp__scenario__model_run", "mcp__scenario__workflow_run",
                    "mcp__scenario__scenario_tool_execute_write", "mcp__scenario__scenario_tool_execute_delete"}:
    decide("ask", "TAKY/SAVEY cost gate: Scenario generation/workflow/write actions require explicit user approval.")

# Generic MCP high-impact gate. Inspect control/action fields and tool identity, not arbitrary page/document text.
if tool.lower().startswith("mcp__"):
    control_keys = ("action", "operation", "mode", "permission", "role", "visibility", "scope", "command")
    control_values = [str(tool_input.get(k) or "") for k in control_keys if k in tool_input]
    mcp_control_text = (tool + " " + " ".join(control_values)).lower()
    high_impact_terms = [
        "delete", "trash", "purge", "remove_member", "revoke", "share", "permission",
        "invite", "publish", "deploy", "release", "merge", "force", "send_email",
        "send_message", "post_message", "account", "credential", "secret", "billing", "payment"
    ]
    if any(term in mcp_control_text for term in high_impact_terms):
        decide("ask", "TAKY connection-security gate: this MCP action may delete, publish/share, change access/account state, communicate externally, or create financial impact. Explicit user approval is required.")

sys.exit(0)
