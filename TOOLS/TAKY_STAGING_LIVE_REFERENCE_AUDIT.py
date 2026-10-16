"""Bounded cross-repo staging reference audit; no relocation, no content copying.

Conservatively classifies unclear files as HOLD rather than claiming unused.
"""
from pathlib import Path
import json,collections
R=Path("D:/Git PWA");T=R/"TAKY";V=R/"TAKY-SOURCE-VAULT";W=R/"TAKY_AI_WORKBENCH"
STAGING=T/"staging"
OUT=W/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_STAGING_LIVE_REFERENCES_20261013.json"
FOCUS=[T/"TOOLS",T/"ENFORCEMENT",T/"LEARNING",T/"CURRENT",T/"OS",
 V, R/"Ready & Set",R/"Hide & Seek",R/"Snap & Pop",R/"Play Camp"/"src",
 R/"TAKY-MOBILE"/"src",R/"SAVEY"/"src"]
SUFFIX={".py",".ps1",".js",".cjs",".mjs",".ts",".tsx",".json",".cmd",".bat",".vbs"}
SKIP={"node_modules",".git",".local","backup","reports","logs","vendor","data","assets","staging","dist","build","coverage",".cache"}
CAP=1_200_000
def collect():
 files=[];count=0
 for root in FOCUS:
  if not root.is_dir():continue
  # depth-first but skip deeply nested raw & generated trees.
  import os
  for base,dirs,names in os.walk(root):
   dirs[:]=[x for x in dirs if x not in SKIP and not x.startswith("__pycache__")]
   for n in names:
    f=Path(base)/n
    if f.suffix.lower() not in SUFFIX:continue
    try:
     if f.stat().st_size>CAP:continue
    except OSError:continue
    files.append(f)
    if len(files)>=6000:break
   if len(files)>=6000:break
  if len(files)>=6000:break
 return files,len(files)>=6000
def main():
 base=[x for x in STAGING.iterdir() if x.is_file()]
 names=[x.name for x in base]
 matches={n:[] for n in names};files,truncated=collect()
 for f in files:
  try:data=f.read_text(encoding="utf-8-sig",errors="replace")
  except OSError:continue
  for name in names:
   if name in data:
    matches[name].append(str(f))
 report={"schema":"TAKY_STAGING_BOUND_CONSUMER_AUDIT_V1",
  "scanned_code_files":len(files),"scan_truncated":truncated,
  "root_file_count":len(base),"staging_files":[{
   "name":f.name,"size":f.stat().st_size,
   "bounded_consumers":matches[f.name],
   "decision":"HOLD_PENDING_FULL_HISTORY_AND_ACTIVE_CONSUMER_REBIND"
  } for f in base],
  "move_applied":False,
  "reason":"Static code scan cannot prove no dynamic/archived references; preserve immutable references."}
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"CLASSIFIED_NOT_MOVED",
  "root_files":len(base),"bounded_scan_files":len(files),"truncated":truncated,
  "with_code_references":sum(bool(v) for v in matches.values()),
  "without_code_references":sum(not v for v in matches.values()),
  "evidence":str(OUT)},ensure_ascii=False))
if __name__=="__main__":main()
