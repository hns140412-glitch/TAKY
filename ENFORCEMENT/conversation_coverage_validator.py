#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ALLOWED_TYPES = {
    "REQUIREMENT","DECISION","CORRECTION","IDEA","FRONTIER","STRATEGY",
    "CONFLICT","OPEN","EVIDENCE","ASSUMPTION","REJECTION","CONSTRAINT",
    "OUTCOME","LESSON"
}
ALLOWED_DISPOSITIONS = {
    "PRESERVE","ADOPT","ADJUST","HOLD","REJECT","EXCLUDE",
    "OWNERSHIP_TRANSFER","CONFLICT","SUPERSEDED","OPEN","FRONTIER"
}

def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)

def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    atoms = data.get("atoms")
    if not isinstance(atoms, list):
        fail("atoms must be a list")

    ids = set()
    material = 0
    mapped = 0
    for i, atom in enumerate(atoms):
        aid = atom.get("atom_id")
        if not aid:
            fail(f"atom[{i}] missing atom_id")
        if aid in ids:
            fail(f"duplicate atom_id: {aid}")
        ids.add(aid)

        if atom.get("type") not in ALLOWED_TYPES:
            fail(f"{aid}: invalid type")
        if not atom.get("source_pointer"):
            fail(f"{aid}: missing source_pointer")
        if not atom.get("content"):
            fail(f"{aid}: missing content")
        if atom.get("disposition") not in ALLOWED_DISPOSITIONS:
            fail(f"{aid}: invalid/missing disposition")
        if not atom.get("destination"):
            fail(f"{aid}: missing destination")

        if atom.get("material") is True:
            material += 1
            mapped += 1 if atom.get("destination") else 0

        if atom.get("type") == "CORRECTION":
            if not atom.get("supersedes") and not atom.get("affects"):
                fail(f"{aid}: correction missing supersedes/affects linkage")

    summary = data.get("coverage_summary") or {}
    expected = {
        "material_atoms": material,
        "mapped_material": mapped,
        "unmapped_material": material - mapped,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            fail(f"coverage_summary.{k}={summary.get(k)!r}, expected {v}")

    if summary.get("unmapped_material") != 0:
        fail("UNMAPPED_MATERIAL must be 0 for compile completion")
    if summary.get("silent_loss_count") != 0:
        fail("SILENT_LOSS must be 0")
    if summary.get("false_convergence_count") != 0:
        fail("FALSE_CONVERGENCE must be 0")

    rr = data.get("reverse_reconstruction") or {}
    for key in (
        "intent_reconstructable",
        "latest_corrections_reconstructable",
        "open_items_reconstructable",
        "why_preserved",
    ):
        if rr.get(key) is not True:
            fail(f"reverse reconstruction failed: {key}")

    scope = data.get("source_scope") or {}
    if not scope.get("description") or not scope.get("coverage_status"):
        fail("source_scope missing description/coverage_status")

    print(
        f"PASS: {data.get('ledger_id','<no-ledger-id>')} "
        f"material={material} mapped={mapped} "
        f"source_coverage={scope.get('coverage_status')}"
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: conversation_coverage_validator.py <coverage-ledger.json>")
        raise SystemExit(2)
    main(sys.argv[1])
