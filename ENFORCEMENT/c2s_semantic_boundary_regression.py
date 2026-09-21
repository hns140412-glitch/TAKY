#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

failures = []

def require(path: str, needle: str):
    text = read(path)
    if needle not in text:
        failures.append(f"MISSING:{path}:{needle}")

def forbid(path: str, needle: str):
    text = read(path)
    if needle in text:
        failures.append(f"STALE:{path}:{needle}")

# C2S semantic core sentinels: detect accidental meaning loss, not exact-file immutability.
protocol = "MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md"
for needle in (
    "Conversation is not disposable narration.",
    "The system layer SHALL NOT replace the evidence layer.",
    "A material recovered atom SHALL NOT disappear",
    "TAKY SHALL NOT merge distinct ideas merely to make the model/document simpler.",
    "A user correction is not a note attached to the latest answer. It is a graph mutation.",
    "UNMAPPED_MATERIAL = 0",
    "SILENT_LOSS = 0",
    "STRUCTURAL PASS != SEMANTIC RECONSTRUCTION PASS",
    "C2S_COMPILE_CLOSED != REFLECTION_COMPLETE",
    "C2S closure is a knowledge-compilation state",
):
    require(protocol, needle)

# Highest-level and boot surfaces must expose the same boundary.
boundary = "C2S_COMPILE_CLOSED != REFLECTION_COMPLETE != IMPLEMENTED != CI_VERIFIED != RUNTIME_VERIFIED != DEPLOYED != DEVICE_VERIFIED"
require("MASTER/MASTER_LOGIC.md", boundary)
require("TAKY.md", boundary)

# Current command/state surfaces must not reintroduce superseded coupling or NotebookLM default routing.
forbid("OS/COMMAND_INTERACTION.md", "coverage/reflect/history stop condition")
forbid("OS/COMMAND_INTERACTION.md", "targeted L2 NotebookLM/index")
require("OS/COMMAND_INTERACTION.md", "targeted L2 Drive/source-registry/index recovery")
require("OS/COMMAND_INTERACTION.md", "continue through its C2S compile stop condition")

forbid("STATE.md", "NotebookLM recovery pipeline: `DRIVE_WORKSPACE_IMPLEMENTED + CANONICAL_PROTOCOL_IMPLEMENTED + CI_ENFORCED`")
require("STATE.md", "NotebookLM legacy recovery: `INACTIVE_DEFAULT / LEGACY_REFERENCE_ONLY`")

# Context Ledger major section numbering must be unique and strictly increasing.
ledger_text = read("MASTER/CONVERSATION_CONTEXT_LEDGER_PROTOCOL.md")
major_numbers = []
for line in ledger_text.splitlines():
    m = re.match(r"^## (\d+)\. (?!\d)", line)
    if m:
        major_numbers.append(int(m.group(1)))
if len(major_numbers) != len(set(major_numbers)):
    failures.append(f"DUPLICATE_MAJOR_SECTION:MASTER/CONVERSATION_CONTEXT_LEDGER_PROTOCOL.md:{major_numbers}")
if any(b <= a for a, b in zip(major_numbers, major_numbers[1:])):
    failures.append(f"NON_MONOTONIC_MAJOR_SECTION:MASTER/CONVERSATION_CONTEXT_LEDGER_PROTOCOL.md:{major_numbers}")



# Realization closure: central owner pointers and growth states must track current implementation truth.
family_master = read("MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md")
if "Ready_Set_Ui_Master_Logic_REV_07.md" in family_master:
    failures.append("STALE:MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md:Ready legacy owner pointer")
if "READY_SET_CANONICAL_PRODUCT_CONTRACT.md" not in family_master:
    failures.append("MISSING:MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md:Ready current canonical pointer")

import json
growth = json.loads(read("MASTER/LEARNING_APP_FAMILY_GROWTH_BACKLOG.json"))
growth_by_id = {x.get("gap_id"): x for x in growth.get("items", [])}
for gap_id in (
    "GROWTH-PWA-UPDATE-001",
    "GROWTH-VERSION-TUPLE-001",
    "GROWTH-STATE-EVENT-001",
    "GROWTH-EXTERNAL-BUDGET-001",
):
    row = growth_by_id.get(gap_id)
    if not row:
        failures.append(f"MISSING_GROWTH_ITEM:{gap_id}")
    elif row.get("state") == "OPEN":
        failures.append(f"STALE_GROWTH_STATE:{gap_id}:OPEN_AFTER_IMPLEMENTATION")

for gap_id in ("GROWTH-STATE-EVENT-001", "GROWTH-LOCALFIRST-CONFLICT-001"):
    owner = str((growth_by_id.get(gap_id) or {}).get("owner_destination", ""))
    if "Shared learning data" in owner or "Shared learning event/data contract" in owner:
        failures.append(f"AMBIGUOUS_SHARED_SEMANTIC_OWNER:{gap_id}")

if failures:
    print("FAIL: C2S semantic boundary regression")
    for item in failures:
        print(item)
    raise SystemExit(1)

print("PASS: C2S semantic core preserved; stale coupling/routing absent; section structure valid")
