#!/usr/bin/env python3
"""Guard Git-tracked paths against local/source data, without blocking app assets.

This guard reads Git's tracked-path index, not user source contents. It prevents
accidental source/data commits; it does not attest an app asset's rights/approval.
No user data, filenames, raw bytes or private locators are emitted to CI logs.
"""
from __future__ import annotations

from collections import Counter
import subprocess
import sys

# Component matches apply at ANY depth, not just the repository root.
DATA_DIRECTORY_NAMES = frozenset({
    "source_archive", "90_raw_source_archive", "raw_source_archive",
    "source_vault", "taky-source-vault", "work_os_source_cache",
    "captures_v04", "acquired_external",
})
# Avoid banning general directories named "data" or "assets": legitimate
# PWA code/configuration and approved built-in assets can live there.
PRIVATE_SUBPATHS = (
    ("data", "notion_incremental"),
    ("source_reference", "runtime"),
)
PRIVATE_FILENAMES = frozenset({
    "blocks.json", "incremental_queue.json", "incremental_summary.json",
    "incremental_errors.json", "mining_inbox_handoff.json",
    "source_archive_compare.json", "source_vault_router_receipt.json",
    "source_vault_snapshot_evidence.json",
    "source_vault_external_acquisition.json",
})
SECRET_SUFFIXES = (".p12", ".pfx", ".key")


def reason_for_tracked_path(git_path: str) -> str | None:
    if not isinstance(git_path, str) or not git_path or "\x00" in git_path:
        return "invalid_git_path"
    parts = tuple(x.casefold() for x in git_path.replace("\\", "/").split("/"))
    if any(not item or item in (".", "..") for item in parts):
        return "invalid_git_path"
    if any(part in DATA_DIRECTORY_NAMES for part in parts[:-1]):
        return "source_or_data_directory"
    if any(
        parts[i:i + len(pattern)] == pattern
        for pattern in PRIVATE_SUBPATHS
        for i in range(len(parts) - len(pattern) + 1)
    ):
        return "private_runtime_or_capture_tree"
    filename = parts[-1]
    if filename in PRIVATE_FILENAMES:
        return "private_data_receipt"
    if filename.endswith(".local.json"):
        return "private_local_config"
    if filename == ".env" or (filename.startswith(".env.") and filename != ".env.example"):
        return "private_environment"
    if filename.endswith(SECRET_SUFFIXES):
        return "private_key_material"
    return None


def inspect_paths(paths: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(
        reason for path in paths
        if (reason := reason_for_tracked_path(path)) is not None
    ).items()))


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "-z"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode != 0:
        print("FAIL: Git tracked-path inspection unavailable", file=sys.stderr)
        return 2
    paths = [item.decode("utf-8", "surrogateescape") for item
             in result.stdout.split(b"\0") if item]
    reasons = inspect_paths(paths)
    if reasons:
        print("FAIL: protected source/data paths are tracked by Git; "
              "do not push. Categories only (paths/content intentionally hidden):",
              file=sys.stderr)
        for reason, count in reasons.items():
            print(f"  {reason}: {count}", file=sys.stderr)
        return 1
    print(f"PASS: {len(paths)} Git-tracked implementation paths checked; "
          "0 protected source/data paths. App asset approval and Drive sync "
          "require separate evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
