import json
import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sys

# Claude Code reads hook stdout as UTF-8. Windows redirected Python stdout
# otherwise inherits a legacy code page and corrupts Korean user corrections.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

def _codex_plugin_operation(input_data):
    command = str(input_data.get("command") or input_data.get("cmd") or "")
    match = re.search(
        r"codex-companion\.mjs[\"']?\s+(review|adversarial-review|task|transfer)\b",
        command, re.I,
    )
    return match.group(1).lower() if match else ""


def _codex_plugin_model_call(input_data):
    return bool(_codex_plugin_operation(input_data))


def _signed_codex_verifier_health(cwd):
    """Read signed existing TAKY authority; never issue a model call or receipt."""
    try:
        root = Path(__file__).resolve().parents[2]
        tool_dir = root / "TOOLS"
        if str(tool_dir) not in sys.path:
            sys.path.insert(0, str(tool_dir))
        from TAKY_GOVERNED_ROUTE_HEALTH import signed_health
        return signed_health("Codex", str(Path(cwd or ".").resolve()))
    except Exception as exc:
        return {"status": "HOLD", "reason": "SIGNED_VERIFIER_PREFLIGHT_UNAVAILABLE",
                "reasonClass": type(exc).__name__}


def _is_explicit_task_continuation(prompt):
    value = str(prompt or "").strip().lower()
    if not value or len(value) > 180:
        return False
    if any(x in value for x in ("새로운 작업", "다른 작업", "new task", "switch project")):
        return False
    return bool(
        re.search(r"계속|이어서|쭉\s*진행|재검증|이어\s*진행", value)
        or re.fullmatch(r"(?:ㄱ|ㅇㅇ|계속|진행|go|continue|resume)[.! ]*", value)
    )


def _cost_class(tool_name, input_data):
    command = str(input_data.get("command") or input_data.get("cmd") or "")
    hay = (tool_name + " " + command).lower()
    if _codex_plugin_model_call(input_data):
        return "EXTERNAL_MODEL"
    # Count direct CLI/model-server launches before the generic remote-shell
    # accounting. Read-only codex login/status/version are excluded.
    if re.search(
        r"(?<![\w])codex(?:\.(?:exe|cmd|ps1))?[\"']?\s+(?:exec|app-server)\b",
        command, re.I,
    ):
        return "EXTERNAL_MODEL"
    if re.search(r"(?<![\w])gemini(?:\.(?:exe|cmd))?[\"']?\s+", command, re.I):
        return "EXTERNAL_MODEL"
    if re.search(
        r"(?<![\w])claude(?:\.(?:exe|cmd))?[\"']?\s+(?:-p|--print)\b",
        command, re.I,
    ):
        return "EXTERNAL_MODEL"
    if tool_name.lower() in {
        "mcp__scenario__model_run",
        "mcp__scenario__workflow_run",
    }:
        return "EXTERNAL_MODEL"
    if "remote_desktop_commander" in tool_name.lower():
        return "REMOTE"
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
    prior_cost = _load_cost_state()
    raw_prompt = data.get("prompt") or data.get("user_prompt") or data.get("message")
    continue_budget = (
        _is_explicit_task_continuation(raw_prompt)
        and prior_cost.get("schema") == "TAKY_COST_DRY_RUN_V1"
    )
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
    if continue_budget:
        # Reuse the existing bounded model/remote allocation on an explicit
        # same-session follow-up. A short "go" must not buy another model call.
        state["external_model_calls"] = max(0, int(prior_cost.get("external_model_calls", 0)))
        state["remote_calls"] = max(0, int(prior_cost.get("remote_calls", 0)))
        state["max_external_model_calls"] = min(
            COST_MAX_EXTERNAL_MODEL_CALLS,
            max(0, int(prior_cost.get("max_external_model_calls", COST_MAX_EXTERNAL_MODEL_CALLS)))
        )
        if prior_cost.get("remote_soft_notice_sent"):
            state["remote_soft_notice_sent"] = True
        if prior_cost.get("bootstrap"):
            state["bootstrap"] = prior_cost["bootstrap"]
    _save_cost_state(state)
    pressure = _context_pressure_guidance()
    context_text = (
        "TAKY DRY_RUN_PLAN active: NECESSITY -> REUSE -> LOCAL -> LOWEST SUFFICIENT -> "
        f"BATCH. Remaining external-model call allowance="
        f"{max(0, state['max_external_model_calls'] - state['external_model_calls'])}"
        f"/{state['max_external_model_calls']} for this bounded task; "
        f"Remote MCP batching preference={state['max_remote_calls']}. "
        "Batch related reads/actions before executing. "
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
    # Cross-session, project-scoped failure fingerprints; data only, never CURRENT authority.
    try:
        origin_cwd = str(data.get("cwd") or "")
        if origin_cwd:
            from failure_regression_bridge import recall_project_failures, format_project_failure_recall
            project_hash = hashlib.sha256(
                origin_cwd.replace("\\", "/").lower().encode("utf-8", "ignore")
            ).hexdigest()[:16]
            ledger = Path(os.environ.get("TAKY_FAILURE_LEDGER") or
                          (Path.home() / ".claude" / "taky" / "failure-learning.jsonl"))
            lessons = format_project_failure_recall(recall_project_failures(ledger, project_hash))
            if lessons:
                msg += "\n" + lessons
            # Reuse existing C2S event journals; records are candidate data, not owner rules.
            repo_root = Path(__file__).resolve().parents[2]
            if Path(origin_cwd).resolve().is_relative_to(repo_root):
                from failure_regression_bridge import (
                    recall_user_corrections, format_user_correction_recall
                )
                history_dir = Path(os.environ.get("TAKY_CONVERSATION_HISTORY_DIR") or
                                   r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")
                corrections = format_user_correction_recall(
                    recall_user_corrections(history_dir, "TAKY_SYSTEMWIDE")
                )
                if corrections:
                    msg += "\n" + corrections
    except Exception:
        pass
    print(msg)
    sys.exit(0)

tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}

cost_state = _load_cost_state()
cost_class = _cost_class(tool, tool_input)
remote_soft_guidance = ""

# Independent signed-route preflight for official Codex-for-Claude model calls.
# The existing Codex action is verifier-only; task/transfer cannot inherit its
# authority. This hook is one enforcement layer, not hosted ChatGPT interception.
if event == "PreToolUse":
    plugin_op = _codex_plugin_operation(tool_input)
    if plugin_op:
        reason = None
        if plugin_op not in {"review", "adversarial-review"}:
            reason = (
                "TAKY SHEPHERD: this plugin action is not an authorized "
                "verifier-only review. Keep Claude as implementation owner; "
                "use a scoped Codex review or obtain a distinct trusted "
                "Codex implementation/transfer authorization."
            )
        else:
            health = _signed_codex_verifier_health(data.get("cwd"))
            if health.get("status") != "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES":
                reason = (
                    "TAKY SHEPHERD: signed Codex verifier route is HOLD ("
                    + str(health.get("reason") or "SIGNED_PREFLIGHT_NOT_READY")[:100]
                    + "). Preserve work/context, use local deterministic checks "
                    "and recheck existing signed authority; never bypass the route gate."
                )
        if reason:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }, ensure_ascii=False))
            sys.exit(0)
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
        # Desktop Commander access is an already-connected local execution path,
        # not a new paid provider call. Its count is an efficiency hint, not an
        # authorization gate. Never short-circuit the security checks below.
        used = int(cost_state.get("remote_calls", 0))
        limit = int(cost_state.get("max_remote_calls", COST_MAX_REMOTE_CALLS))
        cost_state["remote_calls"] = used + 1
        if used >= limit and not cost_state.get("remote_soft_notice_sent"):
            remote_soft_guidance = (
                "TAKY SOFT ROUTE GUIDANCE: Desktop Commander call count exceeded "
                "the batching preference. Reuse/batch when practical, but continue "
                "the authorized task; the count itself is not a reason to stop. "
                "Credential, external publication, Git and protected-file gates "
                "still apply independently."
            )
            cost_state["remote_soft_notice_sent"] = True
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

# Claude MCP calls are also tool invocations, not automatically trusted.
# Treat a connected Desktop Commander file edit like a native Edit/Write;
# otherwise protected authority files can be changed by changing tool names.
remote_desktop_tool = tool.lower().startswith("mcp__remote_desktop_commander__")
remote_mutation = remote_desktop_tool and any(
    tool.lower().endswith("__" + operation)
    for operation in ("write_file", "edit_block", "move_file", "delete_file")
)
remote_read = remote_desktop_tool and tool.lower().endswith("__read_file")
remote_shell = remote_desktop_tool and tool.lower().endswith("__start_process")

if tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"} or remote_mutation:
    if "/.git/" in path or path.endswith("/.git"):
        decide("deny", "TAKY hard gate: direct edits inside .git are prohibited.")
    if any(x in path for x in ["/.env", "credentials", "secret", "token.json"]):
        decide("deny", "TAKY hard gate: credential/secret files must not be edited by the agent.")
    if any(x in path for x in protected_authority_paths):
        decide("ask", "TAKY authority/config change: user approval is required before modifying this file.")

if (tool in {"Read", "Grep"} or remote_read) and any(x in path for x in ["/.env", "credentials", "secret", "token.json", "/.ssh/", "/.aws/"]):
    decide("ask", "TAKY secret-read gate: explicit user approval is required before reading credential or secret material.")

command = str(tool_input.get("command") or tool_input.get("cmd") or "")
haystack = (tool + " " + command + " " + json.dumps(tool_input, ensure_ascii=False)).lower()
command_lower = command.lower()
command_path_text = command_lower.replace("\\", "/")

if tool in {"Bash", "PowerShell"} or remote_shell:
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

# Guard the real Git subcommand even when -C/-c/global options precede it.
# Pull/rebase/cherry-pick can merge or rewrite local history without saying "merge".
sensitive_git_command = (
    r"\bgit(?:\.exe)?(?:\s+(?:-C|-c|--git-dir|--work-tree)\s+"
    r"(?:'[^']+'|\"[^\"]+\"|\S+)|\s+--no-pager)*"
    r"\s+(?:push|pull|merge|rebase|cherry-pick)\b"
)
if (tool in {"Bash", "PowerShell"} or remote_shell) and re.search(sensitive_git_command, command, re.I | re.S):
    decide("ask", "TAKY Git operation approval gate: push, pull/merge, rebase and cherry-pick require explicit user approval.")

ask_patterns = [
    r"\bgit\s+push\b", r"\bgh\s+pr\s+merge\b", r"\bgh\s+release\s+create\b",
    r"\bnetlify\s+deploy\b",
    r"\bnetlify\s+(?:sites?:create|sites?:delete|env:set|env:unset)\b",
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

# A provider's read API can contain words like "release", "permission" or
# "deploy" in its noun. Distinguish the actual tool verb from those nouns.
# Only explicit, read-only endpoint names qualify. Mutating control fields
# invalidate the read classification even when the endpoint starts with get_.
def _mcp_read_only_operation(tool_name, arguments):
    parts = tool_name.lower().split("__")
    if len(parts) < 3 or parts[0] != "mcp":
        return False
    endpoint = parts[-1]
    if not re.match(
        r"^(get|list|search|find|read|fetch|inspect|describe|check|"
        r"retrieve|query|preview|lookup|view)_", endpoint
    ):
        return False
    if not isinstance(arguments, dict):
        return False
    change_words = re.compile(
        r"(?:^|[^a-z0-9])(delete|trash|remove|revoke|share|publish|"
        r"deploy|push|merge|create|update|write|send|post|approve|"
        r"invite|grant|execute|run|pay|charge)(?:$|[^a-z0-9])"
    )
    for key in ("action", "operation", "mode", "method"):
        value = arguments.get(key)
        if value is not None and change_words.search(str(value).lower()):
            return False
    return True

mcp_read_only = _mcp_read_only_operation(tool, tool_input)

if ("netlify" in tool.lower() and not mcp_read_only
        and any(x in haystack for x in ["deploy", "publish", "production", "prod"])):
    decide("ask", "TAKY deploy gate: Netlify production/publish actions require explicit user approval.")

if ("github" in tool.lower() and not mcp_read_only
        and any(x in haystack for x in ["push", "merge", "delete", "release", "force"])):
    decide("ask", "TAKY GitHub gate: push/merge/delete/release/force actions require explicit user approval.")

if tool.lower() in {"mcp__scenario__model_run", "mcp__scenario__workflow_run",
                    "mcp__scenario__scenario_tool_execute_write", "mcp__scenario__scenario_tool_execute_delete"}:
    decide("ask", "TAKY/SAVEY cost gate: Scenario generation/workflow/write actions require explicit user approval.")

# Shepherding: verify a truly local Reason handoff instead of treating every
# send_message as an external publication. This grants no generic MCP privilege:
# ordinary Claude permissions still apply and all nonlocal/uncertain routes ask.
def _reason_local_same_machine_route(tool_name, arguments):
    if tool_name.lower() != "mcp__reason-network__send_message":
        return False
    if not isinstance(arguments, dict) or set(arguments) != {"to", "message"}:
        return False  # no files, broadcasts, notifications, or impersonation
    target, message = arguments.get("to"), arguments.get("message")
    if not isinstance(target, str) or not isinstance(message, str):
        return False
    if not message.strip() or len(message.encode("utf-8")) > 4096:
        return False
    if target.count("/") != 1:
        return False
    person, session = target.split("/", 1)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}", person):
        return False
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}", session):
        return False
    try:
        import subprocess
        import tomllib
        config_file = Path.home() / ".reason" / "network" / "config.toml"
        config = tomllib.loads(config_file.read_text(encoding="utf-8"))
        if config.get("person") != person:
            return False
        exe = (Path(os.environ.get("LOCALAPPDATA", ""))
               / "TAKY" / "reason_network_evaluation" / "bin" / "reason-network.exe")
        if not exe.is_file():
            return False
        result = subprocess.run(
            [str(exe), "team", "--json"], stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=8, check=False,
        )
        if result.returncode != 0:
            return False
        team = json.loads(result.stdout)
        members = team.get("members")
        return bool(
            team.get("person") == person
            and isinstance(team.get("team_name"), str) and bool(team["team_name"])
            and isinstance(members, list) and len(members) == 1
            and members[0].get("person") == person
            and members[0].get("machine") == team.get("machine")
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            subprocess.SubprocessError):
        return False

if event == "PreToolUse" and tool.lower() == "mcp__reason-network__send_message":
    if _reason_local_same_machine_route(tool, tool_input):
        # Defer to Claude Code's regular tool permissions; no extra TAKY prompt.
        sys.exit(0)
    decide("ask",
           "TAKY GUIDED ROUTE: this recipient is not verified as a same-PC, "
           "single-member Reason session (or the call includes attachments, "
           "broadcasts, or unsupported fields). Use a verified local session "
           "with text-only send_message, or obtain user approval for an "
           "external/uncertain destination. Do not repeat the same blocked call.")

# Generic MCP high-impact gate. Inspect control/action fields and tool identity, not arbitrary page/document text.
if tool.lower().startswith("mcp__"):
    control_keys = ("action", "operation", "mode", "permission", "role", "visibility", "scope", "command")
    control_values = [str(tool_input.get(k) or "") for k in control_keys if k in tool_input]
    mcp_control_text = (tool + " " + " ".join(control_values)).lower()
    high_impact_terms = [
        "delete", "trash", "purge", "remove_member", "revoke", "share", "permission",
        "invite", "publish", "deploy", "release", "push", "merge", "force", "send_email",
        "send_message", "post_message", "account", "credential", "secret", "billing", "payment"
    ]
    if not mcp_read_only and any(term in mcp_control_text for term in high_impact_terms):
        decide("ask",
               "TAKY connection-security gate: action may change external state, "
               "access, messages or cost. Use a read-only endpoint where sufficient; "
               "otherwise obtain user approval for the specific external change.")

if remote_soft_guidance:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": remote_soft_guidance,
        }
    }, ensure_ascii=False))
sys.exit(0)
