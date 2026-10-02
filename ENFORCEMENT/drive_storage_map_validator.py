#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"OS"/"DRIVE_STORAGE_MAP.json"
d=json.loads(p.read_text(encoding="utf-8"))
fail=[]

auth=d.get("authority",{})
if auth.get("github")!="CANONICAL_GOVERNANCE_AND_CODE":
    fail.append("GITHUB_AUTHORITY_INVALID")
if auth.get("drive_is_canonical_governance") is not False:
    fail.append("DRIVE_CANONICAL_AUTHORITY_MUST_BE_FALSE")
if auth.get("netlify")!="PWA_SHELL_DELIVERY_ONLY":
    fail.append("NETLIFY_ROLE_INVALID")

for account in ("hns","siezeall"):
    node=d.get(account) or {}
    root=node.get("taky_root") or {}
    if root.get("name")!="TAKY" or not str(root.get("id","")).strip():
        fail.append(f"{account.upper()}_TAKY_ROOT_INVALID")
    savey=node.get("savey_root") or {}
    if savey.get("name")!="SAVEY" or savey.get("separate_from_taky") is not True:
        fail.append(f"{account.upper()}_SAVEY_BOUNDARY_INVALID")
    ids=[str((m or {}).get("id","")).strip() for m in (node.get("roles") or {}).values()]
    if not ids or any(not x for x in ids):
        fail.append(f"{account.upper()}_ROLE_ID_MISSING")
    if len(ids)!=len(set(ids)):
        fail.append(f"{account.upper()}_DUPLICATE_ROLE_ID")

required_hns={"LEARNING","ARCHIGROW","COMMON","TEMP","DELETE_PENDING"}
if set((d.get("hns") or {}).get("roles") or {})!=required_hns:
    fail.append("HNS_ROLE_SET_INVALID")
required_share={"LEARNING_SHARE","ARCHIGROW_SHARE","UPDATES","USER_DATA","TEMP"}
if set((d.get("siezeall") or {}).get("roles") or {})!=required_share:
    fail.append("SIEZEALL_ROLE_SET_INVALID")

local=d.get("local_execution") or {}
if local.get("inbox")!="C:/TAKY_LOCAL/01_INBOX":
    fail.append("LOCAL_INBOX_INVALID")
if local.get("high_churn_cache_in_drive") is not False:
    fail.append("HIGH_CHURN_CACHE_MUST_STAY_LOCAL")
if local.get("git_repositories_in_drive") is not False:
    fail.append("GIT_REPOS_MUST_STAY_OUT_OF_DRIVE")

rules=d.get("routing_rules") or []
for frag in [
    "All TAKY Drive material must live below TAKY root.",
    "SAVEY is a separate top-level system",
    "automatic only when Wi-Fi is positively confirmed",
    "manifest/version/hash comparison",
    "Netlify serves PWA shell/runtime delivery only",
    "destructive deletion requires explicit human approval"
]:
    if not any(frag in r for r in rules):
        fail.append("MISSING_ROUTING_RULE:"+frag)

if fail:
    print("FAIL: Drive storage map")
    for x in fail: print(x)
    raise SystemExit(1)
print("PASS: TAKY/HNS/SIEZEALL/SAVEY storage routing map")
