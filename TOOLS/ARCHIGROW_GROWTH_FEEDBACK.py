#!/usr/bin/env python3
"""ARCHI GROW: evidence-bound application and targeted growth feedback.
Candidate-only: never promotes authority, alters originals, or invokes external APIs.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROUTES = {
    "SOURCE_MISSING": "MINING",
    "SOURCE_STALE": "MINING",
    "RELATION_MISSING": "INDEXING",
    "CONTRACT_MISSING": "FORMING",
    "METHOD_WEAK": "LEARNING",
    "IMPLEMENTATION_MISSING": "EXECUTION",
    "OUTPUT_QUALITY": "FORMING",
    "REGRESSION_FAIL": "EXECUTION",
}
VALID_STATES = {"PRESERVE", "ADOPT", "ADJUST", "HOLD", "REJECT", "CONFLICT", "SUPERSEDED"}
VALID_RESULTS = {"PASS", "HOLD", "FAIL", "UNVERIFIED"}

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def evaluate(record):
    if not isinstance(record, dict):
        raise ValueError("RECORD_NOT_OBJECT")
    for name in ("case_id", "project_id", "source_ref", "target_artifact", "decision", "result"):
        if not isinstance(record.get(name), str) or not record[name].strip():
            raise ValueError("MISSING_" + name.upper())
    if record["decision"] not in VALID_STATES:
        raise ValueError("INVALID_DECISION")
    if record["result"] not in VALID_RESULTS:
        raise ValueError("INVALID_RESULT")
    if record["decision"] == "ADOPT" and record["result"] == "PASS":
        for field in ("implementation_ref", "verification_ref", "before_after_ref"):
            if not record.get(field):
                return {"case_id": record["case_id"], "status": "HOLD", "reason": "APPLICATION_EVIDENCE_MISSING", "next_route": "EXECUTION", "source_ref": record["source_ref"]}
        return {"case_id": record["case_id"], "status": "APPLIED_VERIFIED", "reason": "EVIDENCE_BOUND", "next_route": "REUSE_CANDIDATE", "source_ref": record["source_ref"]}
    gap = record.get("gap_type") or ("IMPLEMENTATION_MISSING" if record["decision"] == "ADOPT" else "METHOD_WEAK")
    if gap not in ROUTES:
        raise ValueError("UNKNOWN_GAP_TYPE")
    return {"case_id": record["case_id"], "status": "HOLD" if record["result"] != "FAIL" else "FAIL", "reason": gap, "next_route": ROUTES[gap], "source_ref": record["source_ref"]}

def run(payload):
    if payload.get("schema") != "ARCHI_GROW_GROWTH_FEEDBACK_V1":
        raise ValueError("INVALID_SCHEMA")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("RECORDS_NOT_LIST")
    ids = [r.get("case_id") for r in records if isinstance(r, dict)]
    if len(ids) != len(records) or len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_OR_INVALID_CASE")
    decisions = [evaluate(r) for r in records]
    return {"schema": "ARCHI_GROW_GROWTH_FEEDBACK_RESULT_V1", "input_sha256": digest(payload), "results": decisions, "counts": {k: sum(r["status"] == k for r in decisions) for k in ("APPLIED_VERIFIED", "HOLD", "FAIL")}, "authority_promoted": False}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    inp = Path(a.input).resolve()
    out = Path(a.output).resolve()
    if inp == out:
        raise ValueError("INPUT_OUTPUT_SAME")
    result = run(json.loads(inp.read_text(encoding="utf-8")))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "counts": result["counts"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
