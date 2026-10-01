#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

SCHEMA="TAKY_READY_OFFICIAL_STANDARD_REGISTRY_MIGRATION_CANDIDATE_V1"
EXPECTED={"국어":34,"수학":45,"사회":27,"과학":51,"영어":20}
ALLOWED_STATES={"AWAITING_CENTRAL_INDEX_OWNER_REVIEW"}

def load(path:Path)->dict[str,Any]:
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict): raise ValueError("MIGRATION_OBJECT_REQUIRED")
    return data

def validate(data:dict[str,Any])->dict[str,Any]:
    issues=[]
    if data.get("schema")!=SCHEMA: issues.append("SCHEMA_INVALID")
    if data.get("status") not in ALLOWED_STATES: issues.append("STATUS_INVALID")
    contract=data.get("migration_contract") or {}
    if contract.get("central_index_authority") is not False: issues.append("CENTRAL_AUTHORITY_MUST_BE_FALSE")
    if contract.get("canonical_promotion") is not False: issues.append("CANONICAL_PROMOTION_MUST_BE_FALSE")
    if contract.get("learning_index_consumption_allowed_before_index_owner_review") is not False:
        issues.append("PRE_REVIEW_LEARNING_CONSUMPTION_FORBIDDEN")
    rows=data.get("records")
    if not isinstance(rows,list): return {"pass":False,"issues":issues+["RECORDS_REQUIRED"]}
    if len(rows)!=sum(EXPECTED.values()): issues.append("RECORD_COUNT_MISMATCH")
    by_subject={k:0 for k in EXPECTED}
    codes=[]
    source_ids=[]
    for i,row in enumerate(rows):
        prefix=f"ROW_{i}:"
        if not isinstance(row,dict):
            issues.append(prefix+"OBJECT_REQUIRED"); continue
        code=str(row.get("standard_code") or "").strip()
        subject=str(row.get("subject") or "").strip()
        if not code: issues.append(prefix+"STANDARD_CODE_REQUIRED")
        if subject not in EXPECTED: issues.append(prefix+"SUBJECT_INVALID")
        else: by_subject[subject]+=1
        codes.append(code)
        proposed=row.get("proposed_index_record") or {}
        sid=str(proposed.get("source_id") or "").strip()
        source_ids.append(sid)
        if proposed.get("index_state") is not None: issues.append(prefix+"INDEX_STATE_MUST_BE_NULL")
        if row.get("central_index_authority") is not False: issues.append(prefix+"ROW_AUTHORITY_MUST_BE_FALSE")
        if row.get("canonical_promotion") is not False: issues.append(prefix+"ROW_PROMOTION_MUST_BE_FALSE")
        if row.get("migration_state")!="AWAITING_CENTRAL_INDEX_OWNER_REVIEW":
            issues.append(prefix+"MIGRATION_STATE_INVALID")
        tags=set(proposed.get("provenance_tags") or [])
        required={"OFFICIAL_EDUCATION_SOURCE","OFFICIAL_STANDARD_REF","CURRICULUM_ALIGNMENT","READY_VERIFIED_REGISTRY_LINEAGE"}
        if not required.issubset(tags): issues.append(prefix+"PROVENANCE_TAGS_INCOMPLETE")
        if proposed.get("source_family")!="OFFICIAL_CURRICULUM":
            issues.append(prefix+"SOURCE_FAMILY_INVALID")
        if proposed.get("source_type")!="OFFICIAL_ACHIEVEMENT_STANDARD":
            issues.append(prefix+"SOURCE_TYPE_INVALID")
        url=str(row.get("source_url") or "")
        if not url.startswith("https://"): issues.append(prefix+"SOURCE_URL_INVALID")
        if proposed.get("origin_locator")!=url: issues.append(prefix+"ORIGIN_URL_MISMATCH")
        if not str(row.get("semantic_summary") or "").strip():
            issues.append(prefix+"SEMANTIC_SUMMARY_REQUIRED")
    if len(set(codes))!=len(codes): issues.append("DUPLICATE_STANDARD_CODE")
    if len(set(source_ids))!=len(source_ids): issues.append("DUPLICATE_SOURCE_ID")
    if by_subject!=EXPECTED: issues.append("SUBJECT_COVERAGE_MISMATCH")
    source_coverage=data.get("source_coverage") or {}
    for subject,count in EXPECTED.items():
        row=source_coverage.get(subject) or {}
        if row.get("verified_record_count")!=count or row.get("expected_total")!=count:
            issues.append("SOURCE_COVERAGE_MISMATCH:"+subject)
    return {
        "pass":not issues,
        "issues":issues,
        "record_count":len(rows),
        "by_subject":by_subject,
        "central_index_authority":False,
        "next_handoff":"INDEPENDENT_INDEX_OWNER_REVIEW"
    }

def main()->int:
    path=Path(__file__).resolve().parents[1]/"MIGRATION/CURRICULUM/READY_OFFICIAL_STANDARD_REGISTRY_2026-10-02_V1.json"
    result=validate(load(path))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
