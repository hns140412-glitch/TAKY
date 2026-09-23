import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
V=ROOT/"artifact_exposure_contract_validator.py"

def run(name, expect):
    p=ROOT/"fixtures"/name
    r=subprocess.run([sys.executable,str(V),str(p)],capture_output=True,text=True)
    assert (r.returncode==0)==expect, (name,r.returncode,r.stdout,r.stderr)

run("artifact_exposure_pass.json",True)
run("artifact_exposure_self_asserted_fail.json",False)
run("artifact_exposure_receipt_mismatch_fail.json",False)
run("artifact_exposure_oneoff_fail.json",False)
print("artifact_exposure_contract_validator: PASS")
