"""Pin the TAKY review wrapper shell to known Windows installation locations.

This is a local launcher guard, not proof that the OS installation is trusted.
Never search PATH, cwd, or arbitrary aliases for an authenticated executor.
"""
from __future__ import annotations

import os
from pathlib import Path


def trusted_shell_candidates() -> tuple[Path, ...]:
    # PowerShell 7 is preferred. The MSIX App Execution Alias must be an
    # OS-managed reparse point, never a replacement ordinary executable.
    local = Path.home() / "AppData" / "Local"
    return (
        Path(r"C:\Program Files\PowerShell\7\pwsh.exe"),
        local / "Microsoft" / "WindowsApps" / "pwsh.exe",
        Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
    )


def resolve_trusted_shell(*, candidates: tuple[Path, ...] | None = None) -> str:
    if os.name != "nt":
        raise ValueError("TRUSTED_WINDOWS_SHELL_REQUIRED")
    choices = trusted_shell_candidates() if candidates is None else candidates
    for shell in choices:
        try:
            path = Path(shell)
            if not path.is_file():
                continue
            if path.name.casefold() not in ("pwsh.exe", "powershell.exe"):
                continue
            # Trust no arbitrary candidates from caller: root must be one of
            # the pinned locations; tests may inject only exact known paths.
            if str(path).casefold() not in {
                str(p).casefold() for p in trusted_shell_candidates()
            }:
                continue
            if (path.parent.name.casefold() == "windowsapps" and
                    not (path.stat().st_file_attributes & 0x400)):
                # 0x400 = FILE_ATTRIBUTE_REPARSE_POINT. Reject a planted exe.
                continue
            return str(path)
        except (OSError, ValueError, AttributeError):
            continue
    raise ValueError("NO_PINNED_POWERSHELL_RUNTIME")
