#!/usr/bin/env python3
import json, sys
from pathlib import Path

ORDER={"L0":0,"L1":1,"L2":2,"L3":3,"L4":4}

def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)

def main(path):
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    required=["record_id","intent","selected_level","levels_attempted","asked_user_to_repeat","recoverable_path_remaining","full_scan_explicit","stop_reason"]
    for k in required:
        if k not in d: fail(f"missing {k}")

    sel=d["selected_level"]
    attempted=d["levels_attempted"]
    if sel not in attempted:
        fail("selected_level must be in levels_attempted")

    if d.get("asked_user_to_repeat") and d.get("recoverable_path_remaining"):
        fail("ASK_LAST violation: user asked to repeat while recoverable path remains")

    if sel=="L4" and not d.get("full_scan_explicit"):
        fail("FULL_SCAN_LAST violation: L4 requires explicit full/global reconstruction scope")

    if d.get("notebooklm_used") and d.get("l0_l1_sufficient"):
        fail("Context economy violation: NotebookLM used although L0/L1 was sufficient")

    if sel in {"L2","L3","L4"} and not d.get("escalation_reason"):
        fail(f"{sel} requires escalation_reason")

    if d.get("intent")=="CONTINUE" and sel=="L4":
        fail("ordinary continuation cannot select L4")

    if d.get("asked_user_to_repeat") and not d.get("user_is_only_source") and d.get("stop_reason")=="TRUE_UNAVAILABLE":
        fail("TRUE_UNAVAILABLE re-ask requires user_is_only_source or a different stop reason")

    print(f"PASS: {d['record_id']} intent={d['intent']} selected={sel}")

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: conversation_continuity_validator.py <record.json>")
        raise SystemExit(2)
    main(sys.argv[1])
