#!/usr/bin/env python3
"""Read-only source-level deep-baseline and later delta intake for existing Mining.

A WATCHLIST entry is not a deep baseline. All inputs are caller-provided evidence
candidates; comparison does not mint an Index receipt, run a provider, or promote
content to CURRENT. Only public, item-specific URLs become Mining requirements.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import parse_qsl, urlsplit, urlunsplit

SENSITIVE_QUERY = ("token", "secret", "api_key", "apikey", "auth", "signature",
                   "credential", "password", "access_key", "x-amz-", "x-goog-")
PROFILE_KINDS = {"PROFILE", "CHANNEL", "ACCOUNT", "INDEX_PAGE", "HASHTAG"}
ACTIONS = {"BASELINE_DEEP_DIVE", "DELTA_DEEP_DIVE", "SNAPSHOT_REQUIRED",
           "VERSION_OR_PROVENANCE_REVIEW"}


def _clean(value):
    return str(value or "").strip()


def _digest(value):
    val = _clean(value).lower()
    if not val:
        return None
    return val if len(val) == 64 and all(c in "0123456789abcdef" for c in val) else False


def _public_url(row):
    if not isinstance(row, dict) or row.get("public_source") is not True:
        return ""
    raw = _clean(row.get("original_url") or row.get("source_url") or row.get("url"))
    try:
        url = urlsplit(raw)
        if (url.scheme.lower() != "https" or not url.hostname
                or url.username or url.password or url.port not in (None, 443)):
            return ""
        host = url.hostname.rstrip(".").lower()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
            return ""
        try:
            ip = ipaddress.ip_address(host.strip("[]"))
            if not ip.is_global:
                return ""
        except ValueError:
            pass
        if any(any(k == bad or k.startswith(bad) or k.endswith("_" + bad)
                       for bad in SENSITIVE_QUERY)
               for k, _ in parse_qsl(url.query, keep_blank_values=True)):
            return ""
        return urlunsplit(("https", host, url.path or "/", url.query, ""))
    except (ValueError, TypeError):
        return ""


def _key(row, url):
    ns = _clean(row.get("namespace") or row.get("provider")).lower()
    native = _clean(row.get("provider_native_id"))
    author = _clean(row.get("author_id") or row.get("creator_id"))
    content = _clean(row.get("content_id"))
    if ns and native:
        return "native:" + ns + ":" + native
    if author and content:
        return "author_item:" + ns + ":" + author + ":" + content
    return "url:" + url


def _deep_baseline(row):
    if not isinstance(row, dict):
        return False
    refs = row.get("evidence_refs")
    return (row.get("baseline_state") == "DEEP_VERIFIED"
            and isinstance(_digest(row.get("content_sha256")), str)
            and isinstance(refs, list) and bool(refs)
            and all(isinstance(x, str) and x.strip() for x in refs)
            and bool(_clean(row.get("observed_at")))
            and bool(_public_url(row))
            and _clean(row.get("content_kind")).upper() not in PROFILE_KINDS)


def plan_source_work(watch, *, limit=3):
    """Pick at most three deep dives; keep unchanged and holds visible, not queued.

    The baseline is a read-only evidence snapshot, not a self-authenticating
    Index approval. Missing/weak baselines always require initial deep work.
    A missing current byte hash cannot establish an unchanged source.
    """
    if not isinstance(watch, dict):
        return {"schema": "TAKY_MINING_SOURCE_WATCH_PLAN_V1", "state": "HOLD_INPUT",
                "selected": [], "items": [], "counts": {"selected": 0},
                "canonical_promotion": False}
    limit = max(1, min(3, int(limit)))
    prior = {}
    for base in watch.get("baselines") or []:
        if not isinstance(base, dict):
            continue
        url = _public_url(base)
        if not url:
            continue
        key = _key(base, url)
        prior.setdefault(key, []).append(base)
    grouped = {}
    invalid = []
    for obs in watch.get("observations") or []:
        if not isinstance(obs, dict):
            invalid.append({"state": "HOLD_INVALID_OBSERVATION"})
            continue
        url = _public_url(obs)
        if not url:
            invalid.append({"state": "HOLD_NONPUBLIC_OR_UNSAFE_URL",
                            "source_id": _clean(obs.get("source_id"))})
            continue
        if _digest(obs.get("content_sha256")) is False:
            invalid.append({"state": "HOLD_INVALID_HASH", "url": url})
            continue
        if _clean(obs.get("content_kind")).upper() in PROFILE_KINDS:
            invalid.append({"state": "DISCOVERY_ONLY_PROFILE", "url": url})
            continue
        key = _key(obs, url)
        grouped.setdefault(key, []).append((obs, url))
    rows = list(invalid)
    selected = []
    duplicate_count = 0
    for key, versions in grouped.items():
        row, url = versions[0]
        signatures = {(_digest(r.get("content_sha256")),
                       _clean(r.get("source_version")), _clean(r.get("author_id") or r.get("creator_id")))
                      for r, _ in versions}
        if len(signatures) > 1:
            rows.append({"key": key, "url": url, "state": "HOLD_CONFLICTING_OBSERVATIONS"})
            continue
        duplicate_count += len(versions) - 1
        baselines = prior.get(key, [])
        valid = [b for b in baselines if _deep_baseline(b)]
        if len({(_digest(b.get("content_sha256")), _clean(b.get("source_version")))
                for b in valid}) > 1:
            rows.append({"key": key, "url": url, "state": "HOLD_CONFLICTING_BASELINES"})
            continue
        base = valid[0] if valid else None
        current_sha = _digest(row.get("content_sha256"))
        current_version = _clean(row.get("source_version"))
        if not base:
            state = "BASELINE_DEEP_DIVE"
        elif current_sha is None:
            state = "SNAPSHOT_REQUIRED"
        elif current_sha != _digest(base.get("content_sha256")):
            state = "DELTA_DEEP_DIVE"
        elif current_version != _clean(base.get("source_version")):
            state = "VERSION_OR_PROVENANCE_REVIEW"
        else:
            state = "UNCHANGED"
        entry = {"key": key, "url": url, "author_id": _clean(row.get("author_id") or row.get("creator_id")),
                 "content_id": _clean(row.get("content_id") or row.get("provider_native_id")),
                 "title": _clean(row.get("title")), "state": state,
                 "baseline_evidence_refs": list(base.get("evidence_refs") or []) if base else [],
                 "canonical_promotion": False}
        if state in ACTIONS:
            title = entry["title"][:140]
            author = entry["author_id"][:100]
            scope = ("establish an original-content deep baseline" if state == "BASELINE_DEEP_DIVE"
                     else "obtain original bytes and evidence to compare with baseline" if state == "SNAPSHOT_REQUIRED"
                     else "deeply compare changed original against previous baseline")
            entry["question"] = (f"At the original public content {url}, {scope}; "
                                 f"author={author}, title={title}. Verify original, dated version, "
                                 "specific claims/attachments/code, limitations and attributable responses; "
                                 "return source anchors, not an Index approval.")
            if len(selected) < limit:
                selected.append(entry)
            else:
                entry["state"] = "DEFERRED_" + state
        rows.append(entry)
    return {"schema": "TAKY_MINING_SOURCE_WATCH_PLAN_V1",
            "state": "CANDIDATE_INTAKE_ONLY",
            "selected": selected, "items": rows,
            "counts": {"observations": len(watch.get("observations") or []),
                       "deep_baseline": sum(x["state"] == "BASELINE_DEEP_DIVE" for x in rows),
                       "delta": sum(x["state"] == "DELTA_DEEP_DIVE" for x in rows),
                       "unchanged": sum(x["state"] == "UNCHANGED" for x in rows),
                       "duplicate_observations": duplicate_count,
                       "selected": len(selected),
                       "holds": sum(x["state"].startswith("HOLD_") for x in rows)},
            "guards": {"read_only": True, "watchlist_is_not_deep_baseline": True,
                       "changed_metadata_without_original_hash_is_not_verified_delta": True,
                       "index_owner_review_required": True,
                       "source_identity_is_item_not_author_or_hashtag": True},
            "canonical_promotion": False}
