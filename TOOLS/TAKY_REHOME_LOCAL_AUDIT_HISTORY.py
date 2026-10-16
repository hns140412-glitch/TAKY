"""Cold audit history to WORKBENCH/90_ARCHIVE. Live scheduled audit path stays an alias.

No Git worktree deletion, branch modification or script changes. Same-volume
rename, complete file-count/size pre/post, 18 sample hashes, junction check.
"""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
BASE=Path(r"D:\Git PWA")
SRC=BASE/"TAKY-SOURCE-VAULT"/"reports"/"LOCAL_AUDIT"
DEST=BASE/"TAKY_AI_WORKBENCH"/"90_ARCHIVE"/"TAKY_LOCAL_AUDIT_HISTORY"
RECEIPT=BASE/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_LOCAL_AUDIT_HISTORY_REHOME_20261013.json"
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as r:
  for b in iter(lambda:r.read(512*1024),b""):h.update(b)
 return h.hexdigest()
def inventory(root):
 number=total=0
 newest=0
 largest=[]
 sample=[]
 dirs=0
 for base,names,files in os.walk(root):
  # Never follow symlink/junction reparse points from nested snapshots.
  names[:]=[x for x in names if not (Path(base)/x).is_junction() and not (Path(base)/x).is_symlink()]
  dirs+=len(names)
  for name in files:
   path=Path(base)/name
   if path.is_symlink() or path.is_junction():
    raise RuntimeError("UNREVIEWED_NESTED_REPARSE_FILE:"+str(path))
   try:st=path.stat()
   except OSError:raise RuntimeError("AUDIT_FILE_MISSING_DURING_SCAN:"+str(path))
   number+=1;total+=st.st_size
   newest=max(newest,st.st_mtime)
   rel=path.relative_to(root).as_posix()
   # Preserve just a small bounded sample, not an enormous manifest.
   if len(sample)<18 and number%3799==0:sample.append(rel)
   if len(largest)<3 or st.st_size>largest[0][0]:
    largest.append((st.st_size,rel))
    largest=sorted(largest)[-3:]
 if number<30000 or not 450_000_000<total<950_000_000 or dirs<100:
  raise RuntimeError("AUDIT_INVENTORY_UNEXPECTED:%s,%s,%s"%(number,total,dirs))
 return {"files":number,"bytes":total,"child_dirs":dirs,
   "latest_modified_epoch":newest,
   "sample_paths":sorted(set(sample+[p for _,p in largest]))}
def check():
 if not SRC.is_dir() or not SRC.is_junction() or not DEST.is_dir() or not SRC.samefile(DEST):
  raise RuntimeError("LOCAL_AUDIT_COMPAT_JUNCTION_OR_DEST_MISSING")
 if not RECEIPT.is_file():raise RuntimeError("LOCAL_AUDIT_RECEIPT_MISSING")
 proof=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 actual=inventory(DEST)
 # The scheduled read-only audit keeps appending into this archive through
 # the old junction. New files are permitted; missing baseline volume is not.
 if actual["files"]<proof["files"] or actual["bytes"]<proof["bytes"]:
  raise RuntimeError("LOCAL_AUDIT_BASELINE_COUNT_SIZE_LOST")
 for rel,d in proof["sample_sha256"].items():
  if digest(DEST/rel)!=d or digest(SRC/rel)!=d:
   raise RuntimeError("LOCAL_AUDIT_SAMPLED_HASH_DRIFT:"+rel)
 return {"status":"AUDIT_HISTORY_IN_WORKBENCH_VERIFIED",
   "files":actual["files"],"bytes":actual["bytes"],
   "scheduled_audit_old_path_still_valid":True,"canonical":str(DEST)}
def run(apply):
 if DEST.exists():return check()
 if not SRC.is_dir() or SRC.is_junction() or not DEST.parent.is_dir():
  raise RuntimeError("AUDIT_DIR_SRC_OR_TARGET_INVALID")
 if SRC.drive.casefold()!=DEST.drive.casefold():raise RuntimeError("CROSS_DRIVE_COPY_FORBIDDEN")
 info=inventory(SRC)
 if time.time()-info["latest_modified_epoch"]<600:
  return {"status":"HOLD_RECENT_AUDIT_WRITE","latest":info["latest_modified_epoch"]}
 if not apply:
  return {"status":"READY","files":info["files"],"bytes":info["bytes"],
   "latest_modified_epoch":info["latest_modified_epoch"]}
 sample={rel:digest(SRC/rel) for rel in info["sample_paths"]}
 os.rename(SRC,DEST)
 try:
  command=subprocess.run(["cmd.exe","/c","mklink","/J",str(SRC),str(DEST)],
    capture_output=True,text=True,errors="replace",timeout=15)
  if command.returncode or not SRC.is_junction() or not SRC.samefile(DEST):
   raise RuntimeError("AUDIT_OUTPUT_COMPAT_JUNCTION_FAILED")
  after=inventory(DEST)
  if after["files"]!=info["files"] or after["bytes"]!=info["bytes"]:
   raise RuntimeError("AUDIT_INVENTORY_CHANGED_AFTER_MOVE")
  for rel,h in sample.items():
   if digest(SRC/rel)!=h or digest(DEST/rel)!=h:
    raise RuntimeError("AUDIT_SAMPLED_HASH_CHANGED:"+rel)
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  result={"status":"PHYSICALLY_REHOMED_HISTORY_WITH_LEGACY_WRITER_ALIAS",
    "canonical":str(DEST),"old_scheduled_audit_path":str(SRC),
    "files":info["files"],"bytes":info["bytes"],"sample_sha256":sample,
    "audit_source_not_reference":True,"source_git_worktrees_kept_intact":True,
    "git_changes":False,"task_scheduler_changed":False,"drive_changed":False}
  t=RECEIPT.with_suffix(".json.pending")
  t.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(t,RECEIPT)
  return check()
 except BaseException:
  if SRC.is_junction():os.rmdir(SRC)
  if DEST.exists() and not SRC.exists():os.rename(DEST,SRC)
  raise
if __name__=="__main__":
 p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True)
 group.add_argument("--audit",action="store_true")
 group.add_argument("--apply",action="store_true")
 group.add_argument("--check",action="store_true")
 args=p.parse_args()
 print(json.dumps(check() if args.check else run(args.apply),ensure_ascii=False))
