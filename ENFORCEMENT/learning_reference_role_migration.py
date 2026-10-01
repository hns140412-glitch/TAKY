#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/"MIGRATION/LEARNING_REFERENCE/DRIVE_LEARNING_REFERENCE_ROLE_MIGRATION_2026-10-02_V1.json"
ALLOWED_ROLES={"CURRICULUM_ALIGNMENT","LEXICAL_SEMANTICS","LANGUAGE_USAGE","PEDAGOGICAL_USAGE","GENERAL_REFERENCE"}
EXPECTED_IDS={"LRM-NIKL-CTX-V3","LRM-WRITING-CORPUS-2024","LRM-ROON-REFERENCE-2026-09-25"}

def validate(data):
    issues=[]
    if data.get("schema")!="TAKY_LEARNING_REFERENCE_ROLE_MIGRATION_CANDIDATE_V1":
        issues.append("SCHEMA_INVALID")
    if data.get("status")!="AWAITING_CENTRAL_INDEX_OWNER_REVIEW":
        issues.append("STATUS_INVALID")
    guards=data.get("authority_guards") or {}
    for key in [
        "central_index_authority","canonical_promotion",
        "learning_index_runtime_consumption_before_index_owner_review"
    ]:
        if guards.get(key) is not False: issues.append("AUTHORITY_GUARD_INVALID:"+key)
    if guards.get("mined_reference_is_not_authority") is not True:
        issues.append("MINED_AUTHORITY_GUARD_MISSING")
    rows=data.get("candidates") or []
    ids={x.get("candidate_id") for x in rows if isinstance(x,dict)}
    if ids!=EXPECTED_IDS: issues.append("CANDIDATE_SET_MISMATCH")
    drive_ids=[]
    for i,row in enumerate(rows):
        p=f"ROW_{i}:"
        if row.get("source_canonical") is not False: issues.append(p+"SOURCE_CANONICAL_MUST_BE_FALSE")
        if row.get("index_owner_review_required") is not True: issues.append(p+"INDEX_OWNER_REVIEW_REQUIRED")
        role=row.get("proposed_learning_evidence_role")
        if role not in ALLOWED_ROLES: issues.append(p+"ROLE_INVALID")
        did=str(row.get("drive_file_id") or "").strip()
        if not did: issues.append(p+"DRIVE_FILE_ID_REQUIRED")
        drive_ids.append(did)
        if not row.get("allowed_use"): issues.append(p+"ALLOWED_USE_REQUIRED")
        if not row.get("forbidden_use"): issues.append(p+"FORBIDDEN_USE_REQUIRED")
    if len(set(drive_ids))!=len(drive_ids): issues.append("DUPLICATE_DRIVE_FILE_ID")
    unresolved={x.get("role"):x.get("state") for x in data.get("unresolved_reference_roles") or []}
    if unresolved.get("ENGLISH_LEXICAL_SEMANTICS")!="OPEN":
        issues.append("ENGLISH_LEXICAL_OPEN_REQUIRED")
    if unresolved.get("ENGLISH_LANGUAGE_USAGE")!="OPEN":
        issues.append("ENGLISH_USAGE_OPEN_REQUIRED")
    roon=next((x for x in rows if x.get("candidate_id")=="LRM-ROON-REFERENCE-2026-09-25"),{})
    if "lexical-definition authority" not in (roon.get("forbidden_use") or []):
        issues.append("ROON_LEXICAL_AUTHORITY_FORBIDDEN_GUARD_MISSING")
    return {"pass":not issues,"issues":issues,"candidate_count":len(rows),"next_handoff":data.get("next_handoff")}

def main():
    data=json.loads(PATH.read_text(encoding="utf-8"))
    out=validate(data)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
