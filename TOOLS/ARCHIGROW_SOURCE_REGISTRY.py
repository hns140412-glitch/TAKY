#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"DOMAIN"/"ARCHITECTURE_SOURCE_REGISTRY.json"
ALLOWED_AUTH={"VERIFIED_OFFICIAL","VERIFIED_OFFICIAL_WEB_VIEW","OFFICIAL_PUBLIC_DATA_PORTAL_CONFIRMED__PROVIDER_SPEC_RECHECK_REQUIRED"}
ALLOWED_ADAPTER={"CONTRACT_READY_NOT_CONFIGURED","MANUAL_OR_BROWSER_EVIDENCE_ONLY","HOLD_UNTIL_DIRECT_PROVIDER_SPEC_RECHECK"}

def load_registry(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate(registry):
    issues=[]
    if registry.get("schema")!="ARCHIGROW_SOURCE_REGISTRY_V1": issues.append("SCHEMA_INVALID")
    rows=registry.get("sources") or []
    ids=[str(x.get("source_id") or "").strip() for x in rows]
    if not rows: issues.append("SOURCES_REQUIRED")
    if any(not x for x in ids): issues.append("SOURCE_ID_REQUIRED")
    if len(ids)!=len(set(ids)): issues.append("SOURCE_ID_DUPLICATE")
    banned={"api_key","token","secret","password","service_key","oc"}
    def walk(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k.lower() in banned and str(x or "").strip(): issues.append("SECRET_MATERIAL_FORBIDDEN")
                walk(x)
        elif isinstance(v,list):
            for x in v: walk(x)
    walk(registry)
    for row in rows:
        if row.get("authority_status") not in ALLOWED_AUTH: issues.append("AUTHORITY_STATUS_INVALID:"+str(row.get("source_id")))
        if row.get("adapter_status") not in ALLOWED_ADAPTER: issues.append("ADAPTER_STATUS_INVALID:"+str(row.get("source_id")))
        if not str(row.get("authority_url") or "").startswith("https://"): issues.append("HTTPS_AUTHORITY_URL_REQUIRED:"+str(row.get("source_id")))
        if row.get("credential_storage") not in {"NONE","EXTERNAL_SECRET_ONLY","EXTERNAL_SECRET_ONLY_IF_REQUIRED"}:
            issues.append("CREDENTIAL_STORAGE_INVALID:"+str(row.get("source_id")))
    return {"ok":not issues,"issues":issues}

def source(source_id, registry=None):
    r=registry or load_registry()
    return next((x for x in r.get("sources",[]) if x.get("source_id")==source_id),None)

def qualify_target_fact(source_id, *, target_project_id="", evidence_ref="", observed_as_of="", applicability_status="", registry=None):
    row=source(source_id,registry)
    blockers=[]
    if not row: return {"ok":False,"blockers":["SOURCE_NOT_REGISTERED"]}
    if row.get("target_fact_eligible") is not True: blockers.append("SOURCE_NOT_TARGET_FACT_ELIGIBLE")
    if row.get("authority_status") not in {"VERIFIED_OFFICIAL","VERIFIED_OFFICIAL_WEB_VIEW"}: blockers.append("DIRECT_AUTHORITY_NOT_VERIFIED")
    if not str(target_project_id).strip(): blockers.append("TARGET_PROJECT_ID_REQUIRED")
    if not str(evidence_ref).strip(): blockers.append("EVIDENCE_REF_REQUIRED")
    if row.get("effective_date_required") and not str(observed_as_of).strip(): blockers.append("OBSERVED_AS_OF_REQUIRED")
    if applicability_status not in {"APPLICABLE","TARGET_IDENTITY_MATCHED"}: blockers.append("APPLICABILITY_NOT_CONFIRMED")
    return {
      "ok":not blockers,
      "source_id":source_id,
      "target_project_id":str(target_project_id).strip() or None,
      "evidence_ref":str(evidence_ref).strip() or None,
      "observed_as_of":str(observed_as_of).strip() or None,
      "applicability_status":applicability_status or None,
      "blockers":blockers,
      "rule":"REGISTERED OFFICIAL SOURCE != TARGET PROJECT FACT WITHOUT IDENTITY/APPLICABILITY/EFFECTIVE-DATE EVIDENCE"
    }

if __name__=="__main__":
    result=validate(load_registry())
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["ok"] else 2)
