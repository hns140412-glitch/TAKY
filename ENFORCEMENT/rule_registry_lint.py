#!/usr/bin/env python3
"""Validate TAKY's machine-readable single-owner rule registry."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "MASTER" / "RULE_REGISTRY.json"

def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    errors = []
    ids = set()
    for rule in rules:
        rid = rule.get("rule_id")
        owner = rule.get("owner")
        if not rid or not owner:
            errors.append(f"missing rule_id/owner: {rule}")
            continue
        if rid in ids:
            errors.append(f"duplicate rule_id: {rid}")
        ids.add(rid)
        if not (ROOT / owner).is_file():
            errors.append(f"owner does not exist: {rid} -> {owner}")
    out = {"registry_version": data.get("registry_version"), "rule_count": len(rules), "errors": errors, "pass": not errors}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
