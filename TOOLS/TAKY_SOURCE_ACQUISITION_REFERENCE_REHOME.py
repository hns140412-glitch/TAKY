"""Move cold acquired source bytes and derived catalog into the ONE workbench.

Keep 'runs' and CURRENT_RUN in SOURCE-VAULT pipeline state. Each source
directory retains exact backwards-compatible junction to physical target.
"""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
BASE=Path(r"D:\Git PWA")
SOURCE=BASE/"TAKY-SOURCE-VAULT"/"data"/"source_acquisition"
TARGET=BASE/"TAKY_AI_WORKBENCH"/"REFERENCE"
MAP={
 "deep_original":("80_UNCLASSIFIED/DEEP_ORIGINAL_ACQUIRED",17,"ACQUIRED_RAW_CANDIDATE"),
 "guide_catalog":("90_DERIVED/GUIDE_CATALOG",11,"DERIVED_CATALOG_UNREVIEWED"),
 "http_recovery_pilot":("90_DERIVED/HTTP_RECOVERY_PILOT",410,"DERIVED_RECOVERY_CANDIDATE")
}
RECEIPT=BASE/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"SOURCE_ACQUISITION_REFERENCE_REHOME_20261013.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as r:
  for b in iter(lambda:r.read(256*1024),b""):h.update(b)
 return h.hexdigest()
def index(dir):
 out={}
 for base,dirs,files in os.walk(dir):
  dirs[:]=[d for d in dirs if not (Path(base)/d).is_junction()]
  for name in files:
   p=Path(base)/name
   if p.is_symlink():raise RuntimeError("UNREVIEWED_REPARSE_CONTENT")
   out[p.relative_to(dir).as_posix()]=[p.stat().st_size,sha(p)]
 return out
def move(name,apply):
 relative,count,role=MAP[name]
 old=SOURCE/name;new=TARGET/relative
 if new.is_dir():
  if not old.is_junction() or not old.samefile(new):raise RuntimeError("SOURCE_ALIAS_MISMATCH:"+name)
  entries=index(new)
  if len(entries)!=count:raise RuntimeError("REHOMED_SOURCE_COUNT_DRIFT:"+name)
  return {"name":name,"state":"ALREADY_MOVED","files":len(entries),"size":sum(x[0] for x in entries.values()),"role":role}
 if not old.is_dir() or old.is_junction() or new.exists():raise RuntimeError("UNEXPECTED_SOURCE_OR_TARGET:"+name)
 entries=index(old)
 if len(entries)!=count:raise RuntimeError("PRE_MOVE_SOURCE_COUNT_DRIFT:"+name)
 if time.time()-max(x.stat().st_mtime for x in old.rglob("*") if x.is_file())<600:
  raise RuntimeError("CURRENTLY_MODIFIED_SOURCE_REFUSE_MOVE:"+name)
 if not apply:return {"name":name,"state":"READY","files":count,"size":sum(x[0] for x in entries.values()),"role":role}
 new.parent.mkdir(parents=True,exist_ok=True)
 os.rename(old,new)
 try:
  result=subprocess.run(["cmd.exe","/c","mklink","/J",str(old),str(new)],
   capture_output=True,text=True,errors="replace",timeout=15)
  if result.returncode or not old.is_junction() or not old.samefile(new):
   raise RuntimeError("COMPATIBILITY_JUNCTION_FAILED:"+name)
  if index(new)!=entries or index(old)!=entries:
   raise RuntimeError("AFTER_MOVE_SOURCE_HASH_DRIFT:"+name)
  return {"name":name,"state":"MOVED_WITH_ALIAS","files":count,
    "size":sum(x[0] for x in entries.values()),"role":role,"canonical":str(new),
    "old_path":str(old),"sha256":entries}
 except BaseException:
  if old.is_junction():os.rmdir(old)
  if new.exists() and not old.exists():os.rename(new,old)
  raise
if __name__=="__main__":
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 a=p.parse_args()
 all_results=[]
 for name in MAP:
  result=move(name,a.apply)
  all_results.append(result)
  if a.apply:print("SOURCE_REHOME",name,result["state"],flush=True)
 if a.apply:
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  t=RECEIPT.with_suffix(".json.pending")
  t.write_text(json.dumps({"schema":"TAKY_ACQUISITION_REFERENCES_REHOME_V1",
    "status":"REHOMED_ALL",
    "routes":all_results,"runs_pipeline_state_not_moved":True,
    "source_vault_original_paths_preserved":True,
    "file_copy_count":0,"git_push_or_deploy":False
   },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(t,RECEIPT)
 print(json.dumps({"status":"APPLIED" if a.apply else "PRECHECK",
  "files":sum(x["files"] for x in all_results),"bytes":sum(x["size"] for x in all_results),
  "groups":len(MAP)},ensure_ascii=False))
