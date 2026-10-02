#!/usr/bin/env python3
"""Guard one default resume authority route across TAKY governance surfaces."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "TAKY.md": [
        "/재개",
        "STATE -> applicable owner -> verified CURRENT -> OPEN/NEXT",
    ],
    "STATE.md": [
        "RESOLVE system:current",
        "CURRENT/SYSTEM_WIDE_REVIEW.json",
        "Resume by explicit semantic owner and verified evidence",
    ],
    "MASTER/CONVERSATION_CONTINUITY_PROTOCOL.md": [
        "STATE -> APPLICABLE OWNER -> CURRENT -> OPEN/NEXT -> CONTINUE",
    ],
    "MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md": [
        "CURRENT = VERIFIED RESUME POINTER",
        "STATE -> APPLICABLE OWNER -> CURRENT -> OPEN/NEXT -> CONTINUE",
    ],
    "MASTER/HANDOFF_PROTOCOL.md": [
        "HANDOFF ≠ SOURCE OF TRUTH",
        "Default TAKY `/재개` routing remains governed by STATE / applicable semantic owner / verified CURRENT",
        "Section 6 boot chain applies only when a Handoff package is materially required or CURRENT is insufficient",
    ],
}

def main() -> int:
    failures = []
    for rel, needles in REQUIRED.items():
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"MISSING_SURFACE:{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                failures.append(f"RESUME_AUTHORITY_MARKER_MISSING:{rel}:{needle}")

    handoff = (ROOT / "MASTER/HANDOFF_PROTOCOL.md").read_text(encoding="utf-8")
    legacy = "LATEST CANONICAL → HANDOFF → SOURCE POINTER/SNAPSHOT/MANIFEST RECOVERY"
    scope = "Section 6 boot chain applies only when a Handoff package is materially required or CURRENT is insufficient"
    if legacy in handoff and scope not in handoff:
        failures.append("HANDOFF_FIRST_CHAIN_UNSCOPED")

    result = {
        "pass": not failures,
        "default_resume_route": "STATE->OWNER->VERIFIED_CURRENT->OPEN/NEXT->LIVE_REVERIFY",
        "handoff_role": "CONDITIONAL_RECOVERY_EVIDENCE",
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
