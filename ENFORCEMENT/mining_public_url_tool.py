#!/usr/bin/env python3
"""Explicit-public-URL acquisition tool for the existing Mining provider runner.

Reuses the established SSRF/redirect/bounds-controlled reference adapter.
Search phrases are NOT interpreted as URLs; no web crawling, credentials,
automatic Index writes, content-truth claims, or publisher trust is inferred.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit
import hashlib
from reference_acquisition_adapter import acquire


def build_public_url_tool(destination_dir:Path, *, acquisition=acquire,
                          max_bytes:int=25*1024*1024):
    """Return a callable WEB provider that fetches an explicitly named source URL.

    The host chooses storage and explicitly registers the callable with
    mining_operation_runner.run_with_providers. Returned source evidence
    remains unverified until independent source/claim review.
    """
    directory=Path(destination_dir)
    def handle(request:dict)->dict:
        query=str(request.get("query") or "").strip()
        parsed=urlsplit(query)
        if (parsed.scheme.lower() not in {"http","https"} or not parsed.hostname
            or query != query.split()[0]):
            return {"state":"FAILED","error":"EXPLICIT_PUBLIC_URL_REQUIRED",
                    "external_fetch_performed":False}
        result=acquisition(query,destination_dir=directory,max_bytes=max_bytes)
        if not result.get("pass"):
            detected=(result.get("detected") or ["ACQUISITION_FAILED"])[0]
            return {"state":"FAILED","error":str(detected),
                    "external_fetch_performed":str(detected) not in {
                        "REFERENCE_URL_SCHEME_FORBIDDEN","REFERENCE_URL_LOCALHOST_FORBIDDEN",
                        "REFERENCE_URL_NONPUBLIC_TARGET_FORBIDDEN",
                        "REFERENCE_URL_USERINFO_FORBIDDEN",
                    }}
        status=str(result.get("acquisition_state") or "")
        if status=="ACCESS_RESTRICTED":
            return {"state":"FAILED","error":"ACCESS_HOLD",
                    "external_fetch_performed":True}
        if status!="ACQUIRED_AND_PRESERVED" or result.get("preserved") is not True:
            return {"state":"FAILED","error":"BINARY_NOT_PRESERVED",
                    "external_fetch_performed":True}
        # Verify the physically preserved RAW file, not a claimed download flag.
        raw_path=result.get("preserved_path")
        try:
            path=Path(raw_path).resolve(strict=True)
            path.relative_to(directory.resolve())
            if not path.is_file(): raise ValueError("SOURCE_NOT_A_FILE")
            data=path.read_bytes()
            digest=hashlib.sha256(data).hexdigest()
            if not data or digest!=result.get("sha256") or len(data)!=result.get("content_length"):
                raise ValueError("PRESERVED_SOURCE_INTEGRITY_MISMATCH")
        except (OSError,ValueError,TypeError) as exc:
            return {"state":"FAILED","error":"PRESERVED_SOURCE_INTEGRITY_MISMATCH",
                    "error_type":type(exc).__name__,"external_fetch_performed":True}
        final=str(result.get("final_url") or query)
        return {
            "state":"SUCCESS",
            "external_fetch_performed":True,
            "source_acquisition":{
                "state":"ACQUIRED_AND_PRESERVED",
                "sha256":digest,
                "size_bytes":len(data),
                "preserved_path":str(path),
                "final_url":final,
                "content_type":result.get("content_type"),
                "canonical_promotion":False,
            },
            "response":{"results":[{
                "source_id":"acquired-sha256:"+digest,
                "url":final,
                "title":Path(urlsplit(final).path).name or "original-source",
                "source_class":"UNKNOWN",
                "claim":"Original bytes acquired; substantive claims not verified",
                "direct_support":False,
                "fresh_enough":False,
                "independent_support_count":1,
            }]},
        }
    return handle
