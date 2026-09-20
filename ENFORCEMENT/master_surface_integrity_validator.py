#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]

def fail(msg):
    print("FAIL:", msg)
    raise SystemExit(1)

def duplicate_section_ids(path):
    text=(ROOT/path).read_text(encoding="utf-8")
    ids=[]
    for line in text.splitlines():
        m=re.match(r"^##\s+([0-9]+(?:\.[0-9]+)?[A-Z]?)\b", line)
        if m: ids.append(m.group(1))
    return sorted({x for x in ids if ids.count(x)>1})

for path in [
    "MASTER/MASTER_LOGIC.md",
    "MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md",
    "MASTER/INTENT_EXECUTION_PROTOCOL.md",
    "MASTER/ENFORCEMENT_PROTOCOL.md",
    "MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md",
    "MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md",
]:
    dup=duplicate_section_ids(path)
    if dup:
        fail(f"{path}: duplicate active section ids {dup}")

profile=(ROOT/"PROJECTIONS/ACTIVE_RULE_PROFILE.md").read_text(encoding="utf-8")
required=[
    "SOURCE_REPOSITORY: hns140412-glitch/TAKY",
    "C2S_COMPILE_CLOSED != REFLECTION_COMPLETE != IMPLEMENTED != CI_VERIFIED != RUNTIME_VERIFIED != DEPLOYED != DEVICE_VERIFIED",
    "NotebookLM is legacy/optional",
    "The separate `TAKY-WORK-OS` repository is subordinate implementation/operating code",
]
for token in required:
    if token not in profile:
        fail(f"ACTIVE_RULE_PROFILE missing required current-truth token: {token}")

m=re.search(r"^SOURCE_CANONICAL_HEAD:\s*([0-9a-f]{40})\s*$", profile, re.M)
if not m:
    fail("ACTIVE_RULE_PROFILE missing valid SOURCE_CANONICAL_HEAD")
source=m.group(1)
try:
    subprocess.run(["git","cat-file","-e",f"{source}^commit"],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["git","merge-base","--is-ancestor",source,"HEAD"],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    fail("ACTIVE_RULE_PROFILE source canonical head is not a recoverable ancestor of HEAD")

print("PASS: master structural integrity and active-rule projection")
