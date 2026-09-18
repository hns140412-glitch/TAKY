#!/usr/bin/env python3
"""Repository-executable C2S-aware preflight bridge.

This composes the canonical TAKY preflight with conversation-to-system coverage
when a record declares conversation_system_compile_required=true.

It proves repository-executable gating only. It does NOT prove that hosted ChatGPT
native turns automatically invoke this bridge.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from preflight_bridge import run as run_preflight


def run(record: dict, repo_root: Path, coverage_record: Path | None) -> dict:
    result = run_preflight(record, repo_root)
    detected = list(result.get("detected", []))
    compile_required = bool(record.get("conversation_system_compile_required", False))

    coverage = {
        "required": compile_required,
        "provided": coverage_record is not None,
        "pass": None,
        "output": None,
    }

    if compile_required:
        if coverage_record is None:
            detected.append("C2S_COVERAGE_RECORD_MISSING")
            coverage["pass"] = False
        else:
            validator = repo_root / "ENFORCEMENT" / "conversation_coverage_validator.py"
            proc = subprocess.run(
                [sys.executable, str(validator), str(coverage_record)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            coverage["pass"] = proc.returncode == 0
            coverage["output"] = (proc.stdout + proc.stderr).strip()
            if proc.returncode != 0:
                detected.append("C2S_COVERAGE_FAIL")

    detected = list(dict.fromkeys(detected))
    return {
        **result,
        "pass": not detected,
        "detected": detected,
        "c2s": coverage,
        "runtime_claim_ceiling": "REPOSITORY_EXECUTABLE_CI_ENFORCED",
        "live_runtime_auto_invocation_verified": bool(
            record.get("live_runtime_auto_invocation_verified", False)
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--coverage-record", type=Path)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = run(record, args.repo_root, args.coverage_record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
