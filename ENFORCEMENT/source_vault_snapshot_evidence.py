#!/usr/bin/env python3
"""Local Notion block-snapshot evidence extraction for SOURCE VAULT.

READ-ONLY input: verified queue/handoff/summary and the existing blocks.json files.
This is deterministic RAW acquisition, not external-web capture, semantic Mining,
Indexing acceptance, Learning use, or canonical promotion. No network required.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
from typing import Any

from source_vault_handoff_bridge import build_receipt, InputError

MAX_SNAPSHOT_BYTES = 25 * 1024 * 1024
MAX_BLOCKS_PER_PAGE = 10000
SCHEMA = "TAKY_NOTION_LOCAL_SNAPSHOT_EVIDENCE_V1"


def _folder(root: Path, row: dict[str, Any]) -> Path:
    page_id = row["notion_page_id"]
    claimed = row.get("block_snapshot_folder")
    if not isinstance(claimed, str) or not claimed:
        raise InputError("SNAPSHOT_LOCATOR_MISSING")
    claimed_parts = PureWindowsPath(claimed).parts
    if len(claimed_parts) < 5 or claimed_parts[-5:-2] != ("data", "notion_incremental", "snapshots"):
        raise InputError("SNAPSHOT_LOCATOR_INVALID")
    if claimed_parts[-2] != page_id:
        raise InputError("SNAPSHOT_PAGE_MISMATCH")
    fingerprint = claimed_parts[-1]
    if len(fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in fingerprint.lower()):
        raise InputError("SNAPSHOT_FINGERPRINT_LOCATOR_INVALID")
    target = root / "data" / "notion_incremental" / "snapshots" / page_id / fingerprint / "blocks.json"
    if PureWindowsPath(claimed) != PureWindowsPath(str(target.parent)):
        raise InputError("SNAPSHOT_OUTSIDE_EXPECTED_VAULT")
    resolved_root = root.resolve()
    resolved = target.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise InputError("SNAPSHOT_PATH_ESCAPE")
    return resolved


def _extract(blocks: list) -> tuple[list[dict[str, Any]], int, list[str]]:
    extracted: list[dict[str, Any]] = []
    flags: list[str] = []
    count = 0
    def visit(nodes: list, parents: tuple[str, ...], depth: int) -> None:
        nonlocal count
        if depth > 8:
            raise InputError("SNAPSHOT_EXCEEDS_BLOCK_DEPTH")
        for block in nodes:
            count += 1
            if count > MAX_BLOCKS_PER_PAGE:
                raise InputError("SNAPSHOT_EXCEEDS_BLOCK_COUNT")
            if not isinstance(block, dict):
                raise InputError("SNAPSHOT_BLOCK_SHAPE_INVALID")
            ident = block.get("id")
            kind = block.get("type")
            if not isinstance(ident, str) or not ident or not isinstance(kind, str):
                raise InputError("SNAPSHOT_BLOCK_ID_TYPE_MISSING")
            value = block.get(kind) or {}
            if not isinstance(value, dict):
                raise InputError("SNAPSHOT_CONTENT_SHAPE_INVALID")
            rt = value.get("rich_text") or []
            if not isinstance(rt, list):
                raise InputError("SNAPSHOT_RICH_TEXT_INVALID")
            text = "".join(str(x.get("plain_text", "")) for x in rt if isinstance(x, dict)).strip()
            if text:
                extracted.append({"block_id": ident, "block_path": list(parents + (ident,)),
                                  "block_type": kind, "text": text,
                                  "scope": "NOTION_BLOCK_TEXT_ONLY"})
            if kind in {"file", "pdf", "image", "audio", "video"}:
                flags.append("ATTACHMENT_BYTES_NOT_ACQUIRED")
            if kind in {"child_page", "child_database"}:
                flags.append("CHILD_PAGE_NOT_RECURSIVELY_ACQUIRED")
            if block.get("_children_error"):
                flags.append("CHILD_BLOCK_READ_ERROR")
            children = block.get("_children")
            if block.get("has_children") and not isinstance(children, list):
                flags.append("CHILD_BLOCKS_UNAVAILABLE")
            if isinstance(children, list):
                visit(children, parents + (ident,), depth + 1)
    visit(blocks, (), 0)
    return extracted, count, sorted(set(flags))


def build_snapshot_receipt(report_dir: Path, vault_root: Path) -> dict[str, Any]:
    router = build_receipt(report_dir)
    queue = json.loads((report_dir / "INCREMENTAL_QUEUE.json").read_text(encoding="utf-8-sig"))
    entries = []
    for row in queue:
        page_id = row["notion_page_id"]
        result: dict[str, Any] = {"source_id": f"notion:{page_id}", "notion_page_id": page_id,
                    "state": "SNAPSHOT_HOLD", "block_status": row.get("block_status"),
                    "extracted": [], "snapshot_sha256": None, "flags": [],
                    "external_capture": False, "semantic_mining": False,
                    "index_owner_receipt": None}
        if row.get("block_status") != "OK":
            result["flags"].append("SOURCE_BLOCK_STATUS_NOT_OK")
            entries.append(result)
            continue
        try:
            path = _folder(vault_root, row)
            if not path.is_file():
                raise InputError("SNAPSHOT_FILE_NOT_FOUND")
            if path.stat().st_size > MAX_SNAPSHOT_BYTES:
                raise InputError("SNAPSHOT_SIZE_EXCEEDS_LIMIT")
            data = path.read_bytes()
            if len(data) > MAX_SNAPSHOT_BYTES:
                raise InputError("SNAPSHOT_SIZE_EXCEEDS_LIMIT")
            blocks = json.loads(data.decode("utf-8-sig"))
            if not isinstance(blocks, list):
                raise InputError("SNAPSHOT_BLOCKS_NOT_ARRAY")
            extracted, count, flags = _extract(blocks)
            result.update({"state": "NOTION_BLOCK_TEXT_EXTRACTED" if extracted else "NOTION_BLOCK_NO_TEXT",
                           "snapshot_sha256": hashlib.sha256(data).hexdigest(),
                           "snapshot_bytes": len(data), "block_count": count,
                           "extracted": extracted, "flags": flags})
        except (InputError, ValueError, UnicodeError, OSError, json.JSONDecodeError) as exc:
            result["state"] = "SNAPSHOT_HOLD"
            result["flags"] = [str(exc) if isinstance(exc, InputError) else "SNAPSHOT_UNREADABLE"]
        entries.append(result)
    return {"schema": SCHEMA, "created_at": datetime.now(timezone.utc).isoformat(),
            "queue_sha256": router["queue_sha256"], "router_input_count": router["input_count"],
            "snapshot_evidence_count": sum(bool(x["snapshot_sha256"]) for x in entries),
            "text_extracted_count": sum(x["state"] == "NOTION_BLOCK_TEXT_EXTRACTED" for x in entries),
            "held_count": sum(x["state"] == "SNAPSHOT_HOLD" for x in entries),
            "entries": entries, "network_used": False, "source_queue_changed": False,
            "external_original_acquired": False, "semantic_mining_executed": False,
            "indexing_executed": False, "canonical_promotion": False,
            "queue_acknowledged": False, "next": "EXTERNAL_SOURCE_AND_ATTACHMENT_ACQUISITION_WITH_RECEIPTS"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault-root", type=Path, required=True)
    ap.add_argument("--reports", type=Path, default=None)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    root = args.vault_root.resolve()
    reports = (args.reports or root / "reports").resolve()
    originals = {n: hashlib.sha256((reports / n).read_bytes()).hexdigest() for n in
                 ("INCREMENTAL_QUEUE.json", "MINING_INBOX_HANDOFF.json", "INCREMENTAL_SUMMARY.json")}
    result = build_snapshot_receipt(reports, root)
    if any(hashlib.sha256((reports / n).read_bytes()).hexdigest() != v for n, v in originals.items()):
        raise InputError("QUEUE_CHANGED_DURING_SNAPSHOT_EXTRACTION")
    output = (args.output or reports / "SOURCE_VAULT_SNAPSHOT_EVIDENCE.json").resolve()
    if output in {reports / n for n in originals}:
        raise InputError("REFUSE_TO_OVERWRITE_SOURCE_INPUT")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + ".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, output)
    print(json.dumps({"result": "PASS_LOCAL_NOTION_BLOCK_EXTRACTION_ONLY",
                      "total": len(result["entries"]), "snapshots": result["snapshot_evidence_count"],
                      "with_text": result["text_extracted_count"], "held": result["held_count"],
                      "semantic_mining_executed": False}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
