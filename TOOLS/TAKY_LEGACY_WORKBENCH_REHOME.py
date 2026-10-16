"""Archive obsolete nested 2026-09 workbench tool and browser profile.

No copies; preserve old launch path as a same-volume junction. Do not operate
if Chrome or background apps still own the profile (separate preflight).
"""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(r"D:\Git PWA")
SRC=ROOT/"TAKY-SOURCE-VAULT"/"TOOLS"/"TAKY_AI_WORKBENCH"
DEST=ROOT/"TAKY_AI_WORKBENCH"/"90_ARCHIVE"/"LEGACY_STANDALONE_WORKBENCH_20260929"
RECEIPT=ROOT/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"LEGACY_STANDALONE_WORKBENCH_REHOME_20261013.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(256*1024),b""):h.update(block)
 return h.hexdigest()
def inventory(root):
 rows=[];size=0;recent=0
 for b,dirs,files in os.walk(root):
  dirs[:]=[d for d in dirs if not (Path(b)/d).is_junction()]
  for name in files:
   p=Path(b)/name
   if p.is_symlink():raise RuntimeError("LEGACY_WB_UNREVIEWED_SYMLINK_FILE")
   st=p.stat();size+=st.st_size;recent=max(recent,st.st_mtime)
   rows.append((p.relative_to(root).as_posix(),st.st_size))
 rows.sort()
 if not 1400<len(rows)<2800 or not 130_000_000<size<300_000_000:
  raise RuntimeError("LEGACY_WB_INVENTORY_CHANGED:"+str(len(rows))+","+str(size))
 sample=[rows[int(i*(len(rows)-1)/12)][0] for i in range(13)]
 return {"files":len(rows),"bytes":size,"last_mtime":recent,
    "sample_hashes":{rel:sha(root/rel) for rel in sample}}
def verify():
 if not DEST.is_dir() or not SRC.is_junction() or not SRC.samefile(DEST):
  raise RuntimeError("LEGACY_WB_CANONICAL_AND_ALIAS_MISSING")
 if not RECEIPT.is_file():raise RuntimeError("LEGACY_WB_RECEIPT_MISSING")
 proof=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 current=inventory(DEST)
 if current["files"]!=proof["files"] or current["bytes"]!=proof["bytes"]:
  raise RuntimeError("LEGACY_WB_COUNT_SIZE_DRIFT")
 for rel,val in proof["sample_hashes"].items():
  if sha(SRC/rel)!=val:raise RuntimeError("LEGACY_WB_SHA_DRIFT:"+rel)
 return {"status":"LEGACY_WORKBENCH_ARCHIVE_VERIFIED","files":current["files"],
   "bytes":current["bytes"],"canonical":str(DEST)}
def move(apply):
 if DEST.exists():return verify()
 if not SRC.is_dir() or SRC.is_junction() or DEST.exists():
  raise RuntimeError("LEGACY_WB_SOURCE_INVALID")
 if (SRC/".git").exists():raise RuntimeError("GIT_OWNED_WORKTREE_UNREVIEWED")
 info=inventory(SRC)
 if time.time()-info["last_mtime"]<3600:raise RuntimeError("LEGACY_WB_RECENT_WRITE")
 if not apply:return {"status":"READY","files":info["files"],"bytes":info["bytes"]}
 os.rename(SRC,DEST)
 try:
  r=subprocess.run(["cmd.exe","/c","mklink","/J",str(SRC),str(DEST)],
    capture_output=True,text=True,errors="replace",timeout=15)
  if r.returncode or not SRC.is_junction() or not SRC.samefile(DEST):
   raise RuntimeError("LEGACY_WB_JUNCTION_FAILED")
  after=inventory(DEST)
  if info!=after:raise RuntimeError("LEGACY_WB_POSTMOVE_INVENTORY_DRIFT")
  proof={"status":"ARCHIVED_WITH_OLD_PATH_ALIAS",**info,
   "canonical":str(DEST),"old_path":str(SRC),
   "active_pipeline_relocated":False,"no_duplicate_copy":True,
   "no_git_operation_or_deploy":True}
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  tmp=RECEIPT.with_suffix(".json.pending")
  tmp.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(tmp,RECEIPT)
  return verify()
 except BaseException:
  if SRC.is_junction():os.rmdir(SRC)
  if DEST.exists() and not SRC.exists():os.rename(DEST,SRC)
  raise
if __name__=="__main__":
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 a=p.parse_args()
 print(json.dumps(move(a.apply),ensure_ascii=False))
