"""Transfer central reference metadata DB into the WORKBENCH physical warehouse.

Safely moves individual files under a pinned directory (Windows may refuse to
rename source directory), deletes only the EMPTY old directory, then creates
legacy source-vault junction. On any incomplete step roll back moved files.
"""
import argparse,hashlib,json,os,sqlite3,subprocess,sys
from pathlib import Path
R=Path(r"D:\Git PWA")
OLD=R/"TAKY-SOURCE-VAULT"/"data"/"source_universe"
NEW=R/"TAKY_AI_WORKBENCH"/"REFERENCE"/"99_CONTROL"/"SOURCE_UNIVERSE"
RECEIPT=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"REFERENCE_CENTRAL_STATE_REHOME_20261013.json"
REQUIRED={"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3","UNIFIED_REFERENCE_LOCATOR_CURRENT.json","DRIVE_DISCOVERY_CURRENT.json"}
def source_inventory(d):
 return {p.name:(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
  for p in d.iterdir() if p.is_file()}
def dbcheck(db):
 conn=sqlite3.connect(str(db),timeout=1,isolation_level=None)
 try:
  conn.execute("BEGIN EXCLUSIVE")
  status=conn.execute("PRAGMA quick_check").fetchone()[0]
  conn.execute("COMMIT")
  if status!="ok":raise RuntimeError("SQLITE_INTEGRITY_FAIL:"+status)
 finally:conn.close()
def verify():
 if not NEW.is_dir() or not RECEIPT.is_file():raise RuntimeError("STATE_WAREHOUSE_MISSING")
 if not OLD.is_dir() or not os.path.isjunction(OLD) or not os.path.samefile(OLD,NEW):
  raise RuntimeError("PIPELINE_COMPATIBILITY_JUNCTION_MISSING")
 if not REQUIRED.issubset({f.name for f in NEW.iterdir() if f.is_file()}):
  raise RuntimeError("CENTRAL_STATE_FILES_MISSING")
 dbcheck(NEW/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3")
 return {"status":"CENTRAL_REFERENCE_STATE_CANONICAL_WORKBENCH","db_path":str(NEW/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3"),
  "old_worker_path_is_junction":True}
def apply():
 if NEW.is_dir() and RECEIPT.is_file():return verify()
 if NEW.exists():raise RuntimeError("STATE_TARGET_EXISTS_WITHOUT_RECEIPT")
 if not OLD.is_dir() or os.path.isjunction(OLD):raise RuntimeError("SOURCE_STATE_NOT_PHYSICAL")
 before=source_inventory(OLD)
 if not REQUIRED.issubset(before):raise RuntimeError("REQUIRED_DB_AND_DISCOVERY_MISSING")
 if any(p.name.endswith((".sqlite3-wal",".sqlite3-shm")) for p in OLD.iterdir()):
  raise RuntimeError("ACTIVE_SQLITE_WAL_MIGRATION_HOLD")
 dbcheck(OLD/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3")
 NEW.parent.mkdir(parents=True,exist_ok=True)
 NEW.mkdir()
 moved=[]
 try:
  for name in sorted(before):
   src=OLD/name;dst=NEW/name
   os.rename(src,dst)
   moved.append(name)
   after=dst.stat().st_size,hashlib.sha256(dst.read_bytes()).hexdigest()
   if after!=before[name]:raise RuntimeError("CENTRAL_STATE_FILE_SHA_CHANGED:"+name)
  if any(OLD.iterdir()):raise RuntimeError("UNREVIEWED_FILES_APPEARED_DURING_MOVE")
  os.rmdir(OLD) # empty directory only
  result=subprocess.run(["cmd.exe","/c","mklink","/J",str(OLD),str(NEW)],
    capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=15)
  if result.returncode or not OLD.is_dir() or not os.path.samefile(OLD,NEW):
   raise RuntimeError("COMPATIBILITY_JUNCTION_CREATION_FAILED")
  dbcheck(NEW/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3")
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  proof={"status":"CENTRAL_REFERENCE_STATE_REHOMED",
    "canonical":str(NEW),"old_worker_junction":str(OLD),
    "cutover_file_hashes":{k:list(v) for k,v in before.items()},
    "no_duplicate_db_copy":True,"worker_pipeline_exec_not_moved":True}
  temp=RECEIPT.with_suffix(".json.pending")
  temp.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(temp,RECEIPT)
  return verify()
 except BaseException:
  # Do not destroy valid DB contents in either location. Restore previous
  # physical source layout only if it can be unambiguously reconstructed.
  if OLD.is_dir() and os.path.isjunction(OLD):
   os.rmdir(OLD)
  if not OLD.exists():OLD.mkdir()
  for name in reversed(moved):
   src=NEW/name;dst=OLD/name
   if src.exists() and not dst.exists():os.rename(src,dst)
  if NEW.exists() and not any(NEW.iterdir()):NEW.rmdir()
  raise
if __name__=="__main__":
 a=argparse.ArgumentParser()
 g=a.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 opts=a.parse_args()
 if opts.audit:
  if NEW.exists() and RECEIPT.exists():r=verify()
  else:r={"status":"READY","source":str(OLD),"files":list(source_inventory(OLD))}
 else:r=apply()
 print(json.dumps(r,ensure_ascii=False))
