#!/usr/bin/env python3
"""One-command fail-closed resume preparation acceptance for a declared recovered scope.

Required: raw manifest, inventory, coverage, self-contained bundle and existing
resume evidence. This does not auto-invoke in hosted ChatGPT or establish that
the source universe has been completely discovered.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from raw_source_resume_audit import audit

def run(root,manifest,inventory,coverage,bundle):
    failures=[]
    try:
        failures.extend(audit(root,manifest,inventory,coverage))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        failures.append(f"RAW_AUDIT_EXCEPTION: {exc}")
    if not failures:
        proc=subprocess.run([sys.executable,str(Path(__file__).with_name("handoff_bundle_validator.py")),str(bundle)],
                            capture_output=True,text=True)
        if proc.returncode:
            failures.append("BUNDLE_VALIDATION_FAILED: "+proc.stdout[-3000:]+proc.stderr[-1000:])
    return {"pass":not failures,"status":"PASS_DECLARED_RECOVERED_SCOPE" if not failures else "FAIL_CLOSED",
            "errors":failures,"claim_boundary":"NOT proof of unlisted history, hosted automatic execution, live HEAD, or semantic extraction completeness"}

def main():
    p=argparse.ArgumentParser()
    for name in ("source_root","raw_manifest","inventory","handoff_coverage","bundle"):
        p.add_argument(name,type=Path)
    a=p.parse_args()
    result=run(a.source_root,a.raw_manifest,a.inventory,a.handoff_coverage,a.bundle)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(not result["pass"])
if __name__=="__main__":raise SystemExit(main())
