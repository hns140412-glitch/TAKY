#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
scan_roots=[ROOT/"MASTER",ROOT/"OS"]
extra=[ROOT/"TAKY.md",ROOT/"STATE.md"]
fail=[]

def check_file(p: Path):
    if not p.is_file(): return
    if p.suffix.lower() not in {".md",".json",".py",".yml",".yaml",".txt"}: return
    s=p.read_text(encoding="utf-8",errors="ignore")
    if re.search(r"zpd",s,re.I):
        fail.append(str(p.relative_to(ROOT)))

for root in scan_roots:
    for p in root.rglob("*"):
        check_file(p)
for p in extra:
    check_file(p)

if fail:
    print("FAIL: superseded product identity present in current TAKY surfaces")
    for x in fail: print(x)
    raise SystemExit(1)
print("PASS: current TAKY MASTER/OS/boot/state surfaces contain only current Hide & Seek identity")
