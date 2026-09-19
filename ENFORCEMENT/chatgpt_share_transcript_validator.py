#!/usr/bin/env python3
"""Validate a transcript-only share-page derivative before NotebookLM intake."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REQUIRED = [
    "STATUS: TRANSCRIPT_ONLY / NOTEBOOKLM_INPUT_CANDIDATE",
    "SCOPE: SAVED PAGE linear_conversation; USER↔ASSISTANT only",
    "EXCLUDED: SYSTEM / DEVELOPER / TOOL / bootstrap / session / authentication / application state",
    "CLAIM_BOUNDARY: This transcript does not prove complete account-history coverage.",
]
FORBIDDEN = [
    re.compile(r"accessToken", re.I),
    re.compile(r"client-bootstrap", re.I),
    re.compile(r'"authStatus"\s*:', re.I),
    re.compile(r'"session"\s*:\s*\{\s*"user"', re.I),
    re.compile(r"Authorization\s*[:=]", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{12,}", re.I),
]
MESSAGE_HEADER = re.compile(r"^## \[\d{4}\] (USER|ASSISTANT) — ", re.M)
INTERNAL_CONTENT = re.compile(r"^CONTENT_TYPE:\s*(thoughts|reasoning_recap|model_editable_context|code|tool|analysis|system)\s*$", re.I | re.M)

def main(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [x for x in REQUIRED if x not in text]
    if missing:
        print("FAIL: missing required transcript declarations: " + repr(missing))
        return 1
    hits = [p.pattern for p in FORBIDDEN if p.search(text)]
    if hits:
        print("FAIL: forbidden session/auth pattern(s): " + repr(hits))
        return 1
    if INTERNAL_CONTENT.search(text):
        print("FAIL: internal/non-user-visible content type leaked into sanitized transcript")
        return 1
    count = len(MESSAGE_HEADER.findall(text))
    if count == 0:
        print("FAIL: no USER/ASSISTANT transcript messages")
        return 1
    if "<script" in text.lower() or "<!doctype" in text.lower():
        print("FAIL: raw HTML leaked into sanitized transcript")
        return 1
    print(f"PASS: transcript-only derivative messages={count}")
    return 0

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("transcript", type=Path)
    args=ap.parse_args()
    raise SystemExit(main(args.transcript))
