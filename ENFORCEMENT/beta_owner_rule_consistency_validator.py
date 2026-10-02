#!/usr/bin/env python3
"""Fail closed when an ACTIVE_OWNER declares a Rule ID not mirrored by RULE_REGISTRY."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "MASTER"
FILE_REGISTRY = MASTER / "MASTER_FILE_REGISTRY.json"
RULE_REGISTRY = MASTER / "RULE_REGISTRY.json"

def main() -> int:
    files = json.loads(FILE_REGISTRY.read_text(encoding="utf-8"))
    rules = json.loads(RULE_REGISTRY.read_text(encoding="utf-8"))

    rule_owner = {}
    failures = []
    for row in rules.get("rules", []):
        rid = str(row.get("rule_id", "")).strip()
        owner = str(row.get("owner", "")).strip()
        if not rid or not owner:
            failures.append(f"INVALID_RULE_ROW:{row}")
            continue
        if rid in rule_owner:
            failures.append(f"DUPLICATE_RULE_ID:{rid}")
        rule_owner[rid] = owner

    declared = {}
    active_owners = [
        path
        for path, meta in files.get("files", {}).items()
        if meta.get("class") == "ACTIVE_OWNER"
    ]

    for owner_path in active_owners:
        path = ROOT / owner_path
        if not path.is_file():
            failures.append(f"ACTIVE_OWNER_FILE_MISSING:{owner_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for rid in re.findall(r"(?mi)^\s*Rule ID:\s*`?([A-Z0-9_-]+)`?\s*$", text):
            previous = declared.get(rid)
            if previous and previous != owner_path:
                failures.append(f"RULE_ID_DECLARED_BY_MULTIPLE_OWNERS:{rid}:{previous}:{owner_path}")
            declared[rid] = owner_path
            actual = rule_owner.get(rid)
            if actual is None:
                failures.append(f"DECLARED_RULE_MISSING_FROM_REGISTRY:{rid}:{owner_path}")
            elif actual != owner_path:
                failures.append(f"DECLARED_RULE_OWNER_MISMATCH:{rid}:{actual}:{owner_path}")

    for rid, owner in rule_owner.items():
        if owner.startswith("MASTER/"):
            meta = files.get("files", {}).get(owner, {})
            cls = meta.get("class")
            allowed_legacy = cls == "LEGACY_OPTIONAL" and meta.get("default_activation") is False
            if cls != "ACTIVE_OWNER" and not allowed_legacy:
                failures.append(f"RULE_POINTS_TO_INVALID_MASTER_OWNER:{rid}:{owner}:{cls}")

    result = {
        "pass": not failures,
        "active_owner_count": len(active_owners),
        "registered_rule_count": len(rule_owner),
        "declared_rule_count": len(declared),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
