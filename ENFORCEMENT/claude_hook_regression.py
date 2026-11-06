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
