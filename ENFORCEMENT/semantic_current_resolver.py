#!/usr/bin/env python3
"""Resolve semantic owners/resume pointers by explicit registry binding only.

No globbing, filename ranking, fallback, or authority promotion. Evidence roles
are readable explicitly but can never satisfy an operational CURRENT request.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "MASTER/MASTER_FILE_REGISTRY.json"
CURRENT = "CURRENT/SYSTEM_WIDE_REVIEW.json"
ROLES = {"owner", "current", "change_ledger", "verification_checkpoint"}
STATES = {"MAIN/CLOSED", "DRAFT_CANDIDATE", "OPEN", "HOLD", "UNVERIFIED"}


class ResolutionError(ValueError):
    """An explicit, unambiguous authority binding could not be verified."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResolutionError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def exact_file(root: Path, raw: str) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw or ":" in raw:
        raise ResolutionError(f"INVALID_EXACT_PATH:{raw}")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or str(path) != raw:
        raise ResolutionError(f"INVALID_EXACT_PATH:{raw}")
    resolved = (root / raw).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ResolutionError(f"MISSING_OR_OUTSIDE_REPOSITORY:{raw}")
    # Windows is case-insensitive; authority paths still require exact spelling.
    cursor = root
    for part in path.parts:
        if part not in {entry.name for entry in cursor.iterdir()}:
            raise ResolutionError(f"NONEXACT_PATH:{raw}")
        cursor = cursor / part
    return resolved


def bindings(root: Path, registry: dict | None = None) -> dict:
    registry = load_json(root / REGISTRY) if registry is None else registry
    rows = registry.get("semantic_owners")
    if not isinstance(rows, list) or not rows:
        raise ResolutionError("SEMANTIC_OWNER_BINDINGS_MISSING")
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ResolutionError("INVALID_OWNER_BINDING")
        namespace = row.get("namespace")
        if not isinstance(namespace, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", namespace):
            raise ResolutionError("INVALID_NAMESPACE")
        if namespace in found:
            raise ResolutionError(f"DUPLICATE_ACTIVE_OWNER:{namespace}")
        if row.get("state") != "ACTIVE_OWNER":
            raise ResolutionError(f"NONACTIVE_OWNER:{namespace}")
        paths = row.get("paths")
        if not isinstance(paths, dict) or not paths.get("owner") or set(paths) - ROLES:
            raise ResolutionError(f"INVALID_ROLE_BINDINGS:{namespace}")
        if any(not isinstance(path, str) for path in paths.values()):
            raise ResolutionError(f"INVALID_ROLE_PATH:{namespace}")
        if len(set(paths.values())) != len(paths):
            raise ResolutionError(f"AMBIGUOUS_ARTIFACT_ROLES:{namespace}")
        for role, path in paths.items():
            exact_file(root, path)
            if path.startswith("MASTER/") and role == "owner":
                if registry.get("files", {}).get(path, {}).get("class") != "ACTIVE_OWNER":
                    raise ResolutionError(f"NONCANONICAL_MASTER_OWNER:{path}")
        found[namespace] = row
    return found


def resolve(namespace: str, *, role: str = "owner", expected_path: str | None = None,
            root: Path = ROOT, registry: dict | None = None) -> dict:
    owners = bindings(root, registry)
    if namespace not in owners:
        raise ResolutionError(f"UNKNOWN_SEMANTIC_OWNER:{namespace}")
    path = owners[namespace]["paths"].get(role)
    if role not in ROLES or path is None:
        raise ResolutionError(f"UNREGISTERED_ROLE:{namespace}:{role}")
    if expected_path is not None and expected_path != path:
        raise ResolutionError(f"STALE_OR_UNREGISTERED_DIRECT_PATH:{expected_path}")
    return {"namespace": namespace, "role": role, "path": path,
            "owner": owners[namespace]["paths"]["owner"],
            "resume_pointer": role == "current"}


def validate_system_current(root: Path = ROOT) -> dict:
    owners = bindings(root)
    pointer = resolve("system", role="current", expected_path=CURRENT, root=root)
    current = load_json(root / pointer["path"])
    if current.get("role") != "SEMANTIC_RESUME_POINTER" or current.get("authority_transfer") is not False:
        raise ResolutionError("CURRENT_IS_NOT_AN_OWNER")
    heads = current.get("source_heads", {})
    if not heads:
        raise ResolutionError("SOURCE_HEADS_MISSING")
    for repo, head in heads.items():
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            raise ResolutionError(f"INVALID_EXACT_MAIN_REF:{repo}")
    if current.get("base_ref") != heads.get("TAKY"):
        raise ResolutionError("BASE_REF_MISMATCH")
    seen = set()
    for item in current.get("scopes", []):
        scope = item.get("id")
        if not scope or scope in seen:
            raise ResolutionError(f"AMBIGUOUS_SCOPE:{scope}")
        seen.add(scope)
        if item.get("state") not in STATES:
            raise ResolutionError(f"UNKNOWN_SCOPE_STATE:{scope}")
        for alias in item.get("owner_aliases", []):
            if alias not in owners:
                raise ResolutionError(f"UNKNOWN_SEMANTIC_OWNER:{alias}")
        if item["state"] == "MAIN/CLOSED":
            if not item.get("owner_aliases") or item.get("source_repo") not in heads:
                raise ResolutionError(f"CLOSED_WITHOUT_MAIN_OWNER:{scope}")
        if item["state"] == "DRAFT_CANDIDATE":
            if not item.get("pr") or item.get("main_authority") is not False:
                raise ResolutionError(f"DRAFT_PROMOTED_TO_MAIN:{scope}")
            head_ref = item.get("head_ref")
            if head_ref is not None and not re.fullmatch(r"[0-9a-f]{40}", head_ref):
                raise ResolutionError(f"INVALID_DRAFT_HEAD_REF:{scope}")
        for path in item.get("evidence_paths", []):
            exact_file(root, path)
    if not seen:
        raise ResolutionError("SCOPES_MISSING")
    return {"pass": True, "pointer": pointer, "owners": len(owners), "scopes": len(seen),
            "claim_ceiling": "AUDITED_SNAPSHOT_NOT_LIVE_OR_DEPLOYMENT_PROOF"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace", nargs="?")
    parser.add_argument("--role", choices=sorted(ROLES), default="owner")
    parser.add_argument("--expected-path")
    args = parser.parse_args()
    try:
        result = (resolve(args.namespace, role=args.role, expected_path=args.expected_path)
                  if args.namespace else validate_system_current())
    except (ResolutionError, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"pass": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
