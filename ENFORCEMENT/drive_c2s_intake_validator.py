#!/usr/bin/env python3
"""Validate direct Google Drive -> TAKY C2S intake records."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ALLOWED_IMPACT={"NONE","CANDIDATE","REQUIRED"}
ALLOWED_STATUS={
    "DRIVE_SAVED","DRIVE_POINTER_VERIFIED","DIRECT_C2S_INTAKE_READY",
    "C2S_ATOMIZED","OWNER_REFLECTED","CANONICAL_WRITTEN_VERIFIED",
    "OPEN","HOLD","CONFLICT"
}

def validate(rec: dict) -> list[str]:
    f=[]
    for k in ("intake_id","source_title","drive_file_id","project_or_domain","source_class","canonical_impact","c2s_status"):
        if not str(rec.get(k,"")).strip():
            f.append(f"MISSING:{k}")
    impact=str(rec.get("canonical_impact","")).upper()
    status=str(rec.get("c2s_status","")).upper()
    if impact and impact not in ALLOWED_IMPACT:
        f.append("INVALID:canonical_impact")
    if status and status not in ALLOWED_STATUS:
        f.append("INVALID:c2s_status")
    if rec.get("notebooklm_required") is True:
        f.append("NOTEBOOKLM_DEPENDENCY_FORBIDDEN")
    if status in {"C2S_ATOMIZED","OWNER_REFLECTED","CANONICAL_WRITTEN_VERIFIED"}:
        atoms=rec.get("material_atoms")
        if not isinstance(atoms,list) or not atoms:
            f.append("MATERIAL_ATOMS_MISSING")
    if impact=="REQUIRED" and status=="CANONICAL_WRITTEN_VERIFIED":
        if rec.get("unmapped_material",1)!=0:
            f.append("UNMAPPED_MATERIAL_NONZERO")
        if rec.get("silent_loss",1)!=0:
            f.append("SILENT_LOSS_NONZERO")
        if not str(rec.get("canonical_write_ref","")).strip():
            f.append("CANONICAL_WRITE_REF_MISSING")
    return f

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("record",type=Path)
    a=ap.parse_args()
    rec=json.loads(a.record.read_text(encoding="utf-8"))
    f=validate(rec)
    print(json.dumps({"pass":not f,"detected":f},ensure_ascii=False,indent=2))
    return 0 if not f else 1

if __name__=="__main__":
    raise SystemExit(main())
