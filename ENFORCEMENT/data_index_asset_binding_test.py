#!/usr/bin/env python3
"""Self-contained synthetic contract tests. Approval records cannot approve runtime."""
import copy
import hashlib
import struct
import tempfile
import zlib
from pathlib import Path

from data_index_asset_binding import audit_visual_bindings


def chunk(tag, body):
    return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xffffffff)


def png(width=1, height=1):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(b"\x00" + b"\x00\x00\x00\x00" * width)) +
            chunk(b"IEND", b""))


with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "assets").mkdir()
    raw = png()
    (root / "assets/scene.png").write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    visual_id = "TEST-VISUAL-ID-001"
    registry = {
        "$schema": "TAKY.visual-reference-binding.v1",
        "reference_asset": {"asset_id": "REFERENCE-001", "sha256": "a" * 64},
        "visual_ids": {visual_id: {
            "app": "Hide & Seek", "source_asset_id": "REFERENCE-001",
            "production_asset": {
                "asset_file": "assets/scene.png", "sha256": digest, "width": 1,
                "height": 1, "mime_type": "image/png", "approval": "USER_RECORDED",
            },
        }},
    }
    binding = {
        "app": "Hide & Seek", "home_reference_visual_id": visual_id,
        "reference_asset_sha256": "a" * 64,
        "scope": "APPROVED_PRODUCTION_ENVIRONMENT_ASSET",
        "runtime_artwork_binding": {
            "visual_id": visual_id, "asset_path": "../assets/scene.png",
            "asset_sha256": digest, "size_px": [1, 1],
        },
    }
    before = copy.deepcopy((registry, binding))
    metadata = audit_visual_bindings(registry, [binding])
    assert metadata["cards"][0]["local_binary_evidence_state"] == "METADATA_POINTER_ONLY"
    assert metadata["cards"][0]["app_runtime_binding_verified"] is False
    assert metadata["producer_quality_verified"] is False
    measured = audit_visual_bindings(registry, [binding], local_asset_root=root)
    card = measured["cards"][0]
    assert card["local_binary_evidence_state"] == "LOCAL_BINARY_HASH_AND_DIMENSIONS_VERIFIED"
    assert card["local_binary_bytes"] == len(raw)
    assert card["approval_recorded_in_registry_not_independently_attested"] is True
    assert card["app_runtime_binding_verified"] is False
    assert card["central_git_binary_committed_verified"] is False
    assert card["render_and_interaction_verified"] is False
    assert measured["current_promoted"] is False and measured["domain_use_approved"] is False
    assert (registry, binding) == before

    def reject(r, b, asset_root=None):
        try:
            audit_visual_bindings(r, [b], local_asset_root=asset_root)
        except ValueError:
            return
        raise AssertionError("Invalid or unsupported binding was accepted")

    mismatch = copy.deepcopy(binding)
    mismatch["runtime_artwork_binding"]["asset_sha256"] = "0" * 64
    reject(registry, mismatch)
    mismatch = copy.deepcopy(binding)
    mismatch["runtime_artwork_binding"]["asset_path"] = "../../private.png"
    reject(registry, mismatch)
    mismatch = copy.deepcopy(binding)
    mismatch["home_reference_visual_id"] = "invented"
    reject(registry, mismatch)
    mismatch = copy.deepcopy(binding)
    mismatch["app"] = "Snap & Pop"
    reject(registry, mismatch)
    mismatch = copy.deepcopy(binding)
    mismatch["runtime_artwork_binding"]["size_px"] = [2, 2]
    reject(registry, mismatch)
    mismatch = copy.deepcopy(registry)
    mismatch["visual_ids"][visual_id]["production_asset"]["asset_file"] = "../outside.png"
    reject(mismatch, binding)
    mismatch = copy.deepcopy(registry)
    mismatch["visual_ids"][visual_id]["production_asset"]["sha256"] = "0" * 64
    reject(mismatch, binding)
    try:
        audit_visual_bindings(registry, [binding, binding])
    except ValueError as exc:
        assert str(exc) == "VISUAL_ID_REPEATED"
    else:
        raise AssertionError("Duplicate app/visual binding permitted")
    (root / "assets/scene.png").write_bytes(raw + b"tamper")
    reject(registry, binding, root)
    (root / "assets/scene.png").unlink()
    absent = audit_visual_bindings(registry, [binding], local_asset_root=root)
    assert absent["cards"][0]["local_binary_evidence_state"] == "LOCAL_BINARY_UNAVAILABLE"
    assert not absent["producer_quality_verified"]
print("data_index_asset_binding: PASS (byte integrity, path traversal, approval scope, pointer identity and no false UI completion)")
