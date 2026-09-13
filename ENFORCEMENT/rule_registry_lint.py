#!/usr/bin/env python3
"""Validate TAKY's machine-readable single-owner rule registry."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "MASTER" / "RULE_REGISTRY.json"

REQUIRED_OWNER_BINDINGS = {
    "TKY-ENFORCEMENT-001": "MASTER/ENFORCEMENT_PROTOCOL.md",
}


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    errors = []
    ids = set()
    owner_by_id = {}

    for rule in rules:
        rid = rule.get("rule_id")
        owner = rule.get("owner")
        if not rid or not owner:
            errors.append(f"missing rule_id/owner: {rule}")
            continue
        if rid in ids:
            errors.append(f"duplicate rule_id: {rid}")
        ids.add(rid)
        owner_by_id[rid] = owner
        if not (ROOT / owner).is_file():
            errors.append(f"owner does not exist: {rid} -> {owner}")

    for rid, expected_owner in REQUIRED_OWNER_BINDINGS.items():
        actual_owner = owner_by_id.get(rid)
        if actual_owner is None:
            errors.append(f"required rule missing: {rid}")
        elif actual_owner != expected_owner:
            errors.append(
                f"required owner mismatch: {rid} -> {actual_owner}; expected {expected_owner}"
            )

    enforcement_owner = ROOT / REQUIRED_OWNER_BINDINGS["TKY-ENFORCEMENT-001"]
    if enforcement_owner.is_file():
        text = enforcement_owner.read_text(encoding="utf-8")
        if "MASTER/RULE_REGISTRY.json" not in text:
            errors.append(
                "enforcement owner missing back-reference to MASTER/RULE_REGISTRY.json"
            )
        if "RULE WRITTEN ≠ RULE ENFORCED" not in text:
            errors.append(
                "enforcement owner missing canonical RULE WRITTEN ≠ RULE ENFORCED invariant"
            )

    out = {
        "registry_version": data.get("registry_version"),
        "rule_count": len(rules),
        "required_owner_bindings": REQUIRED_OWNER_BINDINGS,
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
