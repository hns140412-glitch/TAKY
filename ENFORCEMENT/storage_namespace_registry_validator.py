#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/"MASTER/STORAGE_NAMESPACE_REGISTRY.json").read_text(encoding="utf-8"))
drive=json.loads((ROOT/"OS/DRIVE_STORAGE_MAP.json").read_text(encoding="utf-8"))
fail=[]

taky=reg.get("TAKY") or {}
for ns in ("LEARNING","ARCHIGROW","COMMON","TEMP"):
    if ns not in taky:
        fail.append("MISSING_NAMESPACE:"+ns)

if (reg.get("SAVEY") or {}).get("separate_top_level") is not True:
    fail.append("SAVEY_NOT_SEPARATE")
if (reg.get("SAVEY") or {}).get("implicit_taky_route") is not False:
    fail.append("SAVEY_IMPLICIT_TAKY_ROUTE_FORBIDDEN")

expected={
    "LEARNING":("TAKY/01_LEARNING","TAKY/01_LEARNING_SHARE"),
    "ARCHIGROW":("TAKY/02_ARCHIGROW","TAKY/02_ARCHIGROW_SHARE"),
    "COMMON":("TAKY/03_COMMON","TAKY/03_UPDATES"),
    "TEMP":("TAKY/90_TEMP","TAKY/90_TEMP"),
}
for ns,(hns,share) in expected.items():
    row=taky.get(ns) or {}
    if row.get("hns_drive")!=hns:
        fail.append(f"HNS_PATH_MISMATCH:{ns}")
    if row.get("siezeall_drive")!=share:
        fail.append(f"SIEZEALL_PATH_MISMATCH:{ns}")

for rel in ("LEARNING/NAMESPACE.json","ARCHIGROW/NAMESPACE.json","COMMON/NAMESPACE.json"):
    p=ROOT/rel
    if not p.exists():
        fail.append("NAMESPACE_POINTER_MISSING:"+rel)
    else:
        json.loads(p.read_text(encoding="utf-8"))

if (ROOT/"TEMP").exists():
    fail.append("TEMP_MUST_NOT_BE_TRACKED_AS_DURABLE_GITHUB_CONTENT")

rules=drive.get("routing_rules") or []
if not any("SAVEY is a separate top-level system" in r for r in rules):
    fail.append("DRIVE_SAVEY_BOUNDARY_MISSING")
if not any("GitHub stores code/schema/manifest pointers" in r for r in rules):
    fail.append("GITHUB_ROLE_RULE_MISSING")

savey_repo=((reg.get("SAVEY") or {}).get("github") or {})
if savey_repo.get("repository") is None and savey_repo.get("state")!="SEPARATE_REPOSITORY_NOT_CREATED":
    fail.append("SAVEY_REPO_STATE_INVALID")

if fail:
    print("FAIL: storage namespace alignment")
    for x in fail: print(x)
    raise SystemExit(1)
print("PASS: GitHub/Drive/local namespace alignment")
