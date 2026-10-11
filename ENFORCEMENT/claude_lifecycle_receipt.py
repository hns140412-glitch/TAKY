#!/usr/bin/env python3
from __future__ import annotations
import json, os, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCHEMA = "TAKY_CLAUDE_LIFECYCLE_RECEIPT_V1"
ROLE = "WRITE_ONLY_LIFECYCLE_RECEIPT"
AUTHORITY_RELOAD_HINT = "DOMAIN/GROW_DOMAIN_REGISTRY.json#shared_core.current_index"
ALLOWED = {
    "SessionStart": {"startup", "resume", "compact"},
    "PreCompact": {"manual", "auto"},
}

def _s(v): return str(v or "").strip()

def build_receipt(data):
    event = _s(data.get("hook_event_name"))
    source = _s(data.get("source") or data.get("trigger") or data.get("reason")).lower()
    if event not in ALLOWED or source not in ALLOWED[event]:
        return None
    return {
        "schema": SCHEMA,
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "hook_event_name": event,
        "source": source,
        "role": ROLE,
        "authority_reload_hint": AUTHORITY_RELOAD_HINT,
        "semantic_authority": False,
        "promotion_authorized": False,
        "contains_session_content": False,
        "contains_identity": False,
        "contains_path": False,
    }

def receipt_root():
    override = _s(os.environ.get("TAKY_CLAUDE_LIFECYCLE_RECEIPT_DIR"))
    return Path(override).expanduser() if override else Path.home()/".claude"/"taky"/"lifecycle-receipts-v1"

def cleanup(root, ttl_days=14, max_files=200):
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, int(ttl_days)))
    kept = []
    for p in root.glob("receipt-*.json"):
        try:
            st = p.stat()
            if datetime.fromtimestamp(st.st_mtime, timezone.utc) < cutoff:
                p.unlink(missing_ok=True)
                continue
            kept.append((st.st_mtime_ns, p))
        except OSError:
            pass
    kept.sort(reverse=True)
    for _, p in kept[max(1, int(max_files)):]:
        try: p.unlink(missing_ok=True)
        except OSError: pass

def persist_receipt(data, ttl_days=14, max_files=200):
    receipt = build_receipt(data)
    if receipt is None:
        return None
    root = receipt_root()
    root.mkdir(parents=True, exist_ok=True)
    stamp = receipt["captured_at"].replace(":","").replace("-","").replace(".","")
    target = root/f"receipt-{stamp}-{os.getpid()}.json"
    fd, tmp = tempfile.mkstemp(prefix=target.name+".", suffix=".tmp", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(receipt, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
    finally:
        try: Path(tmp).unlink(missing_ok=True)
        except OSError: pass
    cleanup(root, ttl_days, max_files)
    return receipt
