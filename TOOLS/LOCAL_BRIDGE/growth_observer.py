#!/usr/bin/env python3
"""TAKY explicit-scope local evidence change observer (metadata only).

Read-only toward source files. This is NOT Mining, Indexing, Learning, a proof of
Google Drive sync, or a canonical promotion/receipt. No recursive scan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "TAKY_LOCAL_EVIDENCE_OBSERVATION_V1"
KINDS = {
    "SOURCE_RAW": "MINING_OWNER_REVIEW",
    "INDEX_OWNER_RECEIPT": "INDEXING_OWNER_REVIEW",
    "LEARNING_VERIFIED_RECEIPT": "LEARNING_OWNER_REVIEW",
    "OUTCOME_EVIDENCE": "GROWTH_OWNER_REVIEW",
    "CURRENT_CHECKPOINT": "CONTINUITY_OWNER_REVIEW",
}
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def resolved(root: Path, relative: str) -> Path:
    p = Path(relative)
    if not relative or p.is_absolute() or any(x in (".", "..") for x in p.parts):
        raise ValueError("UNSAFE_SOURCE_POINTER")
    base = root.resolve(strict=True)
    target = (base / p).resolve()
    if not target.is_relative_to(base) or target == base:
        raise ValueError("SOURCE_OUTSIDE_BOUNDARY")
    return target


def manifest(config: dict):
    if not isinstance(config, dict) or config.get("schema") != "TAKY_OBSERVATION_SCOPE_V1":
        raise ValueError("INVALID_SCOPE_SCHEMA")
    root = Path(config["source_root"]).expanduser().resolve(strict=True)
    sources = config.get("sources")
    if not isinstance(sources, list) or not sources or len(sources) > 200:
        raise ValueError("EXPLICIT_BOUNDED_SOURCES_REQUIRED")
    normalized, ids = [], set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("INVALID_SOURCE_RECORD")
        sid, rel, owner, kind = (source.get(k) for k in ("source_id", "relative_path", "owner", "kind"))
        if not isinstance(sid, str) or not IDENT.fullmatch(sid) or sid in ids:
            raise ValueError("INVALID_OR_DUPLICATE_SOURCE_ID")
        if not isinstance(owner, str) or not IDENT.fullmatch(owner):
            raise ValueError("OWNER_REQUIRED")
        if kind not in KINDS or not isinstance(rel, str):
            raise ValueError("INVALID_SOURCE_KIND_OR_PATH")
        resolved(root, rel)  # validate even for currently missing targets
        ids.add(sid)
        normalized.append({"source_id": sid, "relative_path": rel.replace("\\", "/"),
                           "owner": owner, "kind": kind})
    normalized.sort(key=lambda x: x["source_id"])
    return root, normalized, digest_bytes(canonical(normalized))


def file_hash(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def load_previous(path: Path, root: Path, scope_hash: str):
    if path is None:
        return {}
    record = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise ValueError("INVALID_PREVIOUS_RECEIPT")
    if record.get("source_root") != str(root) or record.get("scope_hash") != scope_hash:
        raise ValueError("PREVIOUS_SCOPE_MISMATCH")
    rows = record.get("entries")
    if not isinstance(rows, list):
        raise ValueError("PREVIOUS_ROWS_INVALID")
    previous = {}
    for item in rows:
        if not isinstance(item, dict) or item.get("source_id") in previous:
            raise ValueError("PREVIOUS_ROWS_INVALID")
        if item.get("status") not in ("FIRST_OBSERVATION", "UNCHANGED", "CHANGED", "MISSING", "UNREADABLE"):
            raise ValueError("PREVIOUS_STATUS_INVALID")
        d = item.get("sha256")
        if d is not None and (not isinstance(d, str) or not SHA.fullmatch(d)):
            raise ValueError("PREVIOUS_HASH_INVALID")
        previous[item["source_id"]] = item
    return previous


def observe(config: dict, output: Path, previous_path: Path | None = None):
    root, sources, scope_hash = manifest(config)
    output = output.expanduser().resolve()
    if output == root or output.is_relative_to(root):
        raise ValueError("REPORT_INSIDE_SOURCE_ROOT")
    if output.exists():
        raise ValueError("REPORT_ALREADY_EXISTS")
    previous = load_previous(previous_path, root, scope_hash)
    entries = []
    for source in sources:
        path = resolved(root, source["relative_path"])
        entry = dict(source)
        entry.update({"sha256": None, "size": None, "status": None,
                      "route_hint": KINDS[source["kind"]],
                      "owner_promotion_authorized": False,
                      "content_exported": False})
        prior = previous.get(source["source_id"])
        if not path.is_file():
            entry["status"] = "MISSING"
        else:
            try:
                # A file that changes during hashing is not a verified observation.
                before = path.stat()
                entry["sha256"] = file_hash(path)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    entry["sha256"] = None
                    entry["status"] = "UNREADABLE"
                else:
                    entry["size"] = after.st_size
                    if prior is None or prior.get("sha256") is None:
                        entry["status"] = "FIRST_OBSERVATION"
                    elif prior["sha256"] == entry["sha256"]:
                        entry["status"] = "UNCHANGED"
                    else:
                        entry["status"] = "CHANGED"
            except OSError:
                entry["sha256"] = None
                entry["status"] = "UNREADABLE"
        entries.append(entry)
    counts = {status: sum(e["status"] == status for e in entries) for status in
              ("FIRST_OBSERVATION", "CHANGED", "UNCHANGED", "MISSING", "UNREADABLE")}
    result = {"schema": SCHEMA, "generated_at": datetime.now(timezone.utc).isoformat(),
              "source_root": str(root), "scope_hash": scope_hash,
              "previous_receipt": str(previous_path) if previous_path else None,
              "authority": "LOCAL_METADATA_OBSERVATION_ONLY",
              "drive_sync_freshness": "NOT_VERIFIED",
              "mining_complete": False, "indexing_complete": False,
              "learning_verified": False, "canonical_promotion": False,
              "counts": counts, "entries": entries}
    output.mkdir(parents=True, exist_ok=False)
    (output / "OBSERVATION_RECEIPT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# TAKY local evidence change observation", "",
             "Declared sources only. Hash matching proves local bytes, not freshness or semantic correctness.",
             "No Mining, Indexing, Learning or canonical promotion; routes are owner review hints.", "",
             "| Source | Owner | Evidence type | Status | Route |",
             "|---|---|---|---|---|"]
    for row in entries:
        lines.append("| " + " | ".join(row[k] for k in
            ("source_id", "owner", "kind", "status", "route_hint")) + " |")
    lines += ["", "First observation is not proof of a newly created source.",
              "Missing/unreadable sources are not treated as changed verified evidence.",
              "Review private paths and source identifiers before any sharing."]
    (output / "OBSERVATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--previous", type=Path)
    args = p.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8-sig"))
        result = observe(config, args.output, args.previous)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED:", type(exc).__name__, str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"report": str(args.output), "counts": result["counts"]}, ensure_ascii=False))
    return 0 if not (result["counts"]["MISSING"] or result["counts"]["UNREADABLE"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
