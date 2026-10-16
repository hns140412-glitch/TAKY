"""Move pinned reference inbox files individually, preserve old directory junction.

Only 2 reviewed source folders and no active runtime state. If Windows refuses
file moves, stop safely and preserve existing bytes, no task kill.
"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(r"D:\Git PWA")
SRC=R/"TAKY-SOURCE-VAULT"/"data"
WAREHOUSE=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
MAPPING={"reference_inbox":"00_INBOX/REFERENCE_INBOX",
         "reference_intake":"00_INBOX/REFERENCE_INTAKE"}
RECEIPT=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"WORKBENCH_PINNED_INBOX_REHOME_20261013.json"
def sha(f):
 h=hashlib.sha256()
 with f.open("rb") as reader:
  for b in iter(lambda:reader.read(256*1024),b""):h.update(b)
 return h.hexdigest()
def files(path):
 return {p.name:(p.stat().st_size,sha(p)) for p in path.iterdir() if p.is_file()}
def one(name,apply):
 old=SRC/name;new=WAREHOUSE/MAPPING[name]
 if new.exists():
  if old.is_junction() and old.samefile(new):
   return {"name":name,"state":"ALREADY_REHOMED","files":len(files(new))}
  raise RuntimeError("DESTINATION_COLLISION:"+name)
 if not old.is_dir() or old.is_junction():raise RuntimeError("SOURCE_MISSING_OR_ALIAS:"+name)
 before=files(old)
 expected_count={"reference_inbox":4,"reference_intake":13}[name]
 if len(before)!=expected_count or any(x.is_dir() for x in old.iterdir()):
  raise RuntimeError("UNEXPECTED_FOLDER_CONTENT:"+name+":"+str(len(before)))
 latest=max(p.stat().st_mtime for p in old.iterdir())
 if time.time()-latest<600: return {"name":name,"state":"HOLD_RECENT_WRITE"}
 if not apply:return {"name":name,"state":"READY","files":len(before)}
 new.mkdir(parents=True,exist_ok=False)
 moved=[]
 try:
  for filename in sorted(before):
   src=old/filename;dst=new/filename
   os.rename(src,dst)
   moved.append(filename)
   if sha(dst)!=before[filename][1]:raise RuntimeError("FILE_HASH_DRIFT:"+filename)
  if any(old.iterdir()):raise RuntimeError("FOLDER_NOT_EMPTY_AFTER_FILE_MOVE")
  os.rmdir(old)
  result=subprocess.run(["cmd.exe","/c","mklink","/J",str(old),str(new)],
    capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=15)
  if result.returncode or not old.is_junction() or not old.samefile(new):
   raise RuntimeError("PINNED_DIR_ALIAS_FAILED:"+name)
  if files(new)!=before:raise RuntimeError("FINAL_FILE_HASH_COUNT_MISMATCH:"+name)
  return {"name":name,"state":"REHOMED_WITH_JUNCTION","files":len(before),"bytes":sum(v[0] for v in before.values()),
    "canonical":str(new),"legacy":str(old)}
 except BaseException:
  if old.is_junction():os.rmdir(old)
  if not old.exists():old.mkdir()
  for filename in reversed(moved):
   a=new/filename;b=old/filename
   if a.exists() and not b.exists():os.rename(a,b)
  if new.is_dir() and not any(new.iterdir()):new.rmdir()
  raise
def main():
 p=argparse.ArgumentParser()
 group=p.add_mutually_exclusive_group(required=True)
 group.add_argument("--audit",action="store_true")
 group.add_argument("--apply",action="store_true")
 a=p.parse_args()
 results=[]
 for name in MAPPING:
  try:res=one(name,a.apply)
  except PermissionError as exc:res={"name":name,"state":"HOLD_WINDOWS_FILE_HANDLE","error":str(exc)[:180]}
  results.append(res)
  if a.apply:print(json.dumps(res,ensure_ascii=False),flush=True)
 if a.apply:
  tmp=RECEIPT.with_suffix(".json.tmp")
  tmp.write_text(json.dumps({"schema":"TAKY_PINNED_REFERENCE_INBOX_REHOME_V1",
    "results":results,"no_force_process_close":True,
    "no_cloud_changes":True},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(tmp,RECEIPT)
 return {"status":"DONE" if all(x["state"] in ("REHOMED_WITH_JUNCTION","ALREADY_REHOMED") for x in results) else "PARTIAL",
   "results":results}
if __name__=="__main__":print(json.dumps(main(),ensure_ascii=False))
