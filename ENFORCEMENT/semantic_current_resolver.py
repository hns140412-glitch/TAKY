#!/usr/bin/env python3
"""Read-only, fail-closed semantic owner resolution; no numbered filename discovery."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CurrentResolutionError(ValueError):
    pass

def resolve_owner(registry: dict, owner: str, root: Path = ROOT) -> dict:
    aliases = registry.get("logical_owner_aliases", {})
    if not isinstance(owner, str) or not owner or owner not in aliases:
        raise CurrentResolutionError("UNKNOWN_SEMANTIC_OWNER")
    entry = aliases[owner]
    path = entry.get("path")
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        raise CurrentResolutionError("INVALID_OWNER_PATH")
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise CurrentResolutionError("OWNER_SOURCE_MISSING")
    entries = registry.get("files", {})
    if path.startswith("MASTER/"):
        meta = entries.get(path)
        if not meta or meta.get("class") != entry.get("class") or meta.get("class") != "ACTIVE_OWNER":
            raise CurrentResolutionError("OWNER_NOT_ACTIVE")
        if meta.get("logical_id") != owner:
            raise CurrentResolutionError("OWNER_ALIAS_MISMATCH")
        duplicates = [p for p, m in entries.items() if m.get("logical_id") == owner and m.get("class") == "ACTIVE_OWNER"]
        if duplicates != [path]:
            raise CurrentResolutionError("AMBIGUOUS_ACTIVE_OWNER")
    elif entry.get("class") != "NAMESPACE_CURRENT_POINTER" or not path.startswith("CURRENT/"):
        raise CurrentResolutionError("UNVERIFIED_NON_MASTER_OWNER")
    return {"semantic_owner": owner, "path": path, "alias_state": entry.get("alias_state"), "authority_class": entry["class"]}

def resolve_promoted_data(registry: dict, root: Path = ROOT) -> dict:
    selected = resolve_owner(registry, "DATA_SEARCH_PROJECTION", root)
    payload = json.loads((root / selected["path"]).read_text(encoding="utf-8-sig"))
    authority = payload.get("authority_current", {})
    source = authority.get("source_index", {})
    utilization = authority.get("utilization_index", {})
    receipt = authority.get("promotion_receipt", {})
    ids = [x.get("id") for x in (source, utilization, receipt)]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(set(ids)) != 3:
        raise CurrentResolutionError("MISSING_OR_DUPLICATE_PROMOTION_ID")
    if authority.get("source_entries_total") != authority.get("indexed_l1") or not isinstance(authority.get("source_entries_total"), int) or authority["source_entries_total"] < 1:
        raise CurrentResolutionError("INCONSISTENT_SOURCE_COVERAGE")
    if authority.get("source_loss") is not False:
        raise CurrentResolutionError("SOURCE_LOSS_OR_UNKNOWN")
    # Names are retained for historical traceability, but never used to select a file.
    return {"semantic_owner": "DATA_SEARCH_PROJECTION", "projection_path": selected["path"],
            "source_index_id": ids[0], "utilization_index_id": ids[1],
            "promotion_receipt_id": ids[2], "source_entries_total": authority["source_entries_total"],
            "verification_scope": "LOCAL_POINTER_CONSISTENCY_ONLY__EXTERNAL_RECEIPT_READBACK_REQUIRED"}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True, help="Stable semantic owner ID, not a REV/V filename")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        registry = json.loads((args.root / "MASTER/MASTER_FILE_REGISTRY.json").read_text(encoding="utf-8-sig"))
        result = resolve_promoted_data(registry, args.root) if args.owner == "DATA_SEARCH_PROJECTION" else resolve_owner(registry, args.owner, args.root)
    except (CurrentResolutionError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "RESOLVED", **result}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
