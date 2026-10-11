from pathlib import Path
import re

ROOT = Path(r"D:\Git PWA\TAKY")
CLAUDE_DIR = ROOT / ".claude"

DIRECT = re.compile(
    r'shutil\.which\(["\']claude["\']\)|claude\.exe',
    re.IGNORECASE,
)

def test_executable_legacy_audit_scripts_no_longer_call_claude_directly():
    offenders = []
    for path in CLAUDE_DIR.glob("run_*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if DIRECT.search(text):
            offenders.append(path.name)
    assert offenders == []

def test_legacy_direct_sources_are_preserved_for_converted_scripts():
    shims = []
    for path in CLAUDE_DIR.glob("run_*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "TAKY_MODEL_REVIEW.ps1" in text:
            shims.append(path)
            backup = path.with_suffix(path.suffix + ".legacy-direct-source.txt")
            assert backup.exists(), f"missing legacy source backup for {path.name}"
            assert DIRECT.search(backup.read_text(encoding="utf-8", errors="ignore"))
    assert shims, "expected at least one receipt-bound legacy review shim"
