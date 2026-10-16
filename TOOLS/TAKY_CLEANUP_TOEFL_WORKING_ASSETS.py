"""TAKY cleanup: move cold TOEFL preproduction audio to reference warehouse.

Preserves the old pipeline path as NTFS junction. No audio production or
transcoding, no app-bound artifact release. --audit / --apply / --check.
"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
BASE=Path(r"D:\Git PWA")
SOURCE=BASE/"TAKY-SOURCE-VAULT"/"RUNTIME"/"TAKY_TMP"/"TOEFL_PRIMARY_20261008"
TARGET=BASE/"TAKY_AI_WORKBENCH"/"REFERENCE"/"10_LEARNING"/"TOEFL"/"WORKING_AUDIO_20261008"
RECEIPT=BASE/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TOEFL_WORKING_AUDIO_REHOME_20261013.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(256*1024),b""):h.update(chunk)
 return h.hexdigest()
def inventory(root):
 out={}
 for base,dirs,files in os.walk(root):
  dirs[:]=[d for d in dirs if not (Path(base)/d).is_junction()]
  for n in files:
   f=Path(base)/n
   if f.is_symlink():raise RuntimeError("TOEFL_REPARSE_FILE_UNREVIEWED")
   out[f.relative_to(root).as_posix()]=[f.stat().st_size,sha(f)]
 return out
def check():
 if not SOURCE.is_dir() or not TARGET.is_dir() or not SOURCE.is_junction() or not SOURCE.samefile(TARGET):
  raise RuntimeError("TOEFL_CANONICAL_PATH_OR_ALIAS_INVALID")
 if not RECEIPT.is_file():raise RuntimeError("TOEFL_RECEIPT_ABSENT")
 old=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 current=inventory(TARGET)
 if current!=old["files"] or len(current)!=412:
  raise RuntimeError("TOEFL_AUDIO_HASH_OR_COUNT_DRIFT")
 return {"status":"TOEFL_PREPRODUCTION_WAREHOUSE_VERIFIED","files":len(current),
   "bytes":sum(x[0] for x in current.values()),"old_path_works":True}
def run(apply):
 if TARGET.exists():return check()
 if not SOURCE.is_dir() or SOURCE.is_junction():raise RuntimeError("TOEFL_SOURCE_INVALID")
 data=inventory(SOURCE)
 count=len(data);total=sum(x[0] for x in data.values())
 if count!=412 or not 300_000_000<total<400_000_000:
  raise RuntimeError("TOEFL_INVENTORY_UNEXPECTED:%s,%s"%(count,total))
 if not apply:return {"status":"READY","files":count,"bytes":total}
 TARGET.parent.mkdir(parents=True,exist_ok=True)
 os.rename(SOURCE,TARGET)
 try:
  p=subprocess.run(["cmd.exe","/c","mklink","/J",str(SOURCE),str(TARGET)],
     capture_output=True,text=True,errors="replace",timeout=16)
  if p.returncode or not SOURCE.is_junction() or not SOURCE.samefile(TARGET):
   raise RuntimeError("TOEFL_JUNCTION_FAILED")
  if inventory(TARGET)!=data or inventory(SOURCE)!=data:
   raise RuntimeError("TOEFL_POSTMOVE_SHA_MISMATCH")
  receipt={"status":"PHYSICAL_REHOMED_WITH_PIPELINE_ALIAS",
   "canonical":str(TARGET),"pipeline_compat_path":str(SOURCE),"files":data,
   "source_role":"DERIVED_PREPRODUCTION_AUDIO_UNAPPROVED",
   "no_new_audio_generated":True,"no_copy":True}
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  t=RECEIPT.with_suffix(".json.tmp")
  t.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(t,RECEIPT)
  return check()
 except BaseException:
  if SOURCE.is_junction():os.rmdir(SOURCE)
  if TARGET.exists() and not SOURCE.exists():os.rename(TARGET,SOURCE)
  raise
if __name__=="__main__":
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 g.add_argument("--check",action="store_true")
 a=p.parse_args()
 print(json.dumps(check() if a.check else run(a.apply),ensure_ascii=False))
