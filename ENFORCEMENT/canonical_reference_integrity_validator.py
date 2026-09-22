#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_FILES = [
    ROOT / "TAKY.md",
    ROOT / "STATE.md",
    ROOT / "MASTER" / "MASTER_LOGIC.md",
    ROOT / "MASTER" / "MASTER_FILE_REGISTRY.json",
    ROOT / "MASTER" / "LEARNING_APP_FAMILY_MASTER_REV_01.md",
    ROOT / "MASTER" / "SYSTEM_LAYER_OWNERSHIP_MAP.json",
    ROOT / "OS" / "WORK_OS.md",
    ROOT / "OS" / "GUIDE_FAMILY_LEARNING_OS.md",
]
fail=[]

def rel(p:Path)->str:
    return str(p.relative_to(ROOT)).replace("\\","/")

# 1. Referenced local canonical/support paths must resolve when written as repository paths.
ref_re = re.compile(r"(?<![A-Za-z0-9_.-])((?:MASTER|OS|DOMAIN|PROJECTS|ENFORCEMENT|PROJECTIONS|HANDOFF|C2S|SHARED)/[A-Za-z0-9_./-]+\.(?:md|json|py|js|yml|yaml))")
for p in ACTIVE_FILES:
    if not p.exists():
        fail.append(f"ACTIVE_FILE_MISSING:{rel(p)}")
        continue
    s=p.read_text(encoding="utf-8",errors="ignore")
    for m in ref_re.finditer(s):
        ref=m.group(1).rstrip(".,;:)]}")
        if not (ROOT/ref).exists():
            fail.append(f"BROKEN_LOCAL_REF:{rel(p)}->{ref}")

# 2. MASTER registry paths must exist.
reg_path=ROOT/"MASTER"/"MASTER_FILE_REGISTRY.json"
if reg_path.exists():
    reg=json.loads(reg_path.read_text(encoding="utf-8"))
    for path,meta in (reg.get("files") or {}).items():
        if not (ROOT/path).exists():
            fail.append(f"MASTER_REGISTRY_PATH_MISSING:{path}")
        if not isinstance(meta,dict) or not meta.get("class"):
            fail.append(f"MASTER_REGISTRY_CLASS_MISSING:{path}")

# 3. Known filename/header lineage mismatch must be explicit, not accidental.
family=ROOT/"MASTER"/"LEARNING_APP_FAMILY_MASTER_REV_01.md"
if family.exists():
    s=family.read_text(encoding="utf-8",errors="ignore")
    if "REV_01" in family.name and "Historical filename REV_01 is a lineage identifier" not in s:
        fail.append("FAMILY_MASTER_REV_FILENAME_HEADER_MISMATCH_UNEXPLAINED")
    if not re.search(r"^#\s+Learning App Family Master",s,re.M):
        fail.append("FAMILY_MASTER_HEADER_INVALID")

# 4. STATE must not present dated implementation snapshots as timeless runtime truth.
state=ROOT/"STATE.md"
if state.exists():
    s=state.read_text(encoding="utf-8",errors="ignore")
    dated_blocks=re.findall(r"^##\s+.*?\b20\d{2}-\d{2}-\d{2}\b",s,re.M)
    if dated_blocks and "historical snapshot" not in s.lower() and "snapshot" not in s.lower():
        fail.append("STATE_DATED_SNAPSHOT_CLASSIFICATION_MISSING")

# 5. Active boot/current surfaces must not directly hardwire known superseded architecture identities.
boot=(ROOT/"TAKY.md").read_text(encoding="utf-8",errors="ignore")
for token in ["OS/GUIDE_FAMILY_LEARNING_OS.md","OS/GUIDE_CHARACTER_RELATIONSHIP.md"]:
    if token in boot and "legacy" not in boot.lower():
        fail.append(f"BOOT_LEGACY_OWNER_POINTER_REVIEW_REQUIRED:{token}")

# 6. Ownership map current nodes must reference existing local semantic owner files when owner is a repo path.
omap_path=ROOT/"MASTER"/"SYSTEM_LAYER_OWNERSHIP_MAP.json"
if omap_path.exists():
    omap=json.loads(omap_path.read_text(encoding="utf-8"))
    for name,node in (omap.get("layers") or {}).items():
        owner=(node or {}).get("semantic_owner")
        if isinstance(owner,str) and "/" in owner and ":" not in owner and owner.endswith((".md",".json")):
            if not (ROOT/owner).exists():
                fail.append(f"OWNER_POINTER_MISSING:{name}->{owner}")

if fail:
    print("FAIL: canonical reference/header integrity")
    for x in sorted(set(fail)):
        print(x)
    raise SystemExit(1)

print("PASS: active canonical/reference paths, registry entries, owner pointers and known header-lineage contracts are structurally resolvable")
