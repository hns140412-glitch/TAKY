from __future__ import annotations
import re, sys, json, subprocess, os
from pathlib import Path

REPO = Path(r"D:\Git PWA\TAKY")
TAKY_START = REPO / "TOOLS" / "TAKY_START.ps1"

NOISE = [
    r"확인\s*필요할\s*때까지",
    r"쭉\s*진행해",
    r"계속\s*진행해",
    r"알아서",
    r"제대로",
    r"빨리",
]
ALIASES = {
    "비교검토":"COMPARE+REVIEW",
    "보완":"IMPROVE",
    "개선":"IMPROVE",
    "최적화":"OPTIMIZE",
    "오류검증":"ERROR_VERIFY",
    "자기검증":"SELF_VERIFY",
    "회귀검증":"REGRESSION_VERIFY",
}

def compress(text:str)->str:
    x=" ".join(text.strip().split())
    for p in NOISE:
        x=re.sub(p,"",x,flags=re.I)
    for k,v in ALIASES.items():
        x=x.replace(k,f" [{v}] ")
    x=" ".join(x.split())
    return x

def build_prompt(goal:str)->str:
    return f"""TAKY EXECUTION REQUEST
GOAL: {goal}

RULES:
- USER != DEBUGGER
- READ CURRENT STATE FIRST
- COMPARE -> REVIEW -> IMPROVE -> OPTIMIZE -> VERIFY
- PRESERVE CLOSED/PASS; ACT ON OPEN ONLY
- MINIMAL SAFE DIFF
- ACCESS FAILURE != SOURCE ABSENCE
- BLOCKED != FAILED
- NO PAID/API-KEY FALLBACK
- NO DEPLOY/PUSH/MERGE/RELEASE WITHOUT APPROVAL

VERIFY:
- syntax/static
- runtime assumptions
- error paths
- self-review
- regression

REPORT:
RESULT / CHANGED / TESTS / REMAINING_OPEN / PASS|FAIL|HOLD
"""

def main():
    if len(sys.argv)<2:
        raise SystemExit("usage: TAKY_NL_TO_CLAUDE.py <text>|--file <path> [--preview]")
    preview="--preview" in sys.argv
    args=[a for a in sys.argv[1:] if a!="--preview"]
    if len(args)>=2 and args[0]=="--file":
        text=Path(args[1]).read_text(encoding="utf-8")
    else:
        text=" ".join(args)
    goal=compress(text)
    prompt=build_prompt(goal)
    print("=== COMPRESSED ===")
    print(goal)
    print("=== PROMPT ===")
    print(prompt)
    if preview:
        return
    env=os.environ.copy()
    for k in ["ANTHROPIC_API_KEY","OPENAI_API_KEY","GEMINI_API_KEY","GOOGLE_API_KEY"]:
        env.pop(k,None)
    cp=subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(TAKY_START),
            prompt,
        ],
        cwd=str(REPO), env=env, text=True
    )
    raise SystemExit(cp.returncode)

if __name__=="__main__":
    main()
