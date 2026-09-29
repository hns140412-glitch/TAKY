#!/usr/bin/env python3
"""Read-only INDEX-to-visual-asset binding evidence view.

Consumes an existing approved reference registry and app binding pointers.
Checks actual local bytes if a separately supplied root exists. It does not
upload originals, authenticate a user's approval, bind app runtime or judge
visual fidelity. Those remain with source/producer/consumer owners.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any

SCHEMA = "TAKY_INDEX_ASSET_BINDING_EVIDENCE_V1"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _required(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key + "_MISSING")
    return value


def _safe(root: Path, relative: str, *, from_binding: bool) -> Path:
    rel = Path(_required(relative, "ASSET_RELATIVE_PATH"))
    if rel.is_absolute() or "\\" in relative or ":" in relative:
        raise ValueError("ASSET_PATH_NOT_PORTABLE_RELATIVE")
    target = (root / ("app_bindings" if from_binding else "") / rel).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("ASSET_PATH_ESCAPES_ROOT")
    return target


def _actual_png(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"present": False}
    raw = path.read_bytes()
    if (len(raw) < 33 or raw[:8] != PNG_SIGNATURE or raw[12:16] != b"IHDR"
            or int.from_bytes(raw[8:12], "big") != 13):
        raise ValueError("ASSET_PNG_HEADER_INVALID")
    width, height = struct.unpack(">II", raw[16:24])
    if not width or not height:
        raise ValueError("ASSET_PNG_DIMENSIONS_INVALID")
    return {"present": True, "sha256": hashlib.sha256(raw).hexdigest(),
            "dimensions": [width, height], "bytes": len(raw)}


def audit_visual_bindings(
    registry: dict[str, Any], bindings: list[dict[str, Any]], *,
    local_asset_root: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(registry, dict) or registry.get("$schema") != "TAKY.visual-reference-binding.v1":
        raise ValueError("REGISTRY_SCHEMA_INVALID")
    visuals = registry.get("visual_ids")
    reference = registry.get("reference_asset")
    if not isinstance(visuals, dict) or not isinstance(reference, dict):
        raise ValueError("REGISTRY_REFERENCE_MISSING")
    ref_id = _required(reference.get("asset_id"), "REFERENCE_ID")
    ref_sha = _required(reference.get("sha256"), "REFERENCE_HASH")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("BINDINGS_NOT_LIST")
    if local_asset_root is not None and not isinstance(local_asset_root, Path):
        raise ValueError("ASSET_ROOT_INVALID")
    cards = []
    seen_visual_ids = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("BINDING_NOT_OBJECT")
        vid = _required(binding.get("home_reference_visual_id"), "VISUAL_ID")
        if vid in seen_visual_ids:
            raise ValueError("VISUAL_ID_REPEATED")
        seen_visual_ids.add(vid)
        visual = visuals.get(vid)
        if not isinstance(visual, dict):
            raise ValueError("VISUAL_ID_NOT_IN_APPROVED_REGISTRY")
        approved = visual.get("production_asset")
        runtime = binding.get("runtime_artwork_binding")
        if not isinstance(approved, dict) or not isinstance(runtime, dict):
            raise ValueError("PRODUCTION_ASSET_POINTER_ABSENT")
        expected = _required(approved.get("sha256"), "ASSET_HASH")
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError("ASSET_HASH_FORMAT_INVALID")
        size = [approved.get("width"), approved.get("height")]
        if any(type(x) is not int or x <= 0 for x in size):
            raise ValueError("ASSET_DIMENSIONS_INVALID")
        if approved.get("mime_type") != "image/png":
            raise ValueError("ASSET_MEDIA_TYPE_UNSUPPORTED")
        if (binding.get("app") != visual.get("app")
                or visual.get("source_asset_id") != ref_id
                or binding.get("reference_asset_sha256") != ref_sha
                or runtime.get("visual_id") != vid
                or runtime.get("asset_sha256") != expected
                or runtime.get("size_px") != size
                or binding.get("scope") != "APPROVED_PRODUCTION_ENVIRONMENT_ASSET"):
            raise ValueError("REGISTRY_BINDING_CONFLICT")
        source_rel = _required(approved.get("asset_file"), "SOURCE_FILE")
        bound_rel = _required(runtime.get("asset_path"), "BINDING_FILE")
        # Path resolution is necessary even in metadata-only mode to reject traversal.
        pseudo = Path("/virtual-index-root")
        expected_path = _safe(pseudo, source_rel, from_binding=False)
        bound_path = _safe(pseudo, bound_rel, from_binding=True)
        if expected_path != bound_path:
            raise ValueError("SOURCE_BINDING_FILE_MISMATCH")
        evidence_state = "METADATA_POINTER_ONLY"
        measured = None
        if local_asset_root is not None:
            measured = _actual_png(_safe(local_asset_root, source_rel, from_binding=False))
            if measured["present"]:
                if measured["sha256"] != expected or measured["dimensions"] != size:
                    raise ValueError("ASSET_SOURCE_BYTES_CONFLICT")
                evidence_state = "LOCAL_BINARY_HASH_AND_DIMENSIONS_VERIFIED"
            else:
                evidence_state = "LOCAL_BINARY_UNAVAILABLE"
        cards.append({
            "visual_id": vid, "consumer_app": binding["app"],
            "source_reference_id": ref_id, "source_asset_relative_path": source_rel,
            "asset_sha256": expected, "expected_size_px": size,
            "source_binding_metadata_consistent": True,
            "local_binary_evidence_state": evidence_state,
            "local_binary_bytes": measured.get("bytes") if measured and measured["present"] else None,
            "approval_recorded_in_registry_not_independently_attested": bool(approved.get("approval")),
            "app_runtime_binding_verified": False, "central_git_binary_committed_verified": False,
            "render_and_interaction_verified": False,
            "open_witnesses": [
                "EXACT_CENTRAL_TAKY_ASSETS_BINARY_COMMIT_AND_RIGHTS",
                "EXACT_APP_RUNTIME_IMPORT_AND_BUILD",
                "ACTUAL_RENDER_INTERACTION_AND_VISUAL_ID_MATCH",
            ],
        })
    return {
        "schema": SCHEMA, "state": "SOURCE_BINDING_EVIDENCE_ONLY",
        "projection_authoritative": False, "current_promoted": False,
        "domain_use_approved": False, "producer_quality_verified": False,
        "reference_binary_independently_checked": False,
        "asset_binding_count": len(cards), "cards": cards,
        "claim_ceiling": "LOCAL_BINARY_IDENTITY_AND_METADATA_BINDING_IF_PROVIDED",
    }


def audit_consumer_static_footprint(
    approved_asset_basename: str,
    *, app_tree_paths: list[str],
    inspected_code: dict[str, str],
) -> dict[str, Any]:
    """A bounded source-file check, never an app build or runtime attestation.

    The caller must obtain tree/content snapshots from its authorized source.
    Static presence is only a *candidate* binding; absence means absent in
    inspected files and tree, not that dynamic runtime use is impossible.
    """
    name = _required(approved_asset_basename, "APPROVED_ASSET_NAME")
    if name in {".", ".."} or "/" in name or "\\" in name or not name.lower().endswith(".png"):
        raise ValueError("APPROVED_ASSET_BASENAME_INVALID")
    if not isinstance(app_tree_paths, list) or not all(
        isinstance(path, str) and path and not path.startswith("/")
        for path in app_tree_paths
    ):
        raise ValueError("APP_TREE_SNAPSHOT_INVALID")
    if not isinstance(inspected_code, dict) or not inspected_code or not all(
        isinstance(path, str) and path and isinstance(body, str)
        for path, body in inspected_code.items()
    ):
        raise ValueError("INSPECTED_CODE_INVALID")
    import re
    # The result is a conservative signal, not proof that an arbitrary string
    # is the actual DOM/CSS image source. Compare actual render separately.
    hits = [path for path, body in inspected_code.items() if name in body]
    asset_tree_hits = [path for path in app_tree_paths if path.rsplit("/", 1)[-1] == name]
    local_image_refs: dict[str, list[str]] = {}
    for path, body in inspected_code.items():
        refs = re.findall(r"""(?:src\s*=\s*["']|url\(\s*["']?)([^"')]+?\.(?:png|jpg|jpeg|webp))""", body, flags=re.I)
        if refs:
            local_image_refs[path] = sorted(set(refs))[:30]
    return {
        "schema": "TAKY_INDEX_STATIC_CONSUMER_FOOTPRINT_V1",
        "asset_basename": name,
        "source_tree_expected_name_found": bool(asset_tree_hits),
        "source_code_expected_name_found": bool(hits),
        "tree_matching_paths": asset_tree_hits,
        "code_matching_files": hits,
        "observed_static_image_refs": local_image_refs,
        "static_snapshot_indicates_unbound": not bool(asset_tree_hits or hits),
        "runtime_import_verified": False,
        "asset_binary_hash_verified_from_tree": False,
        "render_visual_match_verified": False,
        "claim_ceiling": "BOUNDED_STATIC_SOURCE_SNAPSHOT_ONLY",
    }
