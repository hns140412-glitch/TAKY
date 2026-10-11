#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"OS"/"DRIVE_STORAGE_MAP.json"
d=json.loads(p.read_text(encoding="utf-8"))
fail=[]

auth=d.get("authority") or {}
if auth.get("github")!="CANONICAL_GOVERNANCE":
    fail.append("GITHUB_AUTHORITY_MISSING")
if auth.get("drive_is_canonical_governance") is not False:
    fail.append("DRIVE_CANONICAL_AUTHORITY_MUST_BE_FALSE")
if auth.get("netlify_is_asset_binding_authority") is not False:
    fail.append("NETLIFY_MUST_NOT_BIND_ASSETS")

ns=d.get("final_storage_namespace") or {}
if ns.get("state")!="LOCKED_CURRENT_GROUPED_PHYSICAL_LAYOUT":
    fail.append("FINAL_NAMESPACE_GROUPED_LOCK_MISSING")

expected_root_names=["00_CONTEXT","10_DOMAINS","20_PLATFORM","90_MAINTENANCE"]
expected_hns_root={
    "00_CONTEXT":"1Y3M3Zm4rrwUkloAiViHnWxDtsVN-gvMt",
    "10_DOMAINS":"1lpdO7FvybmgySrow18kaO0TcUkcgXyYn",
    "20_PLATFORM":"1UWklIxYYux6TgoLiD2xReNUz11o1Iz9o",
    "90_MAINTENANCE":"1ViC-lolcTTl69ySyHJsZmEp5G-P2Qtdf",
}
expected_sie_root={
    "00_CONTEXT":"1RAVFjE6HBnQnY42x8EmlRXr3nHi7tGu9",
    "10_DOMAINS":"1jXXTLynHb6-WtmaJy5j6-dD2JaXItWd-",
    "20_PLATFORM":"1B5fQ1KF-iYoVWQHV41_gNiTXVAmQKuI2",
    "90_MAINTENANCE":"1icDeX9cd17l5TcwXezy9wluIIBkBTUrW",
}
if ((ns.get("hns") or {}).get("root") or {}).get("id")!="1WjH-Q2tWFvVNCiBy9r-D9U72Ac7DH61d":
    fail.append("HNS_ROOT_ID_INVALID")
if ((ns.get("siezeall") or {}).get("root") or {}).get("id")!="1A9Mq171etYULKLgD4Wk1AHOFozW76Ulh":
    fail.append("SIEZEALL_ROOT_ID_INVALID")
if ((ns.get("hns") or {}).get("immediate_children") or {})!=expected_hns_root:
    fail.append("HNS_ROOT_GROUP_DRIFT")
if ((ns.get("siezeall") or {}).get("immediate_children") or {})!=expected_sie_root:
    fail.append("SIEZEALL_ROOT_GROUP_DRIFT")

layout=d.get("physical_presentation_layout") or {}
if layout.get("state")!="LOCKED":
    fail.append("PHYSICAL_LAYOUT_NOT_LOCKED")
if layout.get("root_groups")!=expected_root_names:
    fail.append("ROOT_GROUP_ORDER_OR_NAMES_DRIFT")

expected_hns_group_children={
    "00_CONTEXT":["TAKY_2.0_COLLAB"],
    "10_DOMAINS":["01_LEARNING","02_ARCHIGROW"],
    "20_PLATFORM":["03_COMMON","UI_SOURCE_AUTHORITY"],
    "90_MAINTENANCE":["AUDIT","20_REVIEWS_C2S","80_HANDOFF","90_ARCHIVE","90_TEMP","99_DELETE_PENDING"],
}
expected_sie_group_children={
    "00_CONTEXT":["TAKY_2.0_COLLAB","CLAUDE_REVIEW","05_CONTEXT_LEDGER"],
    "10_DOMAINS":["01_LEARNING_SHARE","02_ARCHIGROW_SHARE"],
    "20_PLATFORM":["03_UPDATES","04_USER_DATA"],
    "90_MAINTENANCE":["90_TEMP"],
}
for group,children in expected_hns_group_children.items():
    got=((((layout.get("hns") or {}).get("groups") or {}).get(group) or {}).get("children") or [])
    if got!=children:
        fail.append("HNS_GROUP_CHILDREN_DRIFT:"+group)
for group,children in expected_sie_group_children.items():
    got=((((layout.get("siezeall") or {}).get("groups") or {}).get(group) or {}).get("children") or [])
    if got!=children:
        fail.append("SIEZEALL_GROUP_CHILDREN_DRIFT:"+group)

expected_hns_leaf_ids={
    "01_LEARNING":"17_9ZFdN0vov8ZhC4g9cYnMakHC5u-OKr",
    "02_ARCHIGROW":"1Ji_DA74nRjRwwy5vUJYrkMtl9y-at0zr",
    "03_COMMON":"1UXAb5u1sraxvvIW0gHkPCS6Y-K3YMDnz",
    "90_TEMP":"1qCLjK20Wenh7TLrYHTWJsojSEiDpXuzi",
    "99_DELETE_PENDING":"1r9RmuhkJWL_mHcx-o3B17NnfKOgNgnXe",
}
expected_sie_leaf_ids={
    "01_LEARNING_SHARE":"1pgWTQS6Ondk6D3SYbJXGQ4y0COu0oleb",
    "02_ARCHIGROW_SHARE":"1hSkV9J_ycMdZChU1a2YEsApiRP8Oi2wa",
    "03_UPDATES":"111nmMqJvFfwKYoxaKBGmJWWMoqvCck0s",
    "04_USER_DATA":"1basjn1lv8YTyo0MMMRHBKCmRv5jWyqUf",
    "90_TEMP":"1xZ3a6bYt1uYyiUkctu_b8xrh2c6NFvtK",
}
leaf=(ns.get("logical_role_ids") or {})
if (leaf.get("hns") or {})!=expected_hns_leaf_ids:
    fail.append("HNS_LOGICAL_LEAF_ID_DRIFT")
if (leaf.get("siezeall") or {})!=expected_sie_leaf_ids:
    fail.append("SIEZEALL_LOGICAL_LEAF_ID_DRIFT")

paths=(ns.get("logical_role_paths") or {})
required_paths={
    ("hns","01_LEARNING"):"TAKY/10_DOMAINS/01_LEARNING",
    ("hns","02_ARCHIGROW"):"TAKY/10_DOMAINS/02_ARCHIGROW",
    ("hns","03_COMMON"):"TAKY/20_PLATFORM/03_COMMON",
    ("hns","UI_SOURCE_AUTHORITY"):"TAKY/20_PLATFORM/UI_SOURCE_AUTHORITY",
    ("hns","90_TEMP"):"TAKY/90_MAINTENANCE/90_TEMP",
    ("siezeall","01_LEARNING_SHARE"):"TAKY/10_DOMAINS/01_LEARNING_SHARE",
    ("siezeall","02_ARCHIGROW_SHARE"):"TAKY/10_DOMAINS/02_ARCHIGROW_SHARE",
    ("siezeall","03_UPDATES"):"TAKY/20_PLATFORM/03_UPDATES",
    ("siezeall","04_USER_DATA"):"TAKY/20_PLATFORM/04_USER_DATA",
    ("siezeall","90_TEMP"):"TAKY/90_MAINTENANCE/90_TEMP",
}
for (acct,key),expected in required_paths.items():
    got=((paths.get(acct) or {}).get(key))
    if got!=expected:
        fail.append(f"PHYSICAL_PATH_DRIFT:{acct}:{key}")

lock=d.get("structure_lock") or {}
if lock.get("state")!="LOCKED":
    fail.append("STRUCTURE_LOCK_MISSING")
if lock.get("context_must_be_top_level") is not True:
    fail.append("CONTEXT_TOP_LEVEL_LOCK_MISSING")
if lock.get("logical_leaf_ids_must_remain_stable") is not True:
    fail.append("LEAF_ID_STABILITY_LOCK_MISSING")
if lock.get("new_root_folder_creation")!="FORBIDDEN_UNLESS_USER_CHANGES_NAMESPACE":
    fail.append("ROOT_FOLDER_CREATION_GUARD_MISSING")
if lock.get("duplicate_role_folder_creation")!="FORBIDDEN":
    fail.append("DUPLICATE_ROLE_FOLDER_GUARD_MISSING")
if lock.get("temp_is_authority") is not False:
    fail.append("TEMP_MUST_NOT_BE_AUTHORITY")

roles=d.get("account_roles") or {}
hns=roles.get("HNS") or {}
sie=roles.get("SIEZEALL") or {}
if hns.get("user_direct_access") is not False:
    fail.append("HNS_USER_DIRECT_ACCESS_MUST_BE_FALSE")
if sie.get("cloud_project_oauth_api_owner") is not True:
    fail.append("SIEZEALL_CLOUD_OWNER_MISSING")
inbox=sie.get("canonical_user_reference_inbox") or {}
expected_inbox_id="1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB"
if inbox.get("cloud_folder_id")!=expected_inbox_id:
    fail.append("SINGLE_USER_INBOX_CLOUD_ID_DRIFT")
if inbox.get("ingress_mode")!="GOOGLE_DRIVE_FOLDER_ID_PRIMARY":
    fail.append("SINGLE_USER_INBOX_REMOTE_PRIMARY_MODE_MISSING")
if inbox.get("remote_ingress_state")!="CONNECTED_VERIFIED":
    fail.append("SINGLE_USER_INBOX_REMOTE_INGRESS_NOT_VERIFIED")
sync_state=inbox.get("local_sync_state")
local_path=inbox.get("local_synced_path")
if sync_state=="OPTIONAL_MIRROR_UNBOUND":
    if local_path is not None:
        fail.append("SINGLE_USER_INBOX_OPTIONAL_MIRROR_PATH_MUST_BE_NULL")
elif sync_state=="BOUND":
    if not isinstance(local_path,str) or not local_path.strip():
        fail.append("SINGLE_USER_INBOX_BOUND_PATH_MISSING")
else:
    fail.append("SINGLE_USER_INBOX_SYNC_STATE_INVALID")
if inbox.get("collector_watch") is not True:
    fail.append("SINGLE_USER_INBOX_WATCH_MISSING")

asset=d.get("asset_delivery") or {}
if asset.get("binary_master")!="HNS_DRIVE_APPROVED_ASSET_MASTER":
    fail.append("ASSET_MASTER_ROUTE_DRIFT")
if asset.get("distribution")!="SIEZEALL_DRIVE_APPROVED_PACKAGE":
    fail.append("ASSET_DISTRIBUTION_ROUTE_DRIFT")
if asset.get("runtime")!="DEVICE_VERIFIED_CACHE":
    fail.append("ASSET_RUNTIME_ROUTE_DRIFT")

rules=d.get("routing_rules") or []
for frag in [
    "TAKY root exposes only 00_CONTEXT, 10_DOMAINS, 20_PLATFORM and 90_MAINTENANCE",
    "00_CONTEXT stays directly under TAKY root",
    "Current physical paths are read from final_storage_namespace.logical_role_paths",
    "Netlify delivers PWA shell/runtime only",
    "Do not create multiple user inboxes",
]:
    if not any(frag in x for x in rules):
        fail.append("MISSING_ROUTING_RULE:"+frag)

if fail:
    print("FAIL: Drive storage map")
    for x in fail: print(x)
    raise SystemExit(1)
print("PASS: grouped TAKY root, top-level CONTEXT, stable leaf IDs, current physical paths, single SIEZEALL inbox and asset/Netlify boundaries are locked")
