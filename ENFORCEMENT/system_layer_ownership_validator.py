#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "MASTER" / "SYSTEM_LAYER_OWNERSHIP_MAP.json"
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
for gid in ("LAYER-GAP-001","LAYER-GAP-002","LAYER-GAP-003","LAYER-GAP-004","LAYER-GAP-005","LAYER-GAP-006","LAYER-GAP-007"):
    if gid not in findings:
        fail.append("MISSING_REVIEW_FINDING:" + gid)

invariants=" ".join(str(x) for x in data.get("invariants") or [])
for token in ("ROLE != AGENT","OWNER != ROUTER","TOOL != AUTHORITY","SAVEY_AI_ECONOMY != SAVEY_FAMILY_FINANCE"):
    if token not in invariants:
        fail.append("MISSING_INVARIANT:" + token)

# Cross-cutting planes are pointers to owners; they must not grow into semantic owners.
planes=data.get("cross_cutting_planes")
if not isinstance(planes,dict):
    if planes is not None:
        fail.append("PLANES_MALFORMED")
    planes={}
for plane in ("BETA_EVIDENCE","ALPHA_SEMANTIC_MAP","TAKY2_ENFORCEMENT_KERNEL","SHEPHERDING_CONTROL_PLANE"):
    p=planes.get(plane)
    if not isinstance(p,dict):
        fail.append(("MISSING_PLANE:" if p is None else "PLANE_MALFORMED:") + plane)
        continue
    if not str(p.get("authority_ref","")).strip():
        fail.append("PLANE_AUTHORITY_REF_MISSING:" + plane)
    if "owns" in p:
        fail.append("PLANE_CLAIMS_SEMANTIC_OWNERSHIP:" + plane)
# Plane refs must point at the active Drive-restored V2 numbering (§1-§10), not the older local numbering.
V2_DOC="TAKY2/TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL_20261006.md"
EXPECTED_PLANE_REFS={
    "BETA_EVIDENCE":{"authority_ref":"#2"},
    "ALPHA_SEMANTIC_MAP":{"authority_ref":"#2"},
    "TAKY2_ENFORCEMENT_KERNEL":{"authority_ref":"#2","gate_ref":"#6"},
    "SHEPHERDING_CONTROL_PLANE":{"authority_ref":"#3","control_roles_ref":"#4"},
}
for plane,refs in EXPECTED_PLANE_REFS.items():
    p=planes.get(plane)
    if not isinstance(p,dict):
        continue
    for field,anchor in refs.items():
        if p.get(field) != V2_DOC + anchor:
            fail.append("PLANE_V2_REF_STALE:" + plane + "." + field)
# Malformed (non-dict) planes are already reported above; treat them as empty so checks fail structurally.
def plane_obj(name):
    p=planes.get(name)
    return p if isinstance(p,dict) else {}
if not str(plane_obj("BETA_EVIDENCE").get("semantic_owner","")).startswith("NONE"):
    fail.append("BETA_PLANE_CLAIMS_SEMANTIC_OWNER")
kernel=plane_obj("TAKY2_ENFORCEMENT_KERNEL")
if kernel.get("hard_gates") != ["KEY","CONTEXT","ROUTE","COST","DONE"]:
    fail.append("HARD_GATES_NOT_EXACTLY_FIVE")
if kernel.get("necessity_location") != "COST":
    fail.append("NECESSITY_NOT_INSIDE_COST")
shepherd=plane_obj("SHEPHERDING_CONTROL_PLANE")
if shepherd.get("parent") != "TAKY_CORE":
    fail.append("SHEPHERDING_NOT_SUBORDINATE_TO_TAKY_CORE")
# Canonical exact list: duplicate, extra, missing or reordered roles all fail.
if shepherd.get("control_roles") != ["NAVIGATOR","GUARDIAN","DRIVER+SAVEY_AI_ECONOMY","SCOUT"]:
    fail.append("CONTROL_ROLES_INVALID")
if shepherd.get("role_is_agent") is not False or shepherd.get("mandatory_agent_spawn") is not False:
    fail.append("CONTROL_ROLE_BOUND_TO_AGENT")

# Whole-system systems (owner coverage inherited from MASTER §1.2 / Alpha integration) must be a registered layer or an explicit OWNER_GAP, never silently absent.
# A system promoted out of owner_gaps must carry verifiable authority_ref + semantic_owner_ref pointers;
# presence of a layer key alone is not registration. Ordinary layers keep their existing schema.
# A local ref must exist. A cross-repo owner/repo:path ref cannot be checked here, so it is accepted only
# with a local owner_verification_ref (existing .md/.json receipt). That ref is proof-of-verification
# metadata, never the semantic owner.
PLACEHOLDERS=("UNKNOWN","UNRESOLVED","FIXTURE","TODO","TBD","OWNER_GAP","PLACEHOLDER","NONE")
# repo-relative path (must exist) or owner/repo:path (cross-repo contract), .md/.json, optional #anchor
REF_RE=re.compile(r"^(?:(?P<repo>[\w.-]+/[\w.-]+):)?(?P<path>[\w.-]+(?:/[\w.-]+)*\.(?:md|json))(?:#[\w.-]+)?$")

def ref_error(value):
    """Return (error, is_cross_repo)."""
    value=str(value or "").strip()
    if not value:
        return "MISSING",False
    if any(p in value.upper() for p in PLACEHOLDERS):
        return "PLACEHOLDER",False
    m=REF_RE.match(value)
    if not m:
        return "INVALID_FORMAT",False
    if m.group("repo"):
        return None,True
    if not (ROOT / m.group("path")).is_file():
        return "NOT_FOUND",False
    return None,False

gap_entries=[x for x in data.get("owner_gaps") or [] if isinstance(x,dict)]
gaps={x.get("system"):x for x in gap_entries}
# Dict collapse would hide a repeated system; reject duplicates explicitly.
gap_systems=[x.get("system") for x in gap_entries]
for system in sorted({str(s) for s in gap_systems if gap_systems.count(s) > 1}):
    fail.append("OWNER_GAP_DUPLICATE:" + system)
for system in ("SAVEY_FAMILY_FINANCE","TAKY_MOBILE","PLANNER","PIANO_PRACTICE","EXPLORER_CREW","BADGE_REWARD","EUNHA_FARM"):
    if system in layers and system in gaps:
        fail.append("WHOLE_SYSTEM_OWNER_CONFLICT:" + system)
    elif system in layers:
        layer=layers.get(system) if isinstance(layers.get(system),dict) else {}
        verified=None
        if "owner_verification_ref" in layer:
            err,cross=ref_error(layer.get("owner_verification_ref"))
            if not err and cross:
                err="NOT_LOCAL"
            if err:
                fail.append("WHOLE_SYSTEM_LAYER_OWNER_VERIFICATION_REF_" + err + ":" + system)
            verified=not err
        for field in ("authority_ref","semantic_owner_ref"):
            err,cross=ref_error(layer.get(field))
            if err:
                fail.append("WHOLE_SYSTEM_LAYER_" + field.upper() + "_" + err + ":" + system)
            elif cross and not verified:
                fail.append("WHOLE_SYSTEM_LAYER_" + field.upper() + "_CROSS_REPO_UNVERIFIED:" + system)
    elif system not in gaps:
        fail.append("WHOLE_SYSTEM_OWNER_UNREGISTERED:" + system)
for system,gap in gaps.items():
    if gap.get("state") != "OWNER_GAP":
        fail.append("OWNER_GAP_STATE_INVALID:" + str(system))
    if not str(gap.get("authority_ref","")).strip():
        fail.append("OWNER_GAP_AUTHORITY_REF_MISSING:" + str(system))
    # Active V2 registers no owners for these systems; gap authority is MASTER §1.2, not V2 provenance.
    if str(gap.get("authority_ref","")).startswith(V2_DOC):
        fail.append("OWNER_GAP_AUTHORITY_MISATTRIBUTED_TO_V2:" + str(system))
    if any(k in gap for k in ("owns","owner","semantic_owner","semantic_owner_ref")):
        fail.append("OWNER_GAP_GUESSES_OWNERSHIP:" + str(system))

if fail:
    print("FAIL: system layer ownership map")
    for x in fail:
        print(x)
    raise SystemExit(1)

print("PASS: TAKY/Work/Learning/shared/family/project ownership boundaries are explicit and identity/authority sharing fails closed")
