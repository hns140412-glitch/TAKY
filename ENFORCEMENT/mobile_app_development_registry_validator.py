#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"OS"/"MOBILE_APP_DEVELOPMENT_REGISTRY.json"
d=json.loads(p.read_text(encoding="utf-8"))
fail=[]

fresh=d.get("freshness_policy") or {}
if fresh.get("class")!="VOLATILE_OPERATIONAL_SNAPSHOT":
    fail.append("FRESHNESS_CLASS_INVALID")
if fresh.get("current_state_claim_requires_live_refresh") is not True:
    fail.append("LIVE_REFRESH_GATE_MISSING")
if not isinstance(fresh.get("refresh_triggers"),list) or not fresh.get("refresh_triggers"):
    fail.append("FRESHNESS_TRIGGER_MISSING")


apps=d.get("apps") or {}
required={"READY_SET","SNAP_POP","HIDE_SEEK","SHARED_ASSETS","MOBILE_CATALOG"}
if set(apps)!=required:
    fail.append("APP_SET_INVALID:"+",".join(sorted(apps)))

for key in ("READY_SET","SNAP_POP","HIDE_SEEK"):
    app=apps.get(key,{})
    gh=app.get("github") or {}
    if gh.get("state")!="SOURCE_CURRENT":
        fail.append(f"SOURCE_CURRENT_MISSING:{key}")
    if not gh.get("repo") or not gh.get("main_head"):
        fail.append(f"GITHUB_IDENTITY_INCOMPLETE:{key}")
    if not str(gh.get("head_evidence_state","")).startswith("LIVE_REFRESHED_"):
        fail.append(f"GITHUB_HEAD_FRESHNESS_MISSING:{key}")
    drv=app.get("drive") or {}
    if not drv.get("id") or drv.get("parent_role")!="10_PROJECTS":
        fail.append(f"DRIVE_PROJECT_ROUTE_INVALID:{key}")

# Exact current deploy claims must be proven by SHA equality.
for key,app in apps.items():
    main=(app.get("github") or {}).get("main_head")
    for dep in app.get("netlify") or []:
        rel=dep.get("relation_to_current_main")
        dsha=dep.get("deployed_commit")
        if rel=="EXACT_SHA_MATCH" and (not main or dsha!=main):
            fail.append(f"FALSE_EXACT_SHA_MATCH:{key}:{dep.get('site_id')}")
        if rel=="DEPLOYED_STALE" and main and dsha==main:
            fail.append(f"FALSE_STALE_CLASSIFICATION:{key}:{dep.get('site_id')}")
        if dep.get("provenance")=="PROVENANCE_UNKNOWN_UPLOAD" and dsha:
            fail.append(f"UNKNOWN_PROVENANCE_HAS_ASSERTED_SHA:{key}:{dep.get('site_id')}")

# Validation-only PRs must not be presented as merge candidates.
for key,app in apps.items():
    for pr in app.get("open_prs") or []:
        cls=pr.get("classification","")
        if cls=="VALIDATION_ONLY" and "merge" in str(pr.get("note","")).lower() and "no merge" not in str(pr.get("note","")).lower() and "do not merge" not in str(pr.get("note","")).lower():
            fail.append(f"AMBIGUOUS_VALIDATION_PR:{key}:{pr.get('number')}")

inv=d.get("invariants") or []
for req in (
    "GITHUB_MAIN != DEPLOYED unless exact deploy provenance proves the same commit.",
    "VALIDATION_ONLY_PR != MERGE_CANDIDATE.",
    "CODED != CI_VERIFIED != RUNTIME_VERIFIED != DEPLOYED != DEVICE_VERIFIED.",
    "REGISTRY_SNAPSHOT != LIVE_CURRENT_STATE; refresh volatile GitHub/deploy claims when material."
):
    if req not in inv:
        fail.append("MISSING_INVARIANT:"+req)

if fail:
    print("FAIL: mobile app development registry")
    for x in fail: print(x)
    raise SystemExit(1)
print("PASS: mobile app source/work/validation/deploy/legacy surfaces are explicitly separated")
