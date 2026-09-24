#!/usr/bin/env python3
"""Bootstrap and validate the TAKY local + Google Drive workspace.

This utility creates a local execution layout where only drive-sync/ is meant
to be selected in Google Drive for desktop. Git repositories and high-churn
cache/temp data remain outside that synced subtree.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

LAYOUT = [
    "drive-sync/CURRENT",
    "drive-sync/INDEX",
    "drive-sync/C2S_WORK",
    "drive-sync/HANDOFF",
    "drive-sync/HISTORY",
    "drive-sync/EXPORT",
    "local-only/cache",
    "local-only/temp",
    "local-only/extracted",
    "local-only/renders",
    "repos",
]

CONFIG = ".taky-local-workspace.json"


def init_workspace(root: Path) -> dict:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for rel in LAYOUT:
        (root / rel).mkdir(parents=True, exist_ok=True)

    cfg = {
        "version": "1.0",
        "root": str(root),
        "state_root": str(root / "drive-sync"),
        "sync_selection": str(root / "drive-sync"),
        "local_only_root": str(root / "local-only"),
        "repos_root": str(root / "repos"),
        "authority": {
            "local": "EXECUTION_SURFACE",
            "google_drive_computer_backup": "DURABLE_MIRROR",
            "google_drive_taky_root": "DURABLE_SOURCE_RESULT_REVIEW",
            "github": "CODE_GOVERNANCE_VERSION_AUTHORITY",
        },
        "notes": [
            "Select only drive-sync/ in Google Drive for desktop backup/sync.",
            "Keep Git working trees outside drive-sync/.",
            "Set TAKY_STATE_ROOT to drive-sync/ for local atomic CURRENT persistence.",
        ],
    }
    config_path = root / CONFIG
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "pass": True,
        "root": str(root),
        "state_root": cfg["state_root"],
        "config": str(config_path),
        "created": LAYOUT,
    }


def _contains_git_metadata(path: Path) -> bool:
    if not path.exists():
        return False
    for candidate in path.rglob(".git"):
        if candidate.exists():
            return True
    return False


def doctor(root: Path) -> dict:
    root = root.expanduser().resolve()
    detected: list[str] = []

    for rel in LAYOUT:
        if not (root / rel).exists():
            detected.append(f"MISSING:{rel}")

    sync_root = root / "drive-sync"
    repos_root = root / "repos"

    if _contains_git_metadata(sync_root):
        detected.append("GIT_METADATA_INSIDE_DRIVE_SYNC")

    try:
        sync_root.mkdir(parents=True, exist_ok=True)
        probe = sync_root / ".taky-write-probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
    except OSError:
        detected.append("DRIVE_SYNC_ROOT_NOT_WRITABLE")

    if repos_root == sync_root or sync_root in repos_root.parents:
        detected.append("REPOS_ROOT_INSIDE_DRIVE_SYNC")

    cfg_path = root / CONFIG
    if not cfg_path.exists():
        detected.append("WORKSPACE_CONFIG_MISSING")
    else:
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            if Path(cfg.get("state_root", "")).expanduser().resolve() != sync_root:
                detected.append("STATE_ROOT_CONFIG_MISMATCH")
        except Exception:
            detected.append("WORKSPACE_CONFIG_INVALID")

    return {
        "pass": not detected,
        "detected": detected,
        "root": str(root),
        "state_root": str(sync_root),
        "recommended_env": f"TAKY_STATE_ROOT={sync_root}",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init")
    init_p.add_argument("--root", type=Path, required=True)

    doc_p = sub.add_parser("doctor")
    doc_p.add_argument("--root", type=Path, required=True)

    args = ap.parse_args()
    result = init_workspace(args.root) if args.command == "init" else doctor(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
