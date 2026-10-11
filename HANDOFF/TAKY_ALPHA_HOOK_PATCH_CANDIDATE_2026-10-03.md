# Hook hardening patch — CANDIDATE (not applied)
Status: EVIDENCE / CANDIDATE. Target: `.claude/hooks/taky_hook.py` (harness-marked sensitive file; direct edit was permission-blocked, not bypassed).
Closes: PREAUDIT S1 (scenario cost gate), S3 (hook/AGENTS/CLAUDE self-modification, secret-file reads via shell).

## 1. Edit/Write ask paths — extend list
```python
["/taky.md", "/master/", "/.claude/settings", "/.mcp.json", "/.claude/hooks/", "/agents.md", "/claude.md"]
```

## 2. Before `if any(re.search(p, haystack ...` add
```python
ask_patterns += [
    r"\b(cat|type|get-content|gc|more|less|head|tail|cp|copy|copy-item|scp)\b[^|;&]*(/|\\|\s)\.env\b",
    r"\b(cat|type|get-content|gc|more|less|head|tail|cp|copy|copy-item|scp)\b[^|;&]*(credentials|token\.json|id_rsa)",
]
```

## 3. Before `# Generic MCP high-impact gate.` add
```python
if tool.lower() in {"mcp__scenario__model_run", "mcp__scenario__workflow_run",
                    "mcp__scenario__scenario_tool_execute_write", "mcp__scenario__scenario_tool_execute_delete"}:
    decide("ask", "TAKY/SAVEY cost gate: Scenario generation/workflow/write actions consume credits or change account data. Explicit user approval is required.")
```

## Replay cases (pipe to `python .claude/hooks/taky_hook.py`, expect ask / silent)
- Bash `cat .env` -> ask; Bash `cat ~/.aws/credentials` -> ask; Bash `git status` -> silent; Bash `ls .environment-notes` -> silent
- Edit `.claude/hooks/taky_hook.py` -> ask; Edit `HANDOFF/x.md` -> silent
- `mcp__scenario__model_run` -> ask; `mcp__scenario__models_list` -> silent

Observed live evidence: the existing hook already intercepted a shell command containing provider-key names (ask gate works for T4 text patterns).
Not covered here (needs settings.json edit, ask-gated): PreToolUse matcher omits `Read|Grep`, so Read of secret files is ungated.
