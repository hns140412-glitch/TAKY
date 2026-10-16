"""Cold Notion audit export -> WORKBENCH/90_ARCHIVE, old path junction retained."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(r"D:\Git PWA")
SRC=R/"TAKY-SOURCE-VAULT"/"exports"/"NOTION_COLLECTOR_CODE_AUDIT_20261005"
DST=R/"TAKY_AI_WORKBENCH"/"90_ARCHIVE"/"NOTION_COLLECTOR_CODE_AUDIT_20261005"
RECEIPT=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"NOTION_CODE_AUDIT_EXPORT_REHOME_20261013.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(256*1024),b""):h.update(b)
 return h.hexdigest()
def manifest(d):
 out={}
 for p in d.rglob("*"):
  if p.is_file():out[p.relative_to(d).as_posix()]=[p.stat().st_size,sha(p)]
 return out
def verify():
 if not SRC.is_junction() or not SRC.samefile(DST) or not RECEIPT.is_file():
  raise RuntimeError("NOTION_EXPORT_COMPAT_OR_RECEIPT_INVALID")
 e=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 if manifest(DST)!=e["files"] or manifest(SRC)!=e["files"]:
  raise RuntimeError("NOTION_EXPORT_HASH_DRIFT")
 return {"status":"NOTION_AUDIT_EXPORT_ARCHIVED","files":len(e["files"]),"bytes":sum(x[0] for x in e["files"].values())}
def move(apply):
 if DST.exists():return verify()
 if not SRC.is_dir() or SRC.is_junction():raise RuntimeError("NOTION_EXPORT_SOURCE_INVALID")
 files=manifest(SRC)
 if len(files)!=118:raise RuntimeError("NOTION_EXPORT_FILE_COUNT_CHANGED")
 if not apply:return {"status":"READY","files":len(files),"bytes":sum(x[0] for x in files.values())}
 DST.parent.mkdir(parents=True,exist_ok=True)
 os.rename(SRC,DST)
 try:
  result=subprocess.run(["cmd.exe","/c","mklink","/J",str(SRC),str(DST)],
    capture_output=True,text=True,errors="replace",timeout=15)
  if result.returncode or not SRC.is_junction() or not SRC.samefile(DST):
   raise RuntimeError("NOTION_EXPORT_COMPAT_JUNCTION_FAILED")
  if manifest(DST)!=files:raise RuntimeError("NOTION_EXPORT_POST_MOVE_HASH_DRIFT")
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  RECEIPT.write_text(json.dumps({"status":"AUDIT_ARCHIVED_NOT_REFERENCE",
    "old_path":str(SRC),"new_path":str(DST),"files":files,
    "no_physical_copy":True,"source_code_modified":False,"git_push":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  return verify()
 except BaseException:
  if SRC.is_junction():os.rmdir(SRC)
  if DST.is_dir() and not SRC.exists():os.rename(DST,SRC)
  raise
if __name__=="__main__":
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true");g.add_argument("--apply",action="store_true")
 args=p.parse_args()
 print(json.dumps(move(args.apply),ensure_ascii=False))
