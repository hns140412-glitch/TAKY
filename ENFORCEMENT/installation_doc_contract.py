#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

REQUIRED_LISTS=("fallbacks","observable_verification","prohibited_actions","provenance_refs")
VALID_SURFACES={"TERMINAL","APP_UI","BROWSER","IDE"}

def _text(v: object)->bool:
    return isinstance(v,str) and bool(v.strip())

def validate_install_doc(record: dict[str,Any])->list[str]:
    failures=[]
    if not _text(record.get("guide_id")): failures.append("INSTALL_GUIDE_ID_MISSING")
    if not _text(record.get("tool_name")): failures.append("INSTALL_TOOL_NAME_MISSING")
    surface=record.get("execution_surface")
    if surface not in VALID_SURFACES: failures.append("INSTALL_EXECUTION_SURFACE_INVALID")
    if not _text(record.get("primary_action")): failures.append("INSTALL_PRIMARY_ACTION_MISSING")
    for key in REQUIRED_LISTS:
        v=record.get(key)
        if not isinstance(v,list) or not v or not all(_text(x) for x in v):
            failures.append("INSTALL_"+key.upper()+"_MISSING")
    lic=record.get("license")
    if not isinstance(lic,dict) or not _text(lic.get("status")) or not _text(lic.get("source_ref")):
        failures.append("INSTALL_LICENSE_EVIDENCE_MISSING")
    if record.get("credentials_required") is True:
        if not _text(record.get("credential_scope")):
            failures.append("INSTALL_CREDENTIAL_SCOPE_MISSING")
        if record.get("secret_logging_forbidden") is not True:
            failures.append("INSTALL_SECRET_LOGGING_GUARD_MISSING")
    if record.get("success_claim")=="INSTALLED" and not record.get("observable_verification"):
        failures.append("INSTALL_SUCCESS_WITHOUT_OBSERVATION")
    return list(dict.fromkeys(failures))

def main()->int:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--record",type=Path,required=True)
    args=ap.parse_args()
    r=json.loads(args.record.read_text(encoding="utf-8-sig"))
    failures=validate_install_doc(r)
    print(json.dumps({"pass":not failures,"failures":failures,"guide_id":r.get("guide_id")},ensure_ascii=False))
    return 0 if not failures else 2

if __name__=="__main__":
    raise SystemExit(main())
