from pathlib import Path
import re

ROOT = Path(r"D:\Git PWA\TAKY")
TOOLS = ROOT / "TOOLS"

CANONICAL = TOOLS / "TAKY_START.ps1"
USER_ENTRYPOINTS = [
    TOOLS / "TAKY_CLAUDE.ps1",
    TOOLS / "TAKY_CLAUDE_LAUNCH.ps1",
    TOOLS / "TAKY_NL_TO_CLAUDE.ps1",
    TOOLS / "TAKY_NL_TO_CLAUDE.py",
]

DIRECT = re.compile(
    r"(?:&\s*claude\b|subprocess\.run\s*\(\s*\[\s*str\(CLAUDE\)|claude\.exe)",
    re.IGNORECASE | re.MULTILINE,
)

def test_canonical_launcher_is_the_only_user_entrypoint_that_invokes_claude_directly():
    canonical = CANONICAL.read_text(encoding="utf-8-sig")
    assert re.search(r"&\s*claude\b", canonical, re.IGNORECASE)
    for path in USER_ENTRYPOINTS:
        text = path.read_text(encoding="utf-8-sig" if path.suffix == ".ps1" else "utf-8")
        assert not DIRECT.search(text), f"direct Claude bypass remains in {path.name}"

def test_compatibility_entrypoints_funnel_to_taky_start():
    for name in ["TAKY_CLAUDE.ps1", "TAKY_CLAUDE_LAUNCH.ps1", "TAKY_NL_TO_CLAUDE.ps1"]:
        text = (TOOLS / name).read_text(encoding="utf-8-sig")
        assert "TAKY_START.ps1" in text
    py = (TOOLS / "TAKY_NL_TO_CLAUDE.py").read_text(encoding="utf-8")
    assert "TAKY_START.ps1" in py
    assert "powershell.exe" in py
