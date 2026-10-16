"""TAKY V2 data-only release preflight. Pure local checks; NEVER uploads/publishes.

The gate is intentionally fail-closed. A successful local check is NOT a remote
publish authorization: runtime/publisher security gates must separately attest.
V1 is handled by existing asset_distribution_manifest_validator.py, unchanged.
"""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from drive_route_resolver import resolve

SCHEMA = "TAKY_ASSET_DISTRIBUTION_MANIFEST_V2"
SOURCE = "HNS_DRIVE_APPROVED_ASSET_MASTER"
DISTRIBUTION = "SIEZEALL_DRIVE_APPROVED_PACKAGE"
KINDS = {"LEARNING_CONTENT", "EXPANSION", "VISUAL_ASSET", "VOICE_ASSET", "CONFIG_SAFE"}
SCOPE = {"PUBLIC_RELEASE_SAFE", "FAMILY_PRIVATE_AUTHENTICATED"}
MIME = {"image/png", "image/jpeg", "image/webp", "audio/mpeg", "audio/wav", "audio/ogg", "application/json"}
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
KEYID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$")
BAD_SCHEMES = ("javascript:", "data:", "file:", "http:", "https:")
V1_FIELDS = {"slot_id", "asset_id", "master_ref", "master_revision", "source_sha256",
             "distribution_ref", "distribution_sha256", "mime_type", "release_scope",
             "consumer_apps", "status"}
CONTENT_FIELDS = {"entry_id", "source_sha256", "distribution_sha256", "source_ref",
                  "distribution_ref", "mime_type", "bytes", "release_scope"}
MAX_ITEMS = 2000
MAX_ITEM_BYTES = 50_000_000

def canonical(doc: dict) -> bytes:
    """Signature covers all fields other than signature; deterministic UTF-8."""
    copy = {k: v for k, v in doc.items() if k != "signature"}
    return json.dumps(copy, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID.fullmatch(value))

def _entry_errors(entry: Any, i: int, *, binary: bool, app_ids: set[str]) -> list[str]:
    prefix = ("ASSET" if binary else "CONTENT") + f"_{i}_"
    if not isinstance(entry, dict):
        return [prefix + "NOT_OBJECT"]
    required = V1_FIELDS if binary else CONTENT_FIELDS
    errors = [prefix+"MISSING_"+key.upper() for key in sorted(required - entry.keys())]
    for name in ("source_sha256", "distribution_sha256"):
        if not isinstance(entry.get(name), str) or not HEX64.fullmatch(entry[name]):
            errors.append(prefix + name.upper() + "_INVALID")
    if (isinstance(entry.get("source_sha256"), str)
        and isinstance(entry.get("distribution_sha256"), str)
        and entry["source_sha256"].lower() != entry["distribution_sha256"].lower()):
        errors.append(prefix + "SOURCE_DISTRIBUTION_HASH_MISMATCH")
    if entry.get("mime_type") not in MIME:
        errors.append(prefix + "MIME_UNSAFE")
    if binary and entry.get("mime_type") == "application/json":
        errors.append(prefix + "JSON_REQUIRES_CONTENT_ENTRY")
    if not binary and entry.get("mime_type") != "application/json":
        errors.append(prefix + "CONTENT_MUST_BE_JSON")
    if entry.get("release_scope") not in SCOPE:
        errors.append(prefix + "SCOPE_INVALID")
    for key in (("master_ref", "distribution_ref") if binary else ("source_ref", "distribution_ref")):
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip() or value.strip().lower().startswith(BAD_SCHEMES):
            errors.append(prefix + key.upper() + "_UNSAFE")
    if binary:
        if not valid_id(entry.get("asset_id")) or not valid_id(entry.get("slot_id")):
            errors.append(prefix + "ID_INVALID")
        if entry.get("status") != "APPROVED_FOR_DISTRIBUTION":
            errors.append(prefix + "NOT_APPROVED")
        if not isinstance(entry.get("master_revision"), str) or not entry["master_revision"].strip():
            errors.append(prefix + "MASTER_REVISION_MISSING")
        consumers = entry.get("consumer_apps")
        if not isinstance(consumers, list) or not consumers or any(a not in app_ids for a in consumers):
            errors.append(prefix + "CONSUMER_SCOPE_MISMATCH")
    else:
        if not valid_id(entry.get("entry_id")):
            errors.append(prefix + "ID_INVALID")
    size = entry.get("bytes")
    if not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= MAX_ITEM_BYTES:
        errors.append(prefix + "SIZE_INVALID")
    return errors

def verify_ed25519(doc: dict, public_keys: dict[str, bytes]) -> bool:
    sig = doc.get("signature")
    if not isinstance(sig, dict) or sig.get("alg") != "Ed25519":
        return False
    kid = sig.get("kid")
    if not isinstance(kid, str) or not KEYID.fullmatch(kid) or kid not in public_keys:
        return False
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        encoded = sig.get("value")
        if not isinstance(encoded, str):
            return False
        raw = base64.b64decode(encoded, validate=True)
        Ed25519PublicKey.from_public_bytes(public_keys[kid]).verify(raw, canonical(doc))
        return True
    except Exception:  # Missing crypto backend and invalid keys fail closed.
        return False

def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        when = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return when.tzinfo is not None
    except ValueError:
        return False

def inspect_manifest(doc: Any, *, public_keys: dict[str, bytes] | None = None) -> list[str]:
    if not isinstance(doc, dict):
        return ["MANIFEST_NOT_OBJECT"]
    errors = []
    def require(condition: bool, code: str):
        if not condition:
            errors.append(code)
    require(doc.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
    require(valid_id(doc.get("package_id")), "PACKAGE_ID_INVALID")
    require(valid_id(doc.get("package_version")), "PACKAGE_VERSION_INVALID")
    require(doc.get("source_authority") == SOURCE, "SOURCE_AUTHORITY_MISMATCH")
    require(doc.get("distribution_authority") == DISTRIBUTION, "DISTRIBUTION_AUTHORITY_MISMATCH")
    require(doc.get("kind") in KINDS, "KIND_INVALID")
    require(_valid_timestamp(doc.get("generated_at")), "TIMESTAMP_INVALID")
    require(isinstance(doc.get("effective_manifest_version"), int)
            and not isinstance(doc.get("effective_manifest_version"), bool)
            and doc.get("effective_manifest_version", -1) >= 1, "GENERATION_INVALID")
    require(isinstance(doc.get("runtime_contract_min"), int)
            and isinstance(doc.get("runtime_contract_max"), int)
            and 1 <= doc.get("runtime_contract_min", 0) <= doc.get("runtime_contract_max", 0), "RUNTIME_CONTRACT_INVALID")
    consumers = doc.get("consumer_apps")
    require(isinstance(consumers, list) and bool(consumers)
            and all(valid_id(x) for x in consumers) and len(consumers) == len(set(consumers)), "CONSUMERS_INVALID")
    apps = set(consumers) if isinstance(consumers, list) and all(isinstance(x, str) for x in consumers) else set()
    items = doc.get("assets", [])
    contents = doc.get("content_entries", [])
    require(isinstance(items, list) and isinstance(contents, list), "ITEM_ARRAY_INVALID")
    if not isinstance(items, list) or not isinstance(contents, list):
        return errors
    require(bool(items or contents) and len(items)+len(contents) <= MAX_ITEMS, "ITEM_COUNT_INVALID")
    if doc.get("kind") in {"LEARNING_CONTENT", "EXPANSION", "CONFIG_SAFE"}:
        require(bool(contents), "CONTENT_ENTRIES_REQUIRED")
    if doc.get("kind") in {"VISUAL_ASSET", "VOICE_ASSET"}:
        require(bool(items), "ASSETS_REQUIRED")
    slots = []; identifiers = []
    for i, entry in enumerate(items):
        errors.extend(_entry_errors(entry, i, binary=True, app_ids=apps))
        if isinstance(entry, dict):
            slots.append(entry.get("slot_id"))
            identifiers.append(entry.get("asset_id"))
    for i, entry in enumerate(contents):
        errors.extend(_entry_errors(entry, i, binary=False, app_ids=apps))
        if isinstance(entry, dict):
            identifiers.append(entry.get("entry_id"))
    if len(slots) != len(set(x for x in slots if isinstance(x, str))):
        errors.append("DUPLICATE_SLOT")
    if len([x for x in identifiers if isinstance(x, str)]) != len(set(x for x in identifiers if isinstance(x, str))):
        errors.append("DUPLICATE_ITEM_ID")
    if items:
        required_slots = doc.get("required_slots")
        if not isinstance(required_slots, list) or not required_slots or not all(valid_id(x) for x in required_slots):
            errors.append("REQUIRED_SLOTS_INVALID")
        elif any(x not in slots for x in required_slots):
            errors.append("REQUIRED_SLOT_MISSING")
    require(isinstance(doc.get("approval"), dict)
            and doc["approval"].get("state") == "USER_APPROVED"
            and isinstance(doc["approval"].get("evidence_ref"), str)
            and bool(doc["approval"]["evidence_ref"].strip()), "APPROVAL_EVIDENCE_MISSING")
    require(verify_ed25519(doc, public_keys or {}), "PUBLISHER_SIGNATURE_UNTRUSTED")
    return errors

def inspect_acl(acl: Any, expected_folder_id: str) -> list[str]:
    if not isinstance(acl, dict) or acl.get("folder_id") != expected_folder_id:
        return ["ACL_EVIDENCE_MISSING_OR_WRONG_FOLDER"]
    roles = acl.get("permissions")
    if not isinstance(roles, list) or not roles:
        return ["ACL_PERMISSIONS_NOT_READ_BACK"]
    errors=[]
    ancestors = acl.get("ancestors")
    expected_ancestors = (resolve("siezeall", "20_PLATFORM")["id"],
                          resolve("siezeall", "TAKY")["id"])
    if not isinstance(ancestors, list) or len(ancestors) != 2 or tuple(
            x.get("folder_id") if isinstance(x, dict) else None for x in ancestors
        ) != expected_ancestors:
        errors.append("ACL_PARENT_INHERITANCE_UNVERIFIED")
    else:
        for ancestor in ancestors:
            perms = ancestor.get("permissions")
            if not isinstance(perms, list) or not perms:
                errors.append("ACL_PARENT_PERMISSIONS_UNVERIFIED")
                continue
            for perm in perms:
                if not isinstance(perm, dict):
                    errors.append("ACL_PARENT_PERMISSION_INVALID")
                elif perm.get("type") in {"anyone", "domain"}:
                    errors.append("INHERITED_PUBLIC_ACCESS_BLOCKED")
                elif (perm.get("role") in {"writer", "commenter", "organizer", "fileOrganizer"}
                      and not (perm.get("type") == "user" and perm.get("emailAddress") == "siezeall@gmail.com")):
                    errors.append("INHERITED_UNAUTHORIZED_WRITER_BLOCKED")
    if not isinstance(acl.get("audit_receipt"), str) or not acl["audit_receipt"].strip():
        errors.append("ACL_READBACK_RECEIPT_MISSING")
    if not _valid_timestamp(acl.get("readback_at")):
        errors.append("ACL_READBACK_TIMESTAMP_INVALID")
    else:
        when = dt.datetime.fromisoformat(acl["readback_at"].replace("Z", "+00:00"))
        age = dt.datetime.now(dt.timezone.utc) - when.astimezone(dt.timezone.utc)
        if not dt.timedelta(0) <= age <= dt.timedelta(minutes=15):
            errors.append("ACL_READBACK_STALE")
    for item in roles:
        if not isinstance(item, dict):
            errors.append("ACL_ITEM_INVALID");continue
        if item.get("type") in {"anyone", "domain"} and item.get("role") in {"owner", "writer", "commenter", "organizer", "fileOrganizer"}:
            errors.append("PUBLIC_OR_DOMAIN_WRITER_BLOCKED")
        if item.get("role") in {"writer", "commenter", "organizer", "fileOrganizer"}:
            if not (item.get("type") == "user" and item.get("emailAddress") == "siezeall@gmail.com"):
                errors.append("UNAPPROVED_WRITER_BLOCKED")
    return sorted(set(errors))

def preflight(doc: Any, *, acl: Any, public_keys: dict[str,bytes] | None,
              runtime: dict | None = None, publisher_evidence: dict | None = None) -> dict:
    errors = inspect_manifest(doc, public_keys=public_keys)
    route = resolve("siezeall", "03_UPDATES")
    errors += inspect_acl(acl, route["id"])
    entries = ((doc.get("assets", []) or []) + (doc.get("content_entries", []) or [])) if isinstance(doc, dict) else []
    if isinstance(acl, dict) and any(
            isinstance(row, dict) and row.get("release_scope") == "FAMILY_PRIVATE_AUTHENTICATED"
            for row in entries):
        if any(isinstance(permission, dict) and permission.get("type") in {"anyone", "domain"}
               for permission in acl.get("permissions", [])):
            errors.append("PRIVATE_PACKAGE_PUBLIC_READ_BLOCKED")
    # Caller must prove deployed loader contract; a manifest alone is never proof.
    if not isinstance(runtime, dict) or runtime.get("verified_loader") is not True or runtime.get("remote_auth_api") is not True:
        errors.append("RUNTIME_LOADER_OR_API_UNVERIFIED")
    if not isinstance(publisher_evidence, dict) or publisher_evidence.get("authorized") is not True:
        errors.append("PUBLISHER_AUTHORIZATION_UNVERIFIED")
    return {"status": "HOLD" if errors else "LOCAL_PREFLIGHT_READY_NOT_PUBLISHED",
            "errors": sorted(set(errors)),
            "route": {"account": route["account"], "role": route["role"], "folder_id": route["id"], "path": route["path"]},
            "remote_written": False, "github_push": False, "netlify_deploy": False,
            "scope": "LOCAL_PREFLIGHT_ONLY_NOT_PRODUCTION_APPROVAL"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--acl", required=True)
    args=p.parse_args()
    try:
        doc=json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        acl=json.loads(Path(args.acl).read_text(encoding="utf-8-sig"))
        result=preflight(doc, acl=acl, public_keys=None)
    except (ValueError,OSError) as ex:
        result={"status":"HOLD","errors":[type(ex).__name__]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"]=="LOCAL_PREFLIGHT_READY_NOT_PUBLISHED" else 2

if __name__=="__main__":
    raise SystemExit(main())
