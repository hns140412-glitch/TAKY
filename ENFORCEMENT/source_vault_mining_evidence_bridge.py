#!/usr/bin/env python3
"""Verified local SOURCE VAULT bytes -> Mining V2 source-snapshot candidates.

This is a read-only *input adapter*, not the semantic Mining engine or an Index
writer. It never invents frontier claims, excerpts, reviewer identity, or a
successful Mining/Index/consumer result. Output contains source text: keep it
inside the existing private SOURCE VAULT, never in GitHub/CI artifacts/logs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path

from source_vault_handoff_bridge import build_receipt, REQUIRED, InputError
from source_vault_snapshot_evidence import build_snapshot_receipt
from source_vault_external_acquisition import OUTPUT, _read_prior, _saved_bytes_match

SCHEMA = "TAKY_SOURCE_VAULT_MINING_V2_INPUT_CANDIDATES_V1"
MINING_SOURCE_SCHEMA = "TAKY_MINING_SOURCE_SNAPSHOT_V1"
MAX_TEXT_BYTES = 25 * 1024 * 1024
TEXT_TYPES = {"text/plain", "text/markdown", "text/html", "application/xhtml+xml", "application/json"}
IGNORE_TAGS = {"script", "style", "template", "svg", "noscript"}
DEFAULT_OUTPUT = "SOURCE_VAULT_MINING_V2_INPUT_PRIVATE.json"


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in IGNORE_TAGS:
            self.hidden += 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "br", "tr"} and not self.hidden:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in IGNORE_TAGS and self.hidden:
            self.hidden -= 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr"} and not self.hidden:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def verified_text(data: bytes, mime: str) -> str:
    if len(data) > MAX_TEXT_BYTES:
        raise InputError("EXTERNAL_BYTES_LIMIT")
    kind = str(mime or "").split(";", 1)[0].strip().lower()
    if kind not in TEXT_TYPES:
        raise InputError("EXTERNAL_MIME_NOT_TEXT")
    try:
        raw = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("EXTERNAL_TEXT_ENCODING_UNVERIFIED") from exc
    if kind in {"text/html", "application/xhtml+xml"}:
        parser = VisibleText()
        parser.feed(raw)
        raw = parser.text()
    if not raw.strip():
        raise InputError("EXTERNAL_VISIBLE_TEXT_EMPTY")
    return raw


def _snapshot(source_id: str, locator: str, content: str, *,
              scope: str, original_sha256: str, recorded_at: str | None,
              fragment_anchors: list | None = None) -> dict:
    if not isinstance(content, str) or not content.strip() or not locator:
        raise InputError("INCOMPLETE_SOURCE_SNAPSHOT")
    return {
        "schema": MINING_SOURCE_SCHEMA,
        "source_id": source_id,
        "retrieval_state": "FETCHED",
        "source_locator": locator,
        "source_text": content,
        # Mining V2 audits SHA256 of exact source_text UTF-8. RAW byte digest
        # is separate, not replaced by a normalized/rendered text hash.
        "source_sha256": digest(content.encode("utf-8")),
        "original_sha256": original_sha256,
        "retrieved_at": recorded_at or datetime.now(timezone.utc).isoformat(),
        "source_updated_at": None,
        "source_scope": scope,
        "fragment_anchors": fragment_anchors or [],
        "source_claim_reviewed": False,
        "external_original_is_not_notion_block_text": scope == "PUBLIC_TEXT_ORIGINAL",
    }


def prepare(report_dir: Path, vault_root: Path) -> dict:
    root = vault_root.resolve()
    reports = report_dir.resolve()
    if not reports.is_relative_to(root):
        raise InputError("REPORTS_OUTSIDE_VAULT")
    before = {name: digest((reports / name).read_bytes()) for name in REQUIRED}
    router = build_receipt(reports)
    notion_receipt = build_snapshot_receipt(reports, root)
    if notion_receipt["queue_sha256"] != before[REQUIRED[0]]:
        raise InputError("NOTION_SNAPSHOT_QUEUE_REVISION_MISMATCH")
    if notion_receipt["router_input_count"] != router["input_count"]:
        raise InputError("NOTION_SNAPSHOT_COUNT_MISMATCH")
    local_by_id = {row["source_id"]: row for row in notion_receipt["entries"]}
    acquisition_path = reports / OUTPUT
    ledger = _read_prior(acquisition_path)
    if acquisition_path.exists():
        metadata = json.loads(acquisition_path.read_text(encoding="utf-8-sig"))
        if metadata.get("last_input_hashes") != before:
            raise InputError("EXTERNAL_LEDGER_INPUT_REVISION_MISMATCH")
    most_recent = {}
    for item in ledger:
        most_recent[(item.get("source_id"), item.get("url"))] = item

    source_snapshots = []
    held = []
    counts = {"notion_blocks": 0, "public_original": 0, "held": 0}
    for route in router["routes"]:
        source_id = route["source_id"]
        item = local_by_id.get(source_id)
        if item is None:
            raise InputError("MISSING_NOTION_EVIDENCE_ROW")
        flags = item.get("flags") or []
        if item.get("state") == "NOTION_BLOCK_TEXT_EXTRACTED" and not flags:
            chunks = item.get("extracted") or []
            text = "\n".join(chunk["text"] for chunk in chunks)
            source_snapshots.append(_snapshot(
                source_id + ":notion_blocks", route["source_id"], text,
                scope="NOTION_BLOCK_TEXT_ONLY", original_sha256=item["snapshot_sha256"],
                recorded_at=notion_receipt["created_at"],
                fragment_anchors=[{"block_id": chunk["block_id"],
                                   "block_path": chunk["block_path"]} for chunk in chunks]
            ))
            counts["notion_blocks"] += 1
        else:
            held.append({"source_id": source_id, "part": "NOTION_BLOCK_TEXT",
                         "reason": flags or ["NOTION_TEXT_NOT_AVAILABLE"]})
        if route["kind"] != "PUBLIC_URL_CANDIDATE" or not route["source_url"]:
            continue
        event = most_recent.get((source_id, route["source_url"]))
        if not event or event.get("state") != "ACQUIRED_AND_PRESERVED":
            held.append({"source_id": source_id, "part": "PUBLIC_ORIGINAL",
                         "reason": ["NO_VERIFIED_EXTERNAL_ACQUISITION"]})
            continue
        if not _saved_bytes_match(event, root):
            held.append({"source_id": source_id, "part": "PUBLIC_ORIGINAL",
                         "reason": ["EXTERNAL_BYTES_MISSING_OR_HASH_CHANGED"]})
            continue
        file = (root / event["preserved_relative_path"]).resolve()
        data = file.read_bytes()
        if digest(data) != event["sha256"]:
            raise InputError("EXTERNAL_SOURCE_CHANGED_DURING_READ")
        try:
            text = verified_text(data, event.get("content_type"))
        except InputError as exc:
            held.append({"source_id": source_id, "part": "PUBLIC_ORIGINAL",
                         "reason": [str(exc)]})
            continue
        source_snapshots.append(_snapshot(
            source_id + ":public_original", route["source_url"], text,
            scope="PUBLIC_TEXT_ORIGINAL", original_sha256=digest(data),
            recorded_at=event.get("recorded_at"),
        ))
        counts["public_original"] += 1
    if {name: digest((reports / name).read_bytes()) for name in REQUIRED} != before:
        raise InputError("PENDING_INPUT_CHANGED_DURING_EXTRACTION")
    counts["held"] = len(held)
    return {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_queue_sha256": before[REQUIRED[0]],
        "input_hashes": before,
        "input_count": router["input_count"],
        # This list may be consumed as the EXISTING Mining V2 audit's
        # source_snapshots, only after matching source_id/source_locator in
        # separately generated evidence and host-authorized claim review.
        "source_snapshots": source_snapshots,
        "held": held,
        "counts": counts,
        "claim_reviews": [],
        "mining_frontier_generated": False,
        "provider_independence_verified": False,
        "semantic_mining_executed": False,
        "indexing_executed": False,
        "queue_acknowledged": False,
        "canonical_promotion": False,
        "owner_acceptance": None,
        "next": "EXISTING_MINING_V2_FRONTIER_AND_INDEPENDENT_CLAIM_REVIEW",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault-root", type=Path, required=True)
    ap.add_argument("--reports", type=Path)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    root = a.vault_root.resolve()
    reports = (a.reports or root / "reports").resolve()
    output = (a.output or reports / DEFAULT_OUTPUT).resolve()
    if not output.is_relative_to(root):
        raise InputError("PRIVATE_OUTPUT_MUST_REMAIN_WITHIN_VAULT")
    forbidden = {(reports / name).resolve() for name in REQUIRED}
    forbidden.add((reports / OUTPUT).resolve())
    if output in forbidden:
        raise InputError("REFUSE_TO_OVERWRITE_SOURCE_OR_ACQUISITION_LEDGER")
    result = prepare(reports, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + ".tmp")
    try:
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, output)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(json.dumps({
        "state": "VERIFIED_SOURCE_INPUT_CANDIDATES_ONLY",
        "counts": result["counts"],
        "semantic_mining_executed": False,
        "claim_reviews_created": False,
        "queue_acknowledged": False,
        "raw_text_logged": False
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
