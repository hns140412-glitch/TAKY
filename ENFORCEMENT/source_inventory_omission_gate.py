#!/usr/bin/env python3
"""Fail closed when a handoff omits items from an independently frozen source inventory.

This is a scoped reconciliation gate, NOT an extractor or a claim that all historical
conversations have been discovered. Inventory must be built from source evidence
before the handoff is drafted and frozen outside the candidate handoff.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(inventory_path, handoff_path):
    errors = []
    inv = json.loads(inventory_path.read_text(encoding="utf-8"))
    out = json.loads(handoff_path.read_text(encoding="utf-8"))
    if inventory_path.resolve() == handoff_path.resolve():
        errors.append("inventory and handoff cannot be the same file")
    if not inv.get("source_scope") or not inv.get("source_revision"):
        errors.append("independent inventory requires source_scope and source_revision")
    if inv.get("coverage_status") != "SOURCE_RECOVERED":
        errors.append("source coverage not established; cannot claim omission-free PASS")
    sources = inv.get("source_items")
    targets = out.get("coverage_items")
    if not isinstance(sources, list) or not sources:
        errors.append("source_items must be a nonempty list")
        sources = []
    if not isinstance(targets, list):
        errors.append("coverage_items must be a list")
        targets = []
    def index(items, label):
        result = {}
        for n, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{label}[{n}] not an object")
                continue
            key = item.get("source_id")
            if not isinstance(key, str) or not key.strip():
                errors.append(f"{label}[{n}] missing source_id")
            elif key in result:
                errors.append(f"{label} duplicate source_id: {key}")
            else:
                result[key] = item
        return result
    source = index(sources, "inventory")
    target = index(targets, "handoff")
    for key, item in source.items():
        if not item.get("source_pointer") or not item.get("content_sha256"):
            errors.append(f"{key}: inventory lacks source pointer/content digest")
        if not item.get("classification"):
            errors.append(f"{key}: inventory lacks classification")
        if key not in target:
            errors.append(f"OMITTED_SOURCE_ITEM: {key}")
            continue
        mapped = target[key]
        if mapped.get("content_sha256") != item.get("content_sha256"):
            errors.append(f"SOURCE_CONTENT_DRIFT: {key}")
        if mapped.get("classification") != item.get("classification"):
            errors.append(f"CLASSIFICATION_DRIFT: {key}")
        if not mapped.get("handoff_location") and not mapped.get("recoverable_pointer"):
            errors.append(f"UNRECOVERABLE_ITEM: {key}")
        if item.get("type") == "CORRECTION" and not mapped.get("correction_linkage"):
            errors.append(f"CORRECTION_LINKAGE_MISSING: {key}")
    for key in target.keys() - source.keys():
        errors.append(f"UNTRACED_HANDOFF_ITEM: {key}")
    if out.get("inventory_sha256") != digest(inventory_path):
        errors.append("inventory_sha256 mismatch: candidate must bind to frozen source inventory")
    if out.get("source_revision") != inv.get("source_revision"):
        errors.append("source_revision mismatch")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("inventory", type=Path)
    p.add_argument("handoff_coverage", type=Path)
    a = p.parse_args()
    errors = check(a.inventory, a.handoff_coverage)
    print(json.dumps({"pass": not errors, "errors": errors,
        "claim_boundary": "INVENTORY_RECONCILIATION_PASS != SOURCE_UNIVERSE_COMPLETE != HOSTED_AUTO_ENFORCEMENT"},
        ensure_ascii=False, indent=2))
    return int(bool(errors))

if __name__ == "__main__":
    sys.exit(main())
