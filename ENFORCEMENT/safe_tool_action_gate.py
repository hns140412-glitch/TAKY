#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

AUTH_PATTERNS = [
    r"\\AppData\\.*\\Google\\DriveFS",
    r"\\AppData\\.*\\Credentials?",
    r"\\\.ssh(?:\\|$)",
    r"token",
    r"credential",
]
BROAD_ENV_PATTERNS = [
    r"Get-ChildItem\s+Env:",
    r"\bset\b\s*$",
]
ROOT_SCAN_PATTERNS = [
    r"^[A-Z]:\\?$",
    r"^[A-Z]:\\Users\\?$",
]

def _s(v: object) -> str:
    return str(v or "").strip()

def evaluate(action: dict[str, Any]) -> dict[str, Any]:
    detected: list[str] = []
    purpose = action.get("purpose")
    purposes = action.get("purposes")
    if purposes is not None:
        if not isinstance(purposes, list) or len([x for x in purposes if _s(x)]) != 1:
            detected.append("ONE_CALL_ONE_PRIMARY_PURPOSE_REQUIRED")
    elif not _s(purpose):
        detected.append("PRIMARY_PURPOSE_MISSING")

    target = _s(action.get("target"))
    if not target:
        detected.append("EXACT_TARGET_REQUIRED")

    op = _s(action.get("operation")).lower()
    transport = _s(action.get("transport")).lower()
    command = _s(action.get("command"))
    connector_available = action.get("connector_available") is True
    drive_id = _s(action.get("drive_file_id") or action.get("drive_folder_id"))

    if op in {"google_drive", "drive", "drive_intake"} and connector_available and drive_id:
        if transport in {"local_scan", "drivefs_reverse_lookup", "shell_drive_search"}:
            detected.append("DRIVE_CONNECTOR_ID_ROUTE_REQUIRED")

    for p in ROOT_SCAN_PATTERNS:
        if target and re.search(p, target, re.I):
            detected.append("BROAD_ROOT_SCAN_FORBIDDEN")
            break

    combined = "\n".join([target, command])
    if action.get("explicit_auth_inspection") is not True:
        if any(re.search(p, combined, re.I) for p in AUTH_PATTERNS):
            detected.append("AUTH_ADJACENT_ENUMERATION_REQUIRES_EXPLICIT_NECESSITY")

    if any(re.search(p, command, re.I) for p in BROAD_ENV_PATTERNS):
        detected.append("BROAD_ENV_ENUMERATION_FORBIDDEN")

    blocked_sig = _s(action.get("previous_block_signature"))
    current_sig = _s(action.get("action_signature"))
    if blocked_sig and current_sig and blocked_sig == current_sig:
        detected.append("BLOCKED_ACTION_SIGNATURE_RETRY_FORBIDDEN")

    if action.get("file_io_only") is True and transport == "shell":
        detected.append("FILE_TOOL_REQUIRED_BEFORE_SHELL")

    return {
        "pass": not detected,
        "detected": detected,
        "recommended_route": (
            "USE_EXACT_FILE_OR_CONNECTOR_ID_AND_SPLIT_ACTION"
            if detected else "EXECUTE"
        ),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ns = ap.parse_args()
    data = json.loads(ns.input.read_text(encoding="utf-8-sig"))
    result = evaluate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
