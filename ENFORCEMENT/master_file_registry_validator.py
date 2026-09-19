#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
master=ROOT/"MASTER"
registry=json.loads((master/"MASTER_FILE_REGISTRY.json").read_text(encoding="utf-8"))
classes=set(registry.get("classes",{}))
entries=registry.get("files",{})
actual={str(p.relative_to(ROOT)).replace("\\","/") for p in master.iterdir() if p.is_file()}
fail=[]

missing=sorted(actual-set(entries))
stale=sorted(set(entries)-actual)
if missing: fail.append("UNCLASSIFIED_MASTER_FILES:"+",".join(missing))
if stale: fail.append("REGISTRY_REFERENCES_MISSING_FILES:"+",".join(stale))

for path,meta in entries.items():
    cls=meta.get("class")
    if cls not in classes:
        fail.append(f"INVALID_CLASS:{path}:{cls}")
    if cls=="LEGACY_OPTIONAL" and meta.get("default_activation") is not False:
        fail.append(f"LEGACY_DEFAULT_NOT_FALSE:{path}")
    if cls=="CANDIDATE" and meta.get("canonical") is not False:
        fail.append(f"CANDIDATE_CANONICAL_NOT_FALSE:{path}")

# High-risk known artifacts must never silently become active.
for path in (
    "MASTER/REMASTER_REV00_DRAFT.md",
    "MASTER/NOTEBOOKLM_RECOVERY_PROTOCOL.md",
    "MASTER/NOTEBOOKLM_SOURCE_SCHEMA.json",
):
    if entries.get(path,{}).get("class") in {"ACTIVE_OWNER","ACTIVE_SUPPORT"}:
        fail.append(f"HIGH_RISK_ARTIFACT_MISCLASSIFIED_ACTIVE:{path}")

if fail:
    print("FAIL: MASTER file authority registry")
    for x in fail: print(x)
    raise SystemExit(1)
print(f"PASS: MASTER file authority registry covers {len(actual)} files; no unclassified root artifacts")
