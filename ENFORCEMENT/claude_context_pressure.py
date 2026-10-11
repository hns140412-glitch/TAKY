from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LIGHT_THRESHOLD = 40.0
COMPACT_THRESHOLD = 50.0
STATE_MAX_AGE_SECONDS = 180


def classify_context_pct(pct: float | int | None) -> str:
    if not isinstance(pct, (int, float)):
        return "UNKNOWN"
    value = float(pct)
    if value >= COMPACT_THRESHOLD:
        return "COMPACT"
    if value >= LIGHT_THRESHOLD:
        return "LIGHT"
    return "NORMAL"


def guidance_for(mode: str, pct: float | int | None = None) -> str:
    suffix = f" ({float(pct):.0f}% context)" if isinstance(pct, (int, float)) else ""
    if mode == "LIGHT":
        return (
            "TAKY LIGHT_CONTEXT_MODE" + suffix + ": preserve DEEP MEMORY - LIGHT EXECUTION. "
            "Do not broadly re-read authority/docs already resolved. Use CURRENT/owner first, then only targeted evidence for an actual gap. "
            "Batch related reads/tools, reuse prior results, avoid duplicate explanation, and finish the current bounded unit before opening another branch."
        )
    if mode == "COMPACT":
        return (
            "TAKY COMPACT_MODE" + suffix + ": context is above the TAKY compact-preparation threshold. "
            "Do not assume native auto-compact has happened or will happen at this percentage. "
            "Continue LIGHT execution, finish only the current bounded unit, and preserve the existing CURRENT/HANDOFF resume pointer before another broad phase. "
            "Claim compaction only after a real PreCompact/compact-resume lifecycle event is observed; then restore from CURRENT/owner and targeted evidence instead of replaying the full transcript."
        )
    return ""


def default_state_path() -> Path:
    return Path.home() / ".claude" / "taky" / "context-pressure.json"


def write_state(pct: float | int | None, *, path: Path | None = None, source: str = "statusline") -> dict[str, Any]:
    target = path or default_state_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "schema": "TAKY_CONTEXT_PRESSURE_V1",
        "used_percentage": float(pct) if isinstance(pct, (int, float)) else None,
        "mode": classify_context_pct(pct),
        "light_threshold": LIGHT_THRESHOLD,
        "compact_threshold": COMPACT_THRESHOLD,
        "source": source,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(target)
    return state


def read_fresh_state(*, path: Path | None = None, max_age_seconds: int = STATE_MAX_AGE_SECONDS) -> dict[str, Any]:
    target = path or default_state_path()
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
        raw = state.get("updated_at")
        if not isinstance(raw, str):
            return {}
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
        if age > max_age_seconds:
            return {}
        return state
    except Exception:
        return {}
