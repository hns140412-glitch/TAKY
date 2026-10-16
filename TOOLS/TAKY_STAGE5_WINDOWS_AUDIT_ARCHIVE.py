"""Move only obsolete system-admin audit snapshots; keep original junction.
Does not touch AutoCAD settings, Windows registry, scheduled tasks or repo code.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
ROOT=Path("D:/Git PWA")
SOURCE=ROOT/"TAKY"/"TAKY_AUDIT_LOCAL"
TARGET=ROOT/"TAKY_AI_WORKBENCH"/"90_ARCHIVE"/"TAKY_WINDOWS_ADMIN_AUDIT_20261007"
RECEIPT=ROOT/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"STAGE5_WINDOWS_AUDIT_RELOCATION_20261013.json"
def digest(f):
 h=hashlib.sha256()
 with f.open("rb") as inp:
  for b in iter(lambda:inp.read(262144),b""):h.update(b)
 return h.hexdigest()
def inventory(root):
 return {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob("*")) if p.is_file()}
def apply():
 git=subprocess.run(["git","-C",str(ROOT/"TAKY"),"ls-files","--","TAKY_AUDIT_LOCAL"],
   capture_output=True,text=True,check=True,timeout=15)
 if git.stdout.strip():raise RuntimeError("GIT_TRACKED_SOURCE")
 if SOURCE.is_dir() and TARGET.is_dir() and os.path.samefile(SOURCE,TARGET):
  if not RECEIPT.is_file():raise RuntimeError("RELOCATION_RECEIPT_MISSING")
  expected=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))["sha256"]
  if inventory(SOURCE)!=expected or inventory(TARGET)!=expected:
   raise RuntimeError("RELOCATED_ADMIN_AUDIT_HASH_DRIFT")
  return {"status":"ALREADY_MOVED_AND_SHA_VERIFIED","files":len(expected)}
 if not SOURCE.is_dir() or TARGET.exists():raise RuntimeError("SOURCE_DESTINATION_COLLISION")
 src=inventory(SOURCE)
 if len(src)!=11:raise RuntimeError("UNEXPECTED_ADMIN_AUDIT_FILE_COUNT")
 os.rename(SOURCE,TARGET)
 proc=subprocess.run(["cmd.exe","/c","mklink","/J",str(SOURCE),str(TARGET)],
    capture_output=True,text=True,timeout=20)
 if proc.returncode or not SOURCE.is_dir() or not os.path.samefile(SOURCE,TARGET):
  if not SOURCE.exists():os.rename(TARGET,SOURCE)
  raise RuntimeError("ALIAS_FAILED_MOVE_ROLLED_BACK")
 if inventory(SOURCE)!=src or inventory(TARGET)!=src:
  raise RuntimeError("SHA256_MISMATCH_AFTER_MOVE")
 RECEIPT.parent.mkdir(parents=True,exist_ok=True)
 RECEIPT.write_text(json.dumps({"status":"REHOMED_WITH_COMPAT_JUNCTION",
  "source":str(SOURCE),"destination":str(TARGET),"sha256":src,
  "files":len(src),"system_settings_changed":False,
  "git_changes":False,"drive_changes":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return {"status":"REHOMED_WITH_COMPAT_JUNCTION","files":len(src)}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 args=p.parse_args()
 if args.apply:result=apply()
 else:
  result={"status":"AUDIT","source_files":len(inventory(SOURCE)),
          "destination_exists":TARGET.exists()}
 print(json.dumps(result,ensure_ascii=False))
