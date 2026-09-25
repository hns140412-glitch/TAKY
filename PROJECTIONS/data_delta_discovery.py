#!/usr/bin/env python3
"""Classify Google Drive DATA changes before incremental indexing."""
from __future__ import annotations

from typing import Any

DERIVED_PREFIXES = (
    "HANDOFF/","C2S/","CURRENT/","HISTORY/","MINED/"
)
DERIVED_NAME_TOKENS = (
    "HANDOFF","CHECKPOINT","CURRENT_POINTER","PROMOTION_RECEIPT",
    "SCHEMA_CONTRACT","COMPATIBILITY_MAP","ROLE_CONTRACT"
)


def classify_candidate(
    item: dict[str, Any],
    *,
    known_source_ids: set[str],
    known_content_hashes: set[str] | None = None,
    in_inbox: bool = False,
) -> dict[str, Any]:
    known_content_hashes = known_content_hashes or set()
    sid = str(item.get("source_id") or item.get("id") or "")
    title = str(item.get("title") or "")
    locator = str(item.get("locator") or "")
    content_hash = item.get("content_hash")
    modified = bool(item.get("modified_since_baseline", False))
    version_hint = bool(item.get("version_hint", False))

    upper = title.upper()
    derived = (
        locator.startswith(DERIVED_PREFIXES)
        or any(upper.startswith(x) for x in ("HANDOFF/","C2S/","CURRENT/","HISTORY/","MINED/"))
        or any(tok in upper for tok in DERIVED_NAME_TOKENS)
    )

    if derived:
        classification = "DERIVED_NOT_SOURCE"
    elif content_hash and content_hash in known_content_hashes:
        classification = "EXACT_DUPLICATE"
    elif sid and sid in known_source_ids and modified:
        classification = "UPDATED_SOURCE"
    elif version_hint:
        classification = "VERSION_CANDIDATE"
    elif sid and sid not in known_source_ids:
        classification = "NEW_SOURCE"
    else:
        classification = "IGNORE"

    return {
        "source_id": sid,
        "title": title,
        "classification": classification,
        "priority": "HIGH" if in_inbox else "NORMAL",
        "accepted_for_incremental_index": classification in {
            "NEW_SOURCE","UPDATED_SOURCE","VERSION_CANDIDATE"
        },
        "requires_source_validation": classification in {
            "NEW_SOURCE","UPDATED_SOURCE","VERSION_CANDIDATE"
        },
    }
