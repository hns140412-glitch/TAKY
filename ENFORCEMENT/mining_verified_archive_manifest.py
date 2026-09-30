#!/usr/bin/env python3
"""Read-only physical ZIP/SOURCE_MANIFEST gate before owner Index classification."""
from __future__ import annotations
import hashlib, io, json, zipfile
from pathlib import Path
from urllib.parse import urlsplit

MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_FILES = 32

def review_original_archive(path: Path, existing_rows: list[dict] | None = None) -> dict:
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if (len(names)>MAX_FILES or len(names)!=len(set(names))
            or any(n.startswith("/") or "\\" in n or ".." in Path(n).parts for n in names)
            or "SOURCE_MANIFEST.json" not in names
            or z.testzip() is not None):
            raise ValueError("ARCHIVE_STRUCTURE_OR_CRC_INVALID")
        manifest=json.loads(z.read("SOURCE_MANIFEST.json"))
        entries=manifest.get("source_entries")
        if not isinstance(entries,list) or len(entries)!=len(names)-1:
            raise ValueError("SOURCE_MANIFEST_COUNT_INVALID")
        known=existing_rows or []
        result=[]
        for e in entries:
            name=e.get("name")
            if not isinstance(name,str) or name not in names or name=="SOURCE_MANIFEST.json":
                raise ValueError("MANIFEST_FILENAME_NOT_IN_ARCHIVE")
            info=z.getinfo(name)
            declared=int(e.get("bytes") or 0)
            if not 0<declared<=MAX_SOURCE_BYTES or info.file_size!=declared:
                raise ValueError("MANIFEST_SIZE_MISMATCH")
            blob=z.read(name)
            digest=hashlib.sha256(blob).hexdigest()
            if digest!=e.get("sha256"):
                raise ValueError("MANIFEST_HASH_MISMATCH")
            locator=e.get("official_url")
            parsed=urlsplit(locator or "")
            if parsed.scheme!="https" or parsed.hostname!="www.ice.go.kr" or not parsed.path.startswith("/upload/ice/"):
                raise ValueError("SOURCE_LOCATOR_INVALID")
            matches=[str(r.get("source_id")) for r in known
                     if r.get("content_hash") and r["content_hash"]==digest]
            title=[str(r.get("source_id")) for r in known
                   if str(r.get("canonical_title") or "").casefold()==name.casefold() and
                   str(r.get("source_id")) not in matches]
            result.append({"filename":name,"source_url":locator,"source_post":manifest.get("publisher_post"),
                           "sha256":digest,"size_bytes":len(blob),
                           "classification":"EXACT_DUPLICATE_CANDIDATE" if matches else
                           "POSSIBLE_VERSION_HOLD" if title else "NO_KNOWN_HASH_MATCH_OWNER_REVIEW_PENDING",
                           "exact_hash_matches":matches,"same_title_candidates":title,
                           "index_owner_authorized":False,"current_promoted":False})
        if {e["name"] for e in entries}!={n for n in names if n!="SOURCE_MANIFEST.json"}:
            raise ValueError("ARCHIVE_ENTRY_NOT_MANIFESTED")
    return {"schema":"TAKY_VERIFIED_ARCHIVE_INDEX_CANDIDATES_V1",
            "state":"ORIGINAL_BYTES_VERIFIED_INDEX_OWNER_REVIEW_PENDING",
            "files":result,"file_count":len(result),
            "index_existing_rows_compared":len(known),
            "canonical_write":False,"current_promoted":False}
