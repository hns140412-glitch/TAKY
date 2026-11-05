#!/usr/bin/env python3
"""Bounded SOURCE VAULT public reference acquisition using TAKY's existing adapter.

Only top-level URL-property candidates from the validated local handoff qualify.
Notion attachment URLs and arbitrary embedded links are not selected. Dry-run is
default. On an explicitly activated local run, fetched bytes stay in SOURCE VAULT
and a local append-only receipt is written. This is not semantic Mining, an
Indexing-owner review, a queue acknowledgment or canonical promotion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable

from reference_acquisition_adapter import acquire
from source_vault_handoff_bridge import build_receipt, REQUIRED, InputError, safe_url

SCHEMA = "TAKY_SOURCE_VAULT_EXTERNAL_ACQUISITION_V1"
OUTPUT = "SOURCE_VAULT_EXTERNAL_ACQUISITION.json"
MAX_PER_RUN = 3


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_prior(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if value.get("schema") != SCHEMA or value.get("append_only") is not True or not isinstance(value.get("entries"), list):
        raise InputError("EXTERNAL_ACQUISITION_LEDGER_INVALID")
    entries = value["entries"]
    if any(not isinstance(e, dict) or not e.get("event_id") or not e.get("source_id") for e in entries):
        raise InputError("EXTERNAL_ACQUISITION_LEDGER_ENTRIES_INVALID")
    if len({e["event_id"] for e in entries}) != len(entries):
        raise InputError("EXTERNAL_ACQUISITION_LEDGER_DUPLICATE_EVENT")
    return entries


def _saved_bytes_match(entry: dict[str, Any], vault_root: Path) -> bool:
    rel = entry.get("preserved_relative_path")
    digest = entry.get("sha256")
    if not isinstance(rel, str) or not isinstance(digest, str) or len(digest) != 64:
        return False
    p = (vault_root / rel).resolve()
    allowed = (vault_root / "data" / "notion_incremental" / "acquired_external").resolve()
    if not p.is_relative_to(allowed) or not p.is_file():
        return False
    return _digest(p) == digest


def _last(prior: list[dict[str, Any]], source_id: str, url: str) -> dict[str, Any] | None:
    return next((e for e in reversed(prior) if e.get("source_id") == source_id and e.get("url") == url), None)


def _append(entries: list[dict[str, Any]], payload: dict[str, Any]) -> None:
    event = {"event_id": "sv-" + hashlib.sha256(
        json.dumps([payload["source_id"], payload["url"], len(entries)], ensure_ascii=False).encode()
    ).hexdigest()[:24], "recorded_at": datetime.now(timezone.utc).isoformat(), **payload}
    entries.append(event)


def execute(report_dir: Path, vault_root: Path, *, execute_public: bool = False,
            max_fetches: int = MAX_PER_RUN, acquire_fn: Callable = acquire) -> dict[str, Any]:
    if not isinstance(max_fetches, int) or not 1 <= max_fetches <= MAX_PER_RUN:
        raise InputError("FETCH_LIMIT_MUST_BE_1_TO_3")
    root = vault_root.resolve()
    report_dir = report_dir.resolve()
    if not report_dir.is_relative_to(root):
        raise InputError("REPORTS_OUTSIDE_VAULT")
    before = {name: _digest(report_dir / name) for name in REQUIRED}
    router = build_receipt(report_dir)
    output = report_dir / OUTPUT
    prior = _read_prior(output)
    entries = list(prior)
    fetched = 0
    reused = 0
    deferred = 0
    attempt_count = 0
    cache: dict[str, dict[str, Any]] = {}
    # Prior local receipts are merely reproducible byte evidence, not a Mining/Index approval.
    for e in prior:
        if e.get("state") == "ACQUIRED_AND_PRESERVED" and _saved_bytes_match(e, root):
            cache[e.get("url", "")] = e

    for row in router["routes"]:
        if row["kind"] != "PUBLIC_URL_CANDIDATE" or not row["source_url"]:
            deferred += 1
            continue
        source_id = row["source_id"]
        url = safe_url(row["source_url"])
        if not url:
            deferred += 1
            continue
        old = _last(prior, source_id, url)
        if old and old.get("state") == "ACQUIRED_AND_PRESERVED" and _saved_bytes_match(old, root):
            reused += 1
            continue
        if old and old.get("state") == "ACCESS_RESTRICTED":
            deferred += 1
            continue
        if not execute_public:
            deferred += 1
            continue
        if url in cache:
            previous = cache[url]
            _append(entries, {"source_id": source_id, "url": url,
                              "state": "ACQUIRED_AND_PRESERVED",
                              "sha256": previous["sha256"],
                              "preserved_relative_path": previous["preserved_relative_path"],
                              "reused_url_receipt": previous["event_id"],
                              "canonical_promotion": False, "index_owner_receipt": None})
            reused += 1
            continue
        if attempt_count >= max_fetches:
            deferred += 1
            continue
        attempt_count += 1
        dest = root / "data" / "notion_incremental" / "acquired_external" / hashlib.sha256(url.encode()).hexdigest()[:24]
        # Validation of public schemes / resolved addresses / redirects / byte limits
        # belongs to the central reference_acquisition_adapter. Do not bypass it.
        result = acquire_fn(url, destination_dir=dest, max_bytes=25*1024*1024, timeout_seconds=20, max_redirects=5)
        state = result.get("acquisition_state")
        if result.get("pass") and state == "ACQUIRED_AND_PRESERVED":
            candidate = Path(result.get("preserved_path", "")).resolve()
            if not candidate.is_relative_to(dest.resolve()) or not candidate.is_file():
                raise InputError("ACQUISITION_OUTPUT_OUTSIDE_BOUNDARY")
            digest = _digest(candidate)
            if digest != result.get("sha256"):
                raise InputError("ACQUISITION_BYTES_DIGEST_MISMATCH")
            payload = {"source_id": source_id, "url": url, "state": state,
                       "sha256": digest, "preserved_relative_path": str(candidate.relative_to(root)),
                       "content_type": result.get("content_type"),
                       "content_length": candidate.stat().st_size,
                       "canonical_promotion": False, "index_owner_receipt": None}
            _append(entries, payload)
            cache[url] = entries[-1]
            fetched += 1
        else:
            if state not in {"ACCESS_RESTRICTED", "ACCESSIBLE_REMOTE_SOURCE"}:
                state = "HOLD_NETWORK_OR_VALIDATION"
            _append(entries, {"source_id": source_id, "url": url, "state": state,
                              "reason_codes": result.get("detected") or [result.get("reason") or "UNRESOLVED"],
                              "canonical_promotion": False, "index_owner_receipt": None})

    if any(_digest(report_dir / name) != digest for name, digest in before.items()):
        raise InputError("SOURCE_CHANGED_DURING_ACQUISITION")
    report = {"schema": SCHEMA, "append_only": True,
              "last_run_at": datetime.now(timezone.utc).isoformat(),
              "last_input_hashes": before, "entries": entries,
              "run": {"candidate_count": sum(r["kind"] == "PUBLIC_URL_CANDIDATE" for r in router["routes"]),
                      "new_files": fetched, "reused_existing": reused,
                      "deferred": deferred, "new_events": len(entries)-len(prior),
                      "network_executed": execute_public and attempt_count > 0,
                      "fetch_attempts": attempt_count},
              "semantic_mining_executed": False, "indexing_executed": False,
              "queue_acknowledged": False, "canonical_promotion": False}
    if execute_public:
        temp = output.with_name(output.name + ".tmp")
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, output)
    return report


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--vault-root", type=Path, required=True)
    ap.add_argument("--reports", type=Path, default=None)
    ap.add_argument("--execute-public", action="store_true", help="Explicitly permit up to 3 bounded public URL acquisitions")
    ap.add_argument("--max-fetches", type=int, default=MAX_PER_RUN)
    a=ap.parse_args()
    root=a.vault_root.resolve()
    result=execute((a.reports or root / "reports"), root, execute_public=a.execute_public, max_fetches=a.max_fetches)
    print(json.dumps({"result": "PASS_PUBLIC_ACQUISITION_STAGE_ONLY",
                      "run": result["run"], "ledger_written": a.execute_public,
                      "semantic_mining_executed": False,
                      "queue_acknowledged": False}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
