#!/usr/bin/env python3
"""Controlled external reference acquisition adapter.

Fetches explicit public HTTP(S) reference URLs only.
Security boundaries:
- no file:// or custom schemes
- no localhost/private/link-local/multicast/reserved targets
- every redirect target is revalidated
- bounded download size
- bounded redirects/timeouts
- no shell execution
- no canonical promotion or indexing authority
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VERSION = "TAKY_REFERENCE_ACQUISITION_ADAPTER_V1"
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_REDIRECTS = 5
ALLOWED_SCHEMES = {"http", "https"}


class AcquisitionError(RuntimeError):
    pass


def _clean(value: object) -> str:
    return str(value or "").strip()


def _is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_public_url(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(_clean(url))
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise AcquisitionError("REFERENCE_URL_SCHEME_FORBIDDEN")
    if not parsed.hostname:
        raise AcquisitionError("REFERENCE_URL_HOST_MISSING")
    if parsed.username or parsed.password:
        raise AcquisitionError("REFERENCE_URL_USERINFO_FORBIDDEN")

    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise AcquisitionError("REFERENCE_URL_LOCALHOST_FORBIDDEN")

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise AcquisitionError("REFERENCE_URL_DNS_RESOLUTION_FAILED") from exc

    ips = sorted({info[4][0] for info in infos})
    if not ips:
        raise AcquisitionError("REFERENCE_URL_DNS_EMPTY")
    if not all(_is_public_ip(ip) for ip in ips):
        raise AcquisitionError("REFERENCE_URL_NONPUBLIC_TARGET_FORBIDDEN")

    return {
        "url": urllib.parse.urlunsplit(parsed),
        "scheme": parsed.scheme.lower(),
        "host": host,
        "resolved_ips": ips,
    }


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, max_redirects: int):
        self.max_redirects = max_redirects

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        count = int(req.headers.get("X-TAKY-Redirect-Count", "0"))
        if count >= self.max_redirects:
            raise AcquisitionError("REFERENCE_REDIRECT_LIMIT_EXCEEDED")
        validate_public_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.add_header("X-TAKY-Redirect-Count", str(count + 1))
        return redirected


def _safe_filename(url: str, content_type: str | None) -> str:
    parsed = urllib.parse.urlsplit(url)
    name = Path(urllib.parse.unquote(parsed.path)).name
    if name and name not in {".", ".."}:
        return name
    suffix = ""
    ct = (content_type or "").split(";", 1)[0].lower()
    suffix = {
        "application/pdf": ".pdf",
        "text/html": ".html",
        "text/plain": ".txt",
        "application/zip": ".zip",
        "application/json": ".json",
    }.get(ct, ".bin")
    return "reference" + suffix


def acquire(
    url: str,
    *,
    destination_dir: Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    user_agent: str = "TAKY-Reference-Acquisition/1.0",
) -> dict[str, Any]:
    if max_bytes < 1:
        return {"pass": False, "detected": ["REFERENCE_MAX_BYTES_INVALID"]}
    if timeout_seconds < 1:
        return {"pass": False, "detected": ["REFERENCE_TIMEOUT_INVALID"]}

    try:
        initial = validate_public_url(url)
        opener = urllib.request.build_opener(_SafeRedirect(max_redirects))
        req = urllib.request.Request(initial["url"], headers={"User-Agent": user_agent, "Accept": "*/*"})
        with opener.open(req, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            final_validation = validate_public_url(final_url)
            content_type = response.headers.get("Content-Type")
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > max_bytes:
                        return {
                            "pass": True,
                            "adapter_version": VERSION,
                            "acquisition_state": "ACCESSIBLE_REMOTE_SOURCE",
                            "source_url": initial["url"],
                            "final_url": final_url,
                            "reason": "CONTENT_LENGTH_EXCEEDS_LIMIT",
                            "content_length": int(content_length),
                            "max_bytes": max_bytes,
                            "preserved": False,
                            "canonical_promotion": False,
                        }
                except ValueError:
                    pass

            data = bytearray()
            while True:
                chunk = response.read(min(1024 * 1024, max_bytes + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > max_bytes:
                    return {
                        "pass": True,
                        "adapter_version": VERSION,
                        "acquisition_state": "ACCESSIBLE_REMOTE_SOURCE",
                        "source_url": initial["url"],
                        "final_url": final_url,
                        "reason": "STREAM_EXCEEDS_LIMIT",
                        "downloaded_bytes": len(data),
                        "max_bytes": max_bytes,
                        "preserved": False,
                        "canonical_promotion": False,
                    }

            destination_dir.mkdir(parents=True, exist_ok=True)
            filename = _safe_filename(final_url, content_type)
            digest = hashlib.sha256(data).hexdigest()
            stem = Path(filename).stem[:80] or "reference"
            suffix = Path(filename).suffix[:16]
            path = destination_dir / f"{stem}__{digest[:12]}{suffix}"
            path.write_bytes(data)

            return {
                "pass": True,
                "adapter_version": VERSION,
                "acquisition_state": "ACQUIRED_AND_PRESERVED",
                "source_url": initial["url"],
                "final_url": final_url,
                "resolved_ips": final_validation["resolved_ips"],
                "content_type": content_type,
                "content_length": len(data),
                "sha256": digest,
                "preserved_path": str(path),
                "preserved": True,
                "canonical_promotion": False,
                "index_result": None,
                "next_handoff": "INDEX_EXISTENCE_DUPLICATE_VERSION_CHECK",
            }
    except urllib.error.HTTPError as exc:
        state = "ACCESS_RESTRICTED" if exc.code in {401, 403} else "ACCESSIBLE_REMOTE_SOURCE"
        return {
            "pass": True,
            "adapter_version": VERSION,
            "acquisition_state": state,
            "source_url": _clean(url),
            "reason": f"HTTP_{exc.code}",
            "preserved": False,
            "canonical_promotion": False,
        }
    except urllib.error.URLError as exc:
        return {
            "pass": False,
            "adapter_version": VERSION,
            "detected": ["REFERENCE_NETWORK_ERROR"],
            "detail": str(exc.reason),
        }
    except AcquisitionError as exc:
        return {
            "pass": False,
            "adapter_version": VERSION,
            "detected": [str(exc)],
        }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--destination-dir", type=Path, required=True)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = ap.parse_args()
    result = acquire(
        args.url,
        destination_dir=args.destination_dir,
        max_bytes=args.max_bytes,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
