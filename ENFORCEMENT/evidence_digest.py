#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA="TAKY_CANONICAL_JSON_DIGEST_V1"

def canonical_json_bytes(value:Any)->bytes:
    if isinstance(value,(str,Path)):
        data=json.loads(Path(value).read_text(encoding="utf-8-sig"))
    else:
        data=value
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",",":"),
    ).encode("utf-8")

def canonical_json_sha256(value:Any)->str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
