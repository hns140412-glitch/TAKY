"""Read-only, allowlisted TAKY usage export for a synced Google Drive JSON file.
Never exports local paths, credentials, authentication state, or raw telemetry.
Runs on demand (or via the existing Windows scheduler); no permanent service.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
from TAKY_USAGE_BOARD import snapshot

PROVIDERS = ("Claude Code", "Codex CLI", "Antigravity", "ElevenLabs", "Netlify", "ChatGPT 웹/앱")
WINDOW_KEYS = ("usedPercent", "remainingPercent", "resetAt", "observedAt",
               "used", "remaining", "limit", "unit", "estimated", "expired")
SOURCE_KEYS = ("name", "observedAt", "fresh", "plan")
TEAM_KEYS = ("name", "plan", "monthlyIncluded", "monthlyUsed", "monthlyIncludedRemaining")
POOL_KEYS = ("remainingPercent", "resetAt", "modelCount", "unit")

def copy_keys(source, keys):
    if not isinstance(source, dict):
        return {}
    return {key: source[key] for key in keys if key in source}

def projection(raw):
    rows = {p.get("name"): p for p in raw.get("providers", []) if isinstance(p, dict)}
    out = []
    for name in PROVIDERS:
        source = rows.get(name)
        if not isinstance(source, dict):
            continue
        item = copy_keys(source, SOURCE_KEYS)
        for field in ("fiveHour", "week", "month", "context"):
            item[field] = copy_keys(source.get(field), WINDOW_KEYS)
        if name == "Antigravity":
            for field in ("geminiPool", "thirdPartyPool"):
                item[field] = copy_keys(source.get(field), POOL_KEYS)
        if name == "Netlify":
            item["teams"] = [copy_keys(t, TEAM_KEYS) for t in source.get("teams", []) if isinstance(t, dict)]
        out.append(item)
    return {
        "schema": "TAKY_USAGE_MOBILE_PROJECTION_V1",
        "checkedAt": raw.get("checkedAt"),
        "exportedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "percentMeans": "consumed_except_antigravity_remaining",
        "providers": out,
    }

def atomic_write(path, data):
    path = Path(path)
    if not path.parent.is_dir():
        raise FileNotFoundError("SYNC_DIRECTORY_NOT_FOUND: " + str(path.parent))
    encoded = (json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > 100000:
        raise ValueError("PROJECTION_TOO_LARGE")
    fd, temp = tempfile.mkstemp(prefix=".taky-usage-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(encoded)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return len(encoded)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Existing local staging or Google Drive synced file")
    parser.add_argument("--refresh-claude", action="store_true",
                        help="Attempt rate-gated read-only Claude account observation before exporting")
    a = parser.parse_args()
    claude_refresh = "NOT_REQUESTED"
    if a.refresh_claude:
        from TAKY_USAGE_BOARD import refresh_claude_usage
        claude_refresh = refresh_claude_usage()  # Authenticated GET; persisted 30-minute/429 cooldown.
    data = projection(snapshot())
    size = atomic_write(a.output, data)
    print(json.dumps({"status":"EXPORTED_LOCAL_FILE","file":str(a.output),
        "bytes":size,"providers":len(data["providers"]),
        "claudeRefresh":claude_refresh}, ensure_ascii=False))

if __name__ == "__main__":
    main()
