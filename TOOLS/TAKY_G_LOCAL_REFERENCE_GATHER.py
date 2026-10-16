"""Bounded internal gathering of historical G: architectural reference folders.

Source never moved or deleted. One Workbench physical copy per SHA-256; catalog
binds every origin path. Current sample: 0-작업중 and Hotel Reference.
No other G: directory may be traversed.
"""
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
sys.stdout.reconfigure(errors="replace")
ROOT=Path(r"D:\Git PWA")
SRC=Path(r"G:\#참고자료")
WB=ROOT/"TAKY_AI_WORKBENCH"/"REFERENCE"
CAN=WB/"20_ARCHITECTURE"/"LOCAL_LEGACY"/"G_REFERENCE"
EVID=WB/"99_CONTROL"/"G_LOCAL_LEGACY_GATHER_EVENTS.ndjson"
HOLD=ROOT/"TAKY_AI_WORKBENCH"/"00_CONTROL"/"G_DRIVE_GATHER_HOLD.json"
FOLDERS=("0-작업중","Hotel Reference","스타필드 하남도면","김포 실시도면","00_판교복합몰(2013.03.20)","02_송도현대아울렛(2015.08.13)")
sys.path.insert(0,str(ROOT/"TAKY"/"ENFORCEMENT"))
import taky_central_source_factory as factory
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(512*1024),b""):h.update(b)
 return h.hexdigest()
def records(selected=None):
 for group in FOLDERS:
  if selected is not None and group!=selected:continue
  base=SRC/group
  if not base.is_dir():raise RuntimeError("SOURCE_REFERENCE_ROOT_MISSING:"+str(base))
  for parent,dirs,files in os.walk(base):
   dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()
             and not (Path(parent)/d).is_junction() and d!=".git"]
   for name in files:
    file=Path(parent)/name
    if file.is_symlink() or file.is_junction():continue
    if file.name.casefold() in ("thumbs.db","desktop.ini") or file.suffix.casefold() in (".lnk",".url"):
     continue
    yield (group,file,file.relative_to(base))
def gather(group,file,rel,dry):
 st=file.stat()
 # Resume safety: trust a prior origin only if its identity, byte count,
 # timestamp, and physical central counterpart remain consistent.
 with factory.connect() as c:
  prior=c.execute("""SELECT source_id,size_bytes,modified FROM location
    WHERE provider='LOCAL_FILE' AND account='G_ARCHIVE_SOURCE' AND locator=?
    AND trust='RAW_HASH_VERIFIED'""",(str(file),)).fetchone()
  if prior and prior["size_bytes"]==st.st_size and prior["modified"]==str(st.st_mtime_ns):
   candidates=c.execute("""SELECT locator FROM location WHERE source_id=?
    AND provider='LOCAL_FILE' AND account='TAKY_WORKBENCH_REFERENCE'""",
    (prior["source_id"],)).fetchall()
   if any(Path(x[0]).is_file() and Path(x[0]).stat().st_size==st.st_size for x in candidates):
    return {"status":"ALREADY_CAPTURED_VERIFIED_PROVENANCE","source":str(file),"size":0}
 if st.st_size==0:return {"status":"EMPTY_REFERENCE_RETAINED_AT_SOURCE","file":str(file),"size":0}
 if st.st_size>650*1048576:
  return {"status":"OVERSIZE_SOURCE_NOT_COPIED","file":str(file),"size":st.st_size}
 if shutil.disk_usage(str(ROOT)).free<65*1073741824:
  return {"status":"LOW_DISK_STOP","file":str(file),"size":st.st_size}
 if dry:return {"status":"REVIEWED_ONLY","file":str(file),"size":st.st_size}
 digest=sha(file)
 with factory.connect() as conn:
  already=conn.execute("""SELECT l.locator FROM source s JOIN location l ON l.source_id=s.id
    WHERE s.original_sha256=? AND l.provider='LOCAL_FILE' ORDER BY l.locator""",(digest,)).fetchall()
  duplicate=None
  for row in already:
   path=Path(row[0])
   if path.is_file() and path.resolve().is_relative_to(WB.resolve()) and sha(path)==digest:
    duplicate=path;break
  if duplicate:
   canonical=duplicate
  else:
   canonical=CAN/group/rel
   canonical.parent.mkdir(parents=True,exist_ok=True)
   if canonical.is_file():
    if sha(canonical)!=digest:raise RuntimeError("DEST_COLLISION_WITH_DIFFERENT_SHA")
   else:
    temporary=canonical.with_name(canonical.name+".taky-gather-partial")
    if temporary.exists():raise RuntimeError("PREEXISTING_PARTIAL_REVIEW_NEEDED")
    try:
     out_sha=hashlib.sha256()
     with file.open("rb") as source,temporary.open("xb") as out:
      for chunk in iter(lambda:source.read(512*1024),b""):
       out.write(chunk);out_sha.update(chunk)
      out.flush();os.fsync(out.fileno())
     after=file.stat()
     if (after.st_size,after.st_mtime_ns)!=(st.st_size,st.st_mtime_ns):
      raise RuntimeError("SOURCE_CHANGED_DURING_GATHER")
     if digest!=out_sha.hexdigest() or digest!=sha(temporary):
      raise RuntimeError("COPY_HASH_MISMATCH")
     os.replace(temporary,canonical)
    finally:
     temporary.unlink(missing_ok=True)
  pre_existing_source=bool(conn.execute("SELECT 1 FROM source WHERE id=?",("raw:"+digest,)).fetchone())
  meta={"gathered_from":"G_LOCAL_ARCHIVE","legacy_folder":group,
    "legacy_source_path":str(file),"reference_role":"ARCHIVAL_UNREVIEWED",
    "raw_sha256":digest,"verified_original_bytes":True,"approved":False}
  local=factory.register(conn,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",str(canonical),
   canonical.name,"REFERENCE_UNREVIEWED",sha=digest,size=st.st_size,
   modified=str(canonical.stat().st_mtime_ns),domain="ARCHITECTURE",meta=meta)
  source=factory.register(conn,"LOCAL_FILE","G_ARCHIVE_SOURCE",str(file),
   file.name,"ARCHIVE_REFERENCE_ORIGIN",sha=digest,size=st.st_size,
   modified=str(st.st_mtime_ns),domain="ARCHITECTURE",meta=meta)
  if local!=source:raise RuntimeError("SOURCE_HASH_ID_NOT_SAME")
  if not pre_existing_source:
   factory.put_stage(conn,local,"REVIEW","PENDING_ARCHIVE_REVIEW",{})
   factory.put_stage(conn,local,"FORMING","BLOCKED_UNREVIEWED",{})
   factory.put_stage(conn,local,"LEARNING","BLOCKED_UNREVIEWED",{})
   factory.put_stage(conn,local,"CONSUME","BLOCKED_UNREVIEWED",{})
 return {"status":"DUPLICATE_LINKED" if duplicate else "HASH_VERIFIED_COPIED",
  "source":str(file),"canonical":str(canonical),"size":st.st_size,"sha256":digest}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 p.add_argument("--budget-mib",type=int,default=1450)
 p.add_argument("--max-files",type=int,default=140)
 p.add_argument("--only",choices=FOLDERS)
 args=p.parse_args()
 if HOLD.is_file():
  flag=json.loads(HOLD.read_text(encoding="utf-8-sig"))
  if flag.get("status")=="HOLD":
   print(json.dumps({"status":"G_DRIVE_HOLD_USER_DIRECTIVE",
    "no_g_drive_read_or_mutation":True,"resume_requires_approval":True},ensure_ascii=False))
   raise SystemExit(3)
 result=[];total=0
 for group,file,rel in records(args.only):
  if sum(x["status"] not in ("ALREADY_CAPTURED_VERIFIED_PROVENANCE",) for x in result)>=args.max_files:break
  try:sz=file.stat().st_size
  except OSError:continue
  if total+sz>args.budget_mib*1048576:continue
  try:
   x=gather(group,file,rel,not args.apply)
  except Exception as e:
   x={"status":"ERROR","source":str(file),"reason":type(e).__name__,"details":str(e)[:160]}
  result.append(x)
  if x["status"]=="HASH_VERIFIED_COPIED":total+=sz
  if args.apply:
   EVID.parent.mkdir(parents=True,exist_ok=True)
   with EVID.open("a",encoding="utf-8") as f:
    f.write(json.dumps(x,ensure_ascii=False)+"\n")
   if len(result)%8==0:print("GATHER_PROGRESS",len(result),round(total/1048576,1),"MiB",flush=True)
 outcome={"status":"APPLIED" if args.apply else "AUDIT",
  "total_inspected":len(result),"copied_bytes":total,
  "by_status":{kind:sum(x["status"]==kind for x in result) for kind in set(x["status"] for x in result)},
  "originals_modified":0,"path":str(CAN)}
 print(json.dumps(outcome,ensure_ascii=False))
if __name__=="__main__":main()
