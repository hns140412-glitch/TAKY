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
    """Extract only actually present Notion-authored text, with original block anchors.

    This is NOT image/file OCR, linked-page expansion, rendered text inference,
    public-web original acquisition, or semantic Mining. Unknown/unrepresented
    content remains an explicit coverage flag even when other text is present.
    """
    extracted: list[dict[str, Any]] = []
    flags: list[str] = []
    count = 0
    text_types = {
        "paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item",
        "numbered_list_item", "to_do", "toggle", "quote", "callout", "code",
        "template",
    }
    structural = {
        "table", "column_list", "column", "divider", "breadcrumb",
        "table_of_contents", "synced_block",
    }
    media = {"file", "pdf", "image", "audio", "video"}
    source_links = {"bookmark", "embed", "link_preview", "link_to_page"}
    children_types = {"child_page", "child_database"}

    def rich(items: object) -> str:
        if not isinstance(items, list):
            raise InputError("SNAPSHOT_RICH_TEXT_INVALID")
        return "".join(str((x.get("plain_text")
                            if x.get("plain_text") is not None
                            else (x.get("text") or {}).get("content") or ""))
                       for x in items if isinstance(x, dict)).strip()

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
            current_path = list(parents + (ident,))

            def add(value_text: str, field: str, *, cell: int | None = None,
                    scope: str = "NOTION_BLOCK_TEXT_ONLY") -> None:
                if not value_text:
                    return
                item: dict[str, Any] = {
                    "block_id": ident, "block_path": current_path,
                    "block_type": kind, "text": value_text,
                    "field": field, "scope": scope,
                }
                if cell is not None:
                    item["cell_index"] = cell
                extracted.append(item)

            if kind in text_types:
                add(rich(value.get("rich_text") or []), "rich_text")
            elif kind == "table_row":
                cells = value.get("cells")
                if not isinstance(cells, list):
                    raise InputError("SNAPSHOT_TABLE_CELLS_INVALID")
                for col, cell in enumerate(cells):
                    add(rich(cell), "cells", cell=col)
            elif kind == "equation":
                expression = value.get("expression")
                if not isinstance(expression, str):
                    raise InputError("SNAPSHOT_EQUATION_INVALID")
                add(expression.strip(), "expression")
            elif kind in media:
                add(rich(value.get("caption") or []), "caption")
                flags.append("ATTACHMENT_BYTES_NOT_ACQUIRED")
                if kind == "image":
                    flags.append("IMAGE_CONTENT_NOT_OCR_EXTRACTED")
            elif kind in children_types:
                # A child-page title is locator metadata, not its page content.
                add(str(value.get("title") or "").strip(), "title",
                    scope="NOTION_CHILD_TITLE_METADATA_ONLY")
                flags.append("CHILD_PAGE_NOT_RECURSIVELY_ACQUIRED")
            elif kind in source_links:
                add(rich(value.get("caption") or []), "caption")
                flags.append("LINKED_OR_EMBEDDED_SOURCE_NOT_ACQUIRED")
            elif kind == "synced_block":
                if value.get("synced_from"):
                    flags.append("SYNCED_BLOCK_ORIGINAL_NOT_ACQUIRED")
            elif kind not in structural:
                flags.append("UNSUPPORTED_NOTION_BLOCK_TYPE:" + kind)

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
            semantic_count = sum(x["scope"] == "NOTION_BLOCK_TEXT_ONLY" for x in extracted)
            metadata_count = len(extracted) - semantic_count
            result.update({"state": "NOTION_BLOCK_TEXT_EXTRACTED" if semantic_count else "NOTION_BLOCK_NO_TEXT",
                           "snapshot_sha256": hashlib.sha256(data).hexdigest(),
                           "snapshot_bytes": len(data), "block_count": count,
                           "semantic_text_item_count": semantic_count,
                           "metadata_only_item_count": metadata_count,
                           "content_completeness": "PARTIAL_MATERIAL_OR_LINKED_CONTENT_OPEN" if flags else "NOTION_BLOCK_TEXT_ONLY_NOT_EXTERNAL_ORIGINAL",
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
