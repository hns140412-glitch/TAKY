"""Relocate only verified, non-Git-owned legacy TAKY work artifacts.

--audit: no changes
--apply: atomic D: rename, SHA-256 verification, old-path compatibility junction,
         owner registry + evidence update.
Never relocates RAW, HNS/SIEZEALL Drive, active 2026-10-12 voice work or source code.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,datetime
from pathlib import Path

ROOT=Path(r"D:\Git PWA")
TAKY=ROOT/"TAKY"
WB=ROOT/"TAKY_AI_WORKBENCH"
RECEIPT=WB/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_STAGE2_REHOME_RECEIPT_20261013.json"
PAIRS=(
 (TAKY/"backup",WB/"90_ARCHIVE"/"TAKY_LEGACY_BACKUP_20261013"),
 (TAKY/"staging"/"content_supply_p0",
  WB/"50_INTEGRATION_TEST"/"CONTENT_SUPPLY"/"content_supply_p0"),
)

def hashes(dir):
 h={}
 for p in sorted(dir.rglob("*")):
  if p.is_file():
   v=hashlib.sha256()
   with p.open("rb") as src:
    for block in iter(lambda:src.read(262144),b""):v.update(block)
   h[p.relative_to(dir).as_posix()]=v.hexdigest()
 return h

def tracked(prefix):
 rel=prefix.relative_to(TAKY).as_posix()
 p=subprocess.run(["git","-C",str(TAKY),"ls-files","--",rel],
                  capture_output=True,text=True,encoding="utf-8",timeout=10,check=True)
 return [x for x in p.stdout.splitlines() if x]

def inspect():
 out=[]
 for src,dst in PAIRS:
  if tracked(src):raise RuntimeError("TRACKED_FILES_REFUSE_REHOME:"+str(src))
  if src.is_dir() and dst.is_dir() and os.path.samefile(src,dst):
   state="MOVED_ALIAS_PRESENT"
   contents=hashes(dst)
  elif src.is_dir() and not dst.exists():
   state="READY"
   contents=hashes(src)
  else:raise RuntimeError("UNEXPECTED_SOURCE_DEST_STATE:"+str(src)+":"+str(dst))
  if not contents:raise RuntimeError("REFUSE_EMPTY_SOURCE:"+str(src))
  if src.is_symlink() and state!="MOVED_ALIAS_PRESENT":
   raise RuntimeError("SYMLINK_UNEXPECTED:"+str(src))
  out.append({"source":str(src),"destination":str(dst),
    "state":state,"file_count":len(contents),"sha256":contents})
 return out

def move(entry):
 src=Path(entry["source"]);dst=Path(entry["destination"])
 if entry["state"]=="MOVED_ALIAS_PRESENT":
  if hashes(src)!=entry["sha256"] or hashes(dst)!=entry["sha256"]:
   raise RuntimeError("EXISTING_ALIAS_CONTENT_HASH_MISMATCH:"+str(src))
  return {**entry,"status":"ALREADY_MOVED"}
 dst.parent.mkdir(parents=True,exist_ok=True)
 os.rename(src,dst)
 p=subprocess.run(["cmd.exe","/c","mklink","/J",str(src),str(dst)],
                  capture_output=True,text=True,errors="replace",timeout=12)
 if p.returncode or not src.is_dir() or not os.path.samefile(src,dst):
  if not src.exists():os.rename(dst,src)
  raise RuntimeError("JUNCTION_FAILED_MOVE_ROLLED_BACK:"+str(src)+":"+p.stderr[-200:])
 if hashes(src)!=entry["sha256"] or hashes(dst)!=entry["sha256"]:
  raise RuntimeError("AFTER_MOVE_HASH_MISMATCH:"+str(src))
 return {**entry,"status":"MOVED_WITH_COMPAT_ALIAS"}

def persist(entries):
 reg=WB/"00_CONTROL"/"PATH_REGISTRY.json"
 d=json.loads(reg.read_text(encoding="utf-8-sig"))
 d.update({
   "taky_legacy_backups":"D:/Git PWA/TAKY_AI_WORKBENCH/90_ARCHIVE/TAKY_LEGACY_BACKUP_20261013",
   "taky_legacy_backup_compat_alias":"D:/Git PWA/TAKY/backup",
   "content_supply_candidate_fixture":"D:/Git PWA/TAKY_AI_WORKBENCH/50_INTEGRATION_TEST/CONTENT_SUPPLY/content_supply_p0",
   "content_supply_candidate_compat_alias":"D:/Git PWA/TAKY/staging/content_supply_p0",
   "play_camp_candidate_consumer":"D:/Git PWA/Play Camp/src/data/supplyCandidate.ts",
   "play_camp_candidate_test":"D:/Git PWA/TAKY/ENFORCEMENT/content_supply_app_consumer_test.py",
   "cleanup_stage2_receipt":"D:/Git PWA/TAKY_AI_WORKBENCH/01_BACKLOG_AND_ADOPTION/80_EVIDENCE/TAKY_STAGE2_REHOME_RECEIPT_20261013.json"
 })
 reg.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 q=WB/"01_BACKLOG_AND_ADOPTION"/"70_EXECUTION_QUEUE"/"TASK_REGISTER.json"
 t=json.loads(q.read_text(encoding="utf-8-sig"))
 for row in t.get("tasks",[]):
  if row.get("id")=="CLN-005":
   row["status"]="IMPLEMENTING"
   row["decision"]="VERIFIED_STAGE1_AUDIO_13_AND_STAGE2_BACKUP_20_CONTENT_FIXTURES_8_MOVED_WITH_COMPAT_ALIASES; 20261012_VOICE_AND_ACTIVE_STAGING_NOT_MOVED"
   row["evidence"]=sorted(set(row.get("evidence",[])+[str(RECEIPT)]))
 q.write_text(json.dumps(t,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 doc=TAKY/"CURRENT"/"TAKY_PATH_AUTHORITY.md"
 s=doc.read_text(encoding="utf-8-sig")
 note="- Archived TAKY backup snapshots: D:/Git PWA/TAKY_AI_WORKBENCH/90_ARCHIVE/TAKY_LEGACY_BACKUP_20261013 (legacy TAKY/backup compatibility junction)\n- Forming/content-supply candidate fixture: D:/Git PWA/TAKY_AI_WORKBENCH/50_INTEGRATION_TEST/CONTENT_SUPPLY/content_supply_p0 (legacy TAKY/staging/content_supply_p0 junction); producer consumer app: D:/Git PWA/Play Camp/src/data/supplyCandidate.ts\n"
 if "Archived TAKY backup snapshots:" not in s:
  s=s.replace("- Raw gathering and scheduled local collector entrypoints:",note+"- Raw gathering and scheduled local collector entrypoints:")
  doc.write_text(s,encoding="utf-8")

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true");g.add_argument("--apply",action="store_true")
 a=p.parse_args()
 entries=inspect()
 if a.audit:
  print(json.dumps({"state":"READONLY","pairs":[{"src":x["source"],"dest":x["destination"],"files":x["file_count"],"state":x["state"]} for x in entries]},ensure_ascii=False))
  return 0
 completed=[]
 try:
  for entry in entries:completed.append(move(entry))
  persist(completed)
  outcome={"schema":"TAKY_STAGE2_REHOME_RECEIPT_V1",
   "created_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "status":"PASS","entries":completed,"raw_root_moved":False,
   "git_branches_changed":False,"drive_modified":False,
   "active_voice_20261012_moved":False}
 except Exception as exc:
  outcome={"status":"PARTIAL_HOLD","exception":str(exc),"completed":completed}
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  RECEIPT.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  raise
 RECEIPT.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","moved":[{"name":Path(e["source"]).name,"files":e["file_count"],"status":e["status"]} for e in completed],"receipt":str(RECEIPT)},ensure_ascii=False))
 return 0

if __name__=="__main__":sys.exit(main())
