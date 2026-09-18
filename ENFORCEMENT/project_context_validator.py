#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

REQUIRED_TOP = [
    "project_id","context_gate_required","recovery_policy",
    "required_taky_rules","required_project_contracts","required_current_state",
    "hard_locks","known_conflicts_or_open","superseded_or_rejected",
    "drive_long_memory","notebooklm_recovery","context_pass_conditions"
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--resolved", default=None, help="JSON file with resolved ids/conditions")
    args=ap.parse_args()
    p=Path(args.manifest)
    data=json.loads(p.read_text(encoding="utf-8"))
    errors=[]
    for k in REQUIRED_TOP:
        if k not in data:
            errors.append(f"MISSING_TOP:{k}")
    if data.get("context_gate_required") is not True:
        errors.append("CONTEXT_GATE_NOT_REQUIRED")
    rp=data.get("recovery_policy",{})
    if rp.get("ask_last") is not True: errors.append("ASK_LAST_REQUIRED")
    if rp.get("full_scan_last") is not True: errors.append("FULL_SCAN_LAST_REQUIRED")
    contracts=data.get("required_project_contracts",[])
    if not contracts: errors.append("NO_REQUIRED_PROJECT_CONTRACTS")
    for c in contracts:
        if c.get("required") and not c.get("id"):
            errors.append("REQUIRED_CONTRACT_ID_MISSING")
    nb=data.get("notebooklm_recovery",{})
    if nb.get("authority")!="REFERENCE_ONLY_EVIDENCE_ASSIST":
        errors.append("NOTEBOOKLM_AUTHORITY_BOUNDARY_FAIL")

    if args.resolved:
        r=json.loads(Path(args.resolved).read_text(encoding="utf-8"))
        resolved=set(r.get("resolved_contracts",[]))
        for c in contracts:
            if c.get("required") and c.get("id") not in resolved:
                errors.append(f"REQUIRED_CONTEXT_MISSING:{c.get('id')}")
        if not r.get("latest_corrections_loaded",False):
            errors.append("LATEST_CORRECTIONS_NOT_LOADED")
        if not r.get("current_implementation_loaded",False):
            errors.append("CURRENT_IMPLEMENTATION_NOT_LOADED")
        if not r.get("reverse_reconstruction_pass",False):
            errors.append("REVERSE_RECONSTRUCTION_FAIL")

    if errors:
        print(json.dumps({"status":"FAIL","errors":errors},ensure_ascii=False,indent=2))
        return 1
    print(json.dumps({"status":"PASS","project_id":data.get("project_id")},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())
