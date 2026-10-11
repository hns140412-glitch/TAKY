from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

VERSION = "TAKY_ASSET_DISTRIBUTION_MANIFEST_VALIDATOR_V1"
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ALLOWED_STATUS = {"APPROVED_FOR_DISTRIBUTION"}
ALLOWED_SCOPE = {"PUBLIC_RELEASE_SAFE","FAMILY_PRIVATE_AUTHENTICATED","INTERNAL_ONLY"}
REQUIRED = {
    "slot_id","asset_id","master_ref","master_revision","source_sha256",
    "distribution_ref","distribution_sha256","mime_type","release_scope",
    "consumer_apps","status"
}

def validate(doc: dict) -> list[str]:
    errors=[]
    if doc.get("schema")!="TAKY_ASSET_DISTRIBUTION_MANIFEST_V1":
        errors.append("SCHEMA_MISMATCH")
    if not str(doc.get("package_id") or "").strip():
        errors.append("PACKAGE_ID_MISSING")
    if not str(doc.get("package_version") or "").strip():
        errors.append("PACKAGE_VERSION_MISSING")
    if doc.get("source_authority")!="HNS_DRIVE_APPROVED_ASSET_MASTER":
        errors.append("SOURCE_AUTHORITY_INVALID")
    if doc.get("distribution_authority")!="SIEZEALL_DRIVE_APPROVED_PACKAGE":
        errors.append("DISTRIBUTION_AUTHORITY_INVALID")
    assets=doc.get("assets")
    if not isinstance(assets,list) or not assets:
        errors.append("ASSETS_EMPTY")
        return errors
    slots=set(); asset_ids=set()
    for i,a in enumerate(assets):
        if not isinstance(a,dict):
            errors.append(f"ASSET_{i}_NOT_OBJECT"); continue
        missing=sorted(REQUIRED-set(a))
        if missing:
            errors.append(f"ASSET_{i}_MISSING:"+",".join(missing))
        slot=str(a.get("slot_id") or "").strip()
        aid=str(a.get("asset_id") or "").strip()
        if not slot: errors.append(f"ASSET_{i}_SLOT_EMPTY")
        elif slot in slots: errors.append(f"ASSET_{i}_DUPLICATE_SLOT:{slot}")
        slots.add(slot)
        if not aid: errors.append(f"ASSET_{i}_ASSET_ID_EMPTY")
        elif aid in asset_ids: errors.append(f"ASSET_{i}_DUPLICATE_ASSET_ID:{aid}")
        asset_ids.add(aid)
        for k in ("source_sha256","distribution_sha256"):
            if not SHA_RE.match(str(a.get(k) or "")):
                errors.append(f"ASSET_{i}_{k.upper()}_INVALID")
        if a.get("status") not in ALLOWED_STATUS:
            errors.append(f"ASSET_{i}_STATUS_INVALID")
        scope=a.get("release_scope")
        if scope not in ALLOWED_SCOPE:
            errors.append(f"ASSET_{i}_RELEASE_SCOPE_INVALID")
        if scope=="INTERNAL_ONLY":
            errors.append(f"ASSET_{i}_INTERNAL_ONLY_CANNOT_DISTRIBUTE")
        if not isinstance(a.get("consumer_apps"),list) or not a.get("consumer_apps"):
            errors.append(f"ASSET_{i}_CONSUMERS_EMPTY")
        ref=str(a.get("distribution_ref") or "")
        if ref.startswith("http") and "netlify" in ref.lower():
            errors.append(f"ASSET_{i}_NETLIFY_REF_NOT_IDENTITY_AUTHORITY")
    required_slots=doc.get("required_slots") or []
    if isinstance(required_slots,list):
        missing=[s for s in required_slots if s not in slots]
        if missing: errors.append("REQUIRED_SLOTS_MISSING:"+",".join(missing))
    return errors

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    args=ap.parse_args()
    doc=json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    errors=validate(doc)
    out={"validator":VERSION,"state":"PASS" if not errors else "HOLD","errors":errors,"asset_count":len(doc.get("assets") or [])}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
