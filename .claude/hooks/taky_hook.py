import json
import os
from pathlib import Path
import re
import sys

data = json.load(sys.stdin)
event = data.get("hook_event_name", "")

if event == "SessionStart":
    msg = "TAKY runtime: THINK AGAIN -> KEEP YOUR KEY -> FIND A WAY -> YOU'RE THE KEY -> VERIFY/CORRECT/CONTINUE. Use the smallest sufficient context and execution path. Recover useful prior context with Claude-Mem when available, but MEMORY IS A ROUTING AID, NOT AUTHORITY; verify against CURRENT/owner before acting. Do not make the user repeat recoverable decisions or act as debugger. For material design/results, produce the actual integrated artifact/runtime, inspect it, correct material deltas, and distinguish IMPLEMENTED from VERIFIED. Claude is executor, TAKY owns authority; SAVEY prefers subscription/local paths and requires human approval for paid API, production deploy, push, merge, or irreversible actions. USER != DEBUGGER."
    key_names = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"]
    active_keys = [name for name in key_names if os.environ.get(name)]
    if active_keys:
        msg += " SAVEY WARNING: provider API key(s) are active in this shell: " + ", ".join(active_keys) + ". Do not use them as fallback."
    root = Path(data.get("cwd") or ".")
    skill_dir = root / ".claude" / "skills"
    if skill_dir.exists() and len(list(skill_dir.glob("netlify-*"))) > 1:
        msg += " REGRESSION WARNING: multiple Netlify auto-skills reappeared; route through netlify-router and archive extras."
    print(msg)
    sys.exit(0)

tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}

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
        if not any(re.search(p, command_lower, re.I) for p in read_only_patterns):
            decide("ask", "TAKY authority/config shell gate: a command targeting protected governance/config surfaces is not recognized as read-only and requires explicit user approval.")

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
