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

def verify_data_receipt(registry: dict, receipt: dict, root: Path = ROOT) -> dict:
    """Cross-check a separately fetched original receipt, not its versioned title."""
    selected = resolve_promoted_data(registry, root)
    if not isinstance(receipt, dict) or receipt.get("canonical") is not False:
        raise CurrentResolutionError("INVALID_DERIVED_RECEIPT_ROLE")
    candidate, source, checks = (receipt.get(k, {}) for k in ("candidate", "source_index", "checks"))
    if candidate.get("id") != selected["utilization_index_id"] or source.get("id") != selected["source_index_id"]:
        raise CurrentResolutionError("PROMOTION_RECEIPT_ID_MISMATCH")
    n = selected["source_entries_total"]
    if any(checks.get(k) != n for k in ("source_entries_total", "source_index_entries_total", "index_l1_coverage")):
        raise CurrentResolutionError("PROMOTION_RECEIPT_COVERAGE_MISMATCH")
    for key in ("json_parse", "source_id_sets_equal", "all_delta_sources_present", "v26_current_regression", "current_pointer_rule_respected"):
        if checks.get(key) is not True:
            raise CurrentResolutionError("PROMOTION_RECEIPT_CHECK_MISSING:" + key)
    for key in ("source_loss", "full_reindex", "raw_reread", "search_projection_authoritative"):
        if checks.get(key) is not False:
            raise CurrentResolutionError("PROMOTION_RECEIPT_GUARD_FAILED:" + key)
    if receipt.get("decision") != "PROMOTE_V26_TO_CURRENT_DERIVED_CHECKPOINT":
        raise CurrentResolutionError("PROMOTION_RECEIPT_DECISION_MISMATCH")
    return {"status": "RECEIPT_MATCHES_POINTER", "semantic_owner": selected["semantic_owner"],
            "source_index_id": selected["source_index_id"], "utilization_index_id": selected["utilization_index_id"],
            "promotion_receipt_id": selected["promotion_receipt_id"], "source_entries_total": n,
            "verification_scope": "PROVIDED_RECEIPT_CONTENT_CROSSCHECK__AUTHENTICATED_FETCH_MUST_BE_INDEPENDENT"}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True, help="Stable semantic owner ID, not a REV/V filename")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt-file", type=Path, help="Independently authenticated original receipt JSON; never inferred from filename")
    args = parser.parse_args()
    try:
        registry = json.loads((args.root / "MASTER/MASTER_FILE_REGISTRY.json").read_text(encoding="utf-8-sig"))
        if args.receipt_file and args.owner != "DATA_SEARCH_PROJECTION":
            raise CurrentResolutionError("RECEIPT_ONLY_FOR_DATA_PROJECTION")
        if args.receipt_file:
            receipt = json.loads(args.receipt_file.read_text(encoding="utf-8-sig"))
            result = verify_data_receipt(registry, receipt, args.root)
        else:
            result = resolve_promoted_data(registry, args.root) if args.owner == "DATA_SEARCH_PROJECTION" else resolve_owner(registry, args.owner, args.root)
    except (CurrentResolutionError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "RESOLVED", **result}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
