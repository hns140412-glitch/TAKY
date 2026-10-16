"""Archive only the seven verified legacy .bak scripts, preserving active entrypoints.
No running code, RAW, or live scheduled task is moved."""
from pathlib import Path
import argparse,hashlib,json,os
ROOT=Path(r"D:/Git PWA/TAKY-SOURCE-VAULT")
TARGET=ROOT/"backup"/"SCRIPT_REVISION_ARCHIVE_20261013"
EVIDENCE=Path(r"D:/Git PWA/TAKY_AI_WORKBENCH/01_BACKLOG_AND_ADOPTION/80_EVIDENCE/STAGE3_LEGACY_SCRIPT_BACKUPS_20261013.json")
NAMES=(
 "RUN_NOTION_INCREMENTAL_SCHEDULED.ps1.20261002_224405.bak",
 "RUN_TAKY_POST_COLLECT_PIPELINE.ps1.20261004_delta_only.bak",
 "RUN_TAKY_POST_COLLECT_PIPELINE.ps1.20261007_pre_haiku.bak",
 "START_INCREMENTAL.bat.20261002_224405.bak",
 "TAKY_INCREMENTAL.js.20261002_223926.pre_safety_patch.bak",
 "TAKY_INCREMENTAL.js.20261002_before_generation_publish.bak",
 "TAKY_INCREMENTAL.js.20261004_000146.bak",
)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for part in iter(lambda:f.read(262144),b""):h.update(part)
 return h.hexdigest()
def candidates():
 out=[]
 root_names=[p.name for p in ROOT.iterdir() if p.is_file() and p.name.lower().endswith(".bak")]
 if set(root_names)-set(NAMES):raise RuntimeError("UNREVIEWED_NEW_BACKUP_FILES")
 for n in NAMES:
  s=ROOT/n;d=TARGET/n
  if s.is_file() and not d.exists():f=s;status="READY"
  elif d.is_file() and not s.exists():f=d;status="ALREADY_ARCHIVED"
  else:raise RuntimeError("FILE_COLLISION_OR_MISSING:"+n)
  out.append({"name":n,"source":str(s),"destination":str(d),
   "status":status,"sha256":sha(f),"length":f.stat().st_size})
 return out
def apply(files):
 TARGET.mkdir(parents=True,exist_ok=True)
 moved=[]
 try:
  for f in files:
   if f["status"]=="ALREADY_ARCHIVED":continue
   s=Path(f["source"]);d=Path(f["destination"])
   os.replace(s,d)
   if sha(d)!=f["sha256"]:raise RuntimeError("POST_MOVE_HASH_MISMATCH:"+f["name"])
   moved.append(f)
  return len(moved)
 except Exception:
  for f in reversed(moved):
   s=Path(f["source"]);d=Path(f["destination"])
   if d.exists() and not s.exists():os.replace(d,s)
  raise
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--apply",action="store_true")
 args=ap.parse_args()
 files=candidates()
 moved=apply(files) if args.apply else 0
 result={"schema":"TAKY_STAGE3_LEGACY_SCRIPT_REHOME_V1",
         "state":"ARCHIVED" if args.apply else "AUDIT",
         "moved_this_run":moved,"legacy_files":files,
         "active_scripts_moved":False,"raw_data_moved":False,
         "git_changes":False,"drive_changes":False}
 if args.apply:
  EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
  EVIDENCE.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"state":result["state"],"files":len(files),"moved":moved,
  "destination":str(TARGET)},ensure_ascii=False))
