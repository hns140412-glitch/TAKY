#!/usr/bin/env python3
import json, sys
from pathlib import Path

PRODUCTION_CLASSES={"PREVIEW","FINAL","USER_FACING"}
FORBIDDEN={"DESTRUCTIVE_RASTER_MASK","GENERATIVE_GEOMETRY_REDRAW","ONE_OFF_RENDERER","UNVERIFIED_SEMANTIC_INFERENCE"}
REQUIRED_GATES=["SOURCE","GEOMETRY","FACT","SEMANTIC","REFERENCE_EFFECT","ARCHITECTURAL_READABILITY","USER_EFFECT"]

def clean(v):
    return str(v or "").strip()

def validate(record):
    failures=[]
    artifact_class=clean(record.get("artifact_class")).upper()
    if artifact_class not in PRODUCTION_CLASSES:
        return failures if not record.get("user_exposure_requested") else ["NON_PRODUCTION_USER_EXPOSURE_FORBIDDEN"]

    if record.get("one_off_implementation_used"):
        failures.append("ONE_OFF_PRODUCTION_FORBIDDEN")
    for op in record.get("operations") or []:
        op=clean(op).upper()
        if op in FORBIDDEN:
            failures.append("FORBIDDEN_PRODUCTION_OPERATION:"+op)

    receipt=record.get("execution_receipt")
    if not isinstance(receipt,dict):
        failures.append("EXECUTION_RECEIPT_REQUIRED")
        receipt={}
    if clean(receipt.get("receipt_type")).upper()!="AUTHORIZED_ENGINE_EXECUTION":
        failures.append("INVALID_RECEIPT_TYPE")
    if clean(receipt.get("route")).upper().replace(" ","")!="TASK>ROUTER>AUTHORIZED_ENGINE":
        failures.append("INVALID_EXECUTION_ROUTE")
    for k in ["engine_id","engine_version","engine_commit_sha","source_digest","artifact_digest","validation_bundle_id"]:
        if not clean(receipt.get(k)):
            failures.append("RECEIPT_FIELD_REQUIRED:"+k)

    bundle=record.get("validation_bundle")
    if not isinstance(bundle,dict):
        failures.append("VALIDATION_BUNDLE_REQUIRED")
        bundle={}
    for k in ["validation_bundle_id","source_digest","artifact_digest"]:
        if not clean(bundle.get(k)):
            failures.append("VALIDATION_FIELD_REQUIRED:"+k)

    if clean(receipt.get("validation_bundle_id"))!=clean(bundle.get("validation_bundle_id")):
        failures.append("VALIDATION_BUNDLE_RECEIPT_MISMATCH")
    if clean(receipt.get("source_digest"))!=clean(bundle.get("source_digest")):
        failures.append("SOURCE_DIGEST_RECEIPT_MISMATCH")
    if clean(receipt.get("artifact_digest"))!=clean(bundle.get("artifact_digest")):
        failures.append("ARTIFACT_DIGEST_RECEIPT_MISMATCH")

    required=list(REQUIRED_GATES)
    if record.get("narrative_present"): required.append("NARRATIVE_EVIDENCE")
    if record.get("a3_required"): required.append("A3")
    gates=bundle.get("gates") if isinstance(bundle.get("gates"),dict) else {}
    for name in required:
        entry=gates.get(name)
        if not isinstance(entry,dict):
            failures.append("GATE_EVIDENCE_REQUIRED:"+name)
            continue
        if clean(entry.get("status")).upper()!="PASS":
            failures.append("GATE_NOT_PASS:"+name)
        if not clean(entry.get("validator")):
            failures.append("GATE_VALIDATOR_REQUIRED:"+name)
        refs=entry.get("evidence_refs")
        if not isinstance(refs,list) or not refs or any(not clean(x) for x in refs):
            failures.append("GATE_EVIDENCE_REF_REQUIRED:"+name)

    if record.get("user_exposure_requested") and failures:
        failures.append("NO_PASS_NO_SHOW")

    return list(dict.fromkeys(failures))

def main():
    if len(sys.argv)!=2:
        print("usage: artifact_exposure_contract_validator.py <record.json>", file=sys.stderr)
        return 2
    record=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    failures=validate(record)
    print(json.dumps({"ok":not failures,"failures":failures},ensure_ascii=False,indent=2))
    return 0 if not failures else 1

if __name__=="__main__":
    raise SystemExit(main())
