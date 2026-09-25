#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "MASTER" / "SYSTEM_LAYER_OWNERSHIP_MAP.json"
data = json.loads(PATH.read_text(encoding="utf-8"))
fail = []

layers = data.get("layers") or {}
required_layers = {
    "TAKY_CORE","SHARED_TECHNICAL_CAPABILITY","WORK_OS","LEARNING_OS",
    "LEARNING_ENGINE_CORE","LEARNING_APP_FAMILY","READY_SET","HIDE_SEEK","SNAP_POP",
    "WORK_DOMAIN_PROJECT","PLATFORM_ADAPTER"
}
if not required_layers.issubset(layers):
    fail.append("MISSING_LAYERS:" + ",".join(sorted(required_layers - set(layers))))

if (layers.get("WORK_OS") or {}).get("parent") != "TAKY_CORE":
    fail.append("WORK_OS_PARENT_INVALID")
if (layers.get("LEARNING_OS") or {}).get("parent") != "TAKY_CORE":
    fail.append("LEARNING_OS_PARENT_INVALID")
if "LEARNING_OS" not in ((layers.get("WORK_OS") or {}).get("sibling_of") or []):
    fail.append("WORK_LEARNING_SIBLING_LINK_MISSING")
if "WORK_OS" not in ((layers.get("LEARNING_OS") or {}).get("sibling_of") or []):
    fail.append("LEARNING_WORK_SIBLING_LINK_MISSING")
if (layers.get("LEARNING_ENGINE_CORE") or {}).get("parent") != "LEARNING_OS":
    fail.append("LEARNING_ENGINE_CORE_PARENT_INVALID")
engine=layers.get("LEARNING_ENGINE_CORE") or {}
for forbidden in ("dated scheduling or calendar placement","Ready session runtime","specialist app UI/interaction"):
    if forbidden not in (engine.get("does_not_own") or []):
        fail.append("LEARNING_ENGINE_CORE_BOUNDARY_MISSING:" + forbidden)
if (layers.get("LEARNING_APP_FAMILY") or {}).get("parent") != "LEARNING_OS":
    fail.append("LEARNING_APP_FAMILY_PARENT_INVALID")

for app in ("READY_SET","HIDE_SEEK","SNAP_POP"):
    if (layers.get(app) or {}).get("parent") != "LEARNING_APP_FAMILY":
        fail.append(f"APP_PARENT_INVALID:{app}")
    inherits=set((layers.get(app) or {}).get("must_inherit") or [])
    if not {"TAKY_CORE","LEARNING_OS","LEARNING_APP_FAMILY"}.issubset(inherits):
        fail.append(f"APP_INHERITANCE_INCOMPLETE:{app}")

shared=layers.get("SHARED_TECHNICAL_CAPABILITY") or {}
if shared.get("class") != "SEMANTIC_LIGHT_SHARED_MECHANISM":
    fail.append("SHARED_LAYER_NOT_SEMANTIC_LIGHT")
for forbidden in (
    "organization identity/role/permission",
    "family/child/parent identity/role/permission",
    "cross-domain authority",
):
    if forbidden not in (shared.get("forbidden_implicit_ownership") or []):
        fail.append("MISSING_SHARED_FORBIDDEN:" + forbidden)

classes=data.get("capability_classification") or []
by_item={x.get("item"):x for x in classes if isinstance(x,dict)}

required_exact={
    "organization identity, membership, roles, permissions":("DOMAIN_OWNED_SEMANTIC","WORK_OS"),
    "family/child/parent identity, relationships, roles, permissions":("DOMAIN_OWNED_SEMANTIC","LEARNING_OS"),
    "same-human link across Work and Learning":("EXPLICIT_FEDERATION","NO_ACTIVE_CONTRACT"),
    "cross-app learning handoff/session semantics":("DOMAIN_OWNED_SEMANTIC","LEARNING_APP_FAMILY"),
    "Work scheduling/task semantics":("DOMAIN_OWNED_SEMANTIC","WORK_OS"),
    "Learning schedule/planner/assignment semantics":("DOMAIN_OWNED_SEMANTIC","LEARNING_OS"),
    "learner modeling and pedagogical adaptation semantics":("DOMAIN_OWNED_SEMANTIC","LEARNING_ENGINE_CORE"),
}
for item,(cls,owner) in required_exact.items():
    x=by_item.get(item)
    if not x:
        fail.append("MISSING_CLASSIFICATION:" + item)
        continue
    if x.get("class") != cls or x.get("owner") != owner:
        fail.append("WRONG_CLASSIFICATION:" + item)

federation=by_item.get("same-human link across Work and Learning") or {}
if federation.get("state") != "HOLD_UNTIL_REAL_USE_CASE":
    fail.append("CROSS_DOMAIN_FEDERATION_NOT_FAIL_CLOSED")

for rel in data.get("cross_layer_rules") or []:
    if {rel.get("from"),rel.get("to")} == {"WORK_OS","LEARNING_OS"}:
        if "direct" not in str(rel.get("forbidden","")).lower():
            fail.append("WORK_LEARNING_DIRECT_INHERITANCE_NOT_FORBIDDEN")

findings={x.get("gap_id"):x for x in data.get("review_findings") or [] if isinstance(x,dict)}
for gid in ("LAYER-GAP-001","LAYER-GAP-002","LAYER-GAP-003","LAYER-GAP-004","LAYER-GAP-005","LAYER-GAP-006"):
    if gid not in findings:
        fail.append("MISSING_REVIEW_FINDING:" + gid)

if fail:
    print("FAIL: system layer ownership map")
    for x in fail:
        print(x)
    raise SystemExit(1)

print("PASS: TAKY/Work/Learning/shared/family/project ownership boundaries are explicit and identity/authority sharing fails closed")
