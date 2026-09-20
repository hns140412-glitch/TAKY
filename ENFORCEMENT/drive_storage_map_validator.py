#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"OS"/"DRIVE_STORAGE_MAP.json"
d=json.loads(p.read_text(encoding="utf-8"))
fail=[]

if d.get("authority",{}).get("github")!="CANONICAL_GOVERNANCE":
    fail.append("GITHUB_AUTHORITY_MISSING")
if d.get("authority",{}).get("drive_is_canonical_governance") is not False:
    fail.append("DRIVE_CANONICAL_AUTHORITY_MUST_BE_FALSE")
root=d.get("root") or {}
if root.get("name")!="TAKY" or root.get("role")!="SINGLE_DRIVE_ENTRYPOINT":
    fail.append("DRIVE_SINGLE_ENTRYPOINT_INVALID")

required={"ACTIVE","PROJECTS","REVIEWS_C2S","HANDOFF","ARCHIVE"}
roles=d.get("roles") or {}
if set(roles)!=required:
    fail.append("ROLE_SET_INVALID:"+",".join(sorted(roles)))

ids=[]
for role,meta in roles.items():
    if not str(meta.get("id","")).strip():
        fail.append(f"MISSING_ROLE_ID:{role}")
    else:
        ids.append(meta["id"])
    if not str(meta.get("name","")).strip():
        fail.append(f"MISSING_ROLE_NAME:{role}")
if len(ids)!=len(set(ids)):
    fail.append("DUPLICATE_ROLE_FOLDER_ID")

legacy=((roles.get("ARCHIVE") or {}).get("children") or {}).get("LEGACY_NOTEBOOKLM_RECOVERY") or {}
if legacy.get("default_activation") is not False:
    fail.append("NOTEBOOKLM_LEGACY_DEFAULT_MUST_BE_FALSE")

rules=d.get("routing_rules") or []
required_fragments=[
    "Do not create a new TAKY sibling root",
    "Preserve Drive file IDs",
    "Do not delete same-name items based on name alone",
    "NotebookLM material is legacy/optional"
]
for frag in required_fragments:
    if not any(frag in x for x in rules):
        fail.append("MISSING_ROUTING_RULE:"+frag)

if fail:
    print("FAIL: Drive storage map")
    for x in fail: print(x)
    raise SystemExit(1)
print("PASS: Drive storage map has one entrypoint, unique role folders, preserved authority boundary, NotebookLM default off")
