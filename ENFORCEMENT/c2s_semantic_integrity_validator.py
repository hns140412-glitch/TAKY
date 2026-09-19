#!/usr/bin/env python3
import json, sys
from pathlib import Path

ALLOWED_TYPES={"REQUIREMENT","DECISION","CORRECTION","IDEA","FRONTIER","STRATEGY","CONFLICT","OPEN","EVIDENCE","ASSUMPTION","REJECTION","CONSTRAINT","OUTCOME","LESSON"}
TERMINAL_DISPOSITIONS={"PRESERVE","ADOPT","ADJUST","HOLD","REJECT","EXCLUDE","OWNERSHIP_TRANSFER","CONFLICT","SUPERSEDED","OPEN","FRONTIER"}

def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)

def main(path):
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    atoms=d.get("atoms")
    if not isinstance(atoms,list) or not atoms:
        fail("atoms missing/empty")
    by_id={}
    for a in atoms:
        aid=a.get("atom_id")
        if not aid or aid in by_id: fail(f"invalid/duplicate atom_id:{aid}")
        by_id[aid]=a
        if a.get("type") not in ALLOWED_TYPES: fail(f"{aid}: invalid type")
        if a.get("disposition") not in TERMINAL_DISPOSITIONS: fail(f"{aid}: invalid disposition")
        if not a.get("source_pointer"): fail(f"{aid}: missing source_pointer")
        if not a.get("destination"): fail(f"{aid}: missing destination")
        if not a.get("content"): fail(f"{aid}: missing content")
        auth=a.get("source_authority")
        if auth=="NOTEBOOKLM_OUTPUT" and a.get("canonicalized") is True:
            fail(f"{aid}: NotebookLM output cannot be canonicalized without raw_recheck")
        if auth=="NOTEBOOKLM_OUTPUT" and a.get("raw_recheck") is not True:
            fail(f"{aid}: NotebookLM output requires raw_recheck before canonical use")

    for aid,a in by_id.items():
        if a.get("type")=="CORRECTION":
            links=(a.get("supersedes") or [])+(a.get("affects") or [])
            if not links: fail(f"{aid}: correction missing supersedes/affects")
        if a.get("type") in {"OPEN","CONFLICT"} and a.get("disposition") not in {"OPEN","CONFLICT","HOLD"}:
            if a.get("resolution_evidence") is None:
                fail(f"{aid}: OPEN/CONFLICT resolved without resolution_evidence")

        merge=a.get("merged_from") or []
        if len(merge)>1 and a.get("equivalence_evidence") is None:
            fail(f"{aid}: possible false convergence; merged_from lacks equivalence_evidence")

    scope=d.get("source_scope") or {}
    inaccessible=scope.get("inaccessible_or_unverified") or []
    coverage=scope.get("coverage_status","")
    if inaccessible and coverage in {"FULL","COMPLETE","FULL_COVERAGE"}:
        fail("coverage lies: inaccessible sources exist but coverage marked full")

    lineage=d.get("correction_lineage") or []
    for edge in lineage:
        new=edge.get("correction_atom")
        old=edge.get("superseded_atom")
        if new not in by_id or old not in by_id:
            fail(f"correction_lineage references unknown atom: {old}->{new}")
        if by_id[new].get("type")!="CORRECTION":
            fail(f"{new}: lineage correction_atom is not CORRECTION")

    rr=d.get("reverse_reconstruction") or {}
    for k in ("intent_reconstructable","latest_corrections_reconstructable","open_items_reconstructable","why_preserved"):
        if rr.get(k) is not True: fail(f"reverse reconstruction failed:{k}")

    summary=d.get("coverage_summary") or {}
    if summary.get("unmapped_material") != 0: fail("UNMAPPED_MATERIAL != 0")
    if summary.get("silent_loss_count") != 0: fail("SILENT_LOSS != 0")
    if summary.get("false_convergence_count") != 0: fail("FALSE_CONVERGENCE != 0")

    print(f"PASS: semantic integrity {d.get('ledger_id','<no-ledger-id>')} atoms={len(atoms)}")

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: c2s_semantic_integrity_validator.py <ledger.json>")
        raise SystemExit(2)
    main(sys.argv[1])
