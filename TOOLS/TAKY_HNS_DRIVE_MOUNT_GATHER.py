"""Internal gathering: import existing mounted HNS Google Drive RAW into Workbench.

Explicit allowlist of three already identified non-operational source folders.
No network scraper, no Git/Drive mutation, no runtime/user-record folders.
SHA-256 dedupe, original Drive file-ID provenance, 15MiB/file and 128MiB
per bounded batch by default. Larger files require an explicit later batch.
"""
import argparse,hashlib,json,os,sys,time,unicodedata
from pathlib import Path
R=Path(r"D:\Git PWA")
MOUNT=Path("F:/내 드라이브/TAKY")
WB=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
DISCOVERY=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"CROSS_STORAGE_DRIVE_METADATA_DISCOVERY_20261013.json"
RECEIPT=WB/"99_CONTROL"/"HNS_DRIVE_MOUNT_GATHER_CURRENT.json"
sys.path.insert(0,str(R/"TAKY"/"ENFORCEMENT"))
import taky_central_source_factory as f
SOURCES={
 "SHARED_REFERENCE":(MOUNT/"20_PLATFORM"/"03_COMMON"/"SHARED_REFERENCE",
   "80_UNCLASSIFIED","COMMON_REFERENCE"),
 "LEARNING_RAW":(MOUNT/"10_DOMAINS"/"01_LEARNING"/"02_RAW_MINING",
   "10_LEARNING","LEARNING_RAW"),
 "ARCH_RAW":(MOUNT/"10_DOMAINS"/"02_ARCHIGROW"/"02_RAW",
   "20_ARCHITECTURE","ARCHITECTURE_RAW"),
 "LEARNING_CNE":(MOUNT/"10_DOMAINS"/"01_LEARNING"/"02_RAW_MINING"/"CNE_LITERACY_20261007",
   "10_LEARNING","LITERACY_ACQUIRED_RAW"),
 "LEARNING_INCH":(MOUNT/"10_DOMAINS"/"01_LEARNING"/"02_RAW_MINING"/"INCH_20260901_3383177_OFFICIAL_RAW",
   "10_LEARNING","INCH_OFFICIAL_RAW"),
 "LEARNING_MINED":(MOUNT/"10_DOMAINS"/"01_LEARNING"/"02_RAW_MINING"/"MINED",
   "90_DERIVED","MINED_REFERENCE_CANDIDATE"),
 "LEARNING_WRITING_PACKS":(MOUNT/"10_DOMAINS"/"01_LEARNING"/"02_RAW_MINING"/"MINED"/"REFERENCE_INTAKE_ELEMENTARY_WRITING_2026-09-25",
   "10_LEARNING","LEARNING_WRITING_SOURCE_PACK"),
}
EXT_NATIVE={".gdoc",".gsheet",".gslides",".gshortcut",".gdraw",".gform"}
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as reader:
  for block in iter(lambda:reader.read(256*1024),b""):h.update(block)
 return h.hexdigest()
def match_name(name):
 return unicodedata.normalize("NFC",name).casefold()
def inventory():
 raw=json.loads(DISCOVERY.read_text(encoding="utf-8-sig"))
 folder_data={x["group"]:x["files"] for x in raw["folders"] if x.get("account")=="HNS"}
 extra=json.loads((WB/"99_CONTROL"/"DRIVE_NESTED_REFERENCE_FOLDERS.json").read_text(encoding="utf-8-sig"))
 folder_data[extra["group"]]=extra["files"]
 records=[];skipped=[]
 for group,(root,category,role) in SOURCES.items():
  if not root.is_dir():raise RuntimeError("HNS_MOUNT_REFERENCE_MISSING:"+str(root))
  providers={}
  for item in folder_data[group]:
   if item.get("kind")!="file":continue
   providers.setdefault(match_name(item["name"]),[]).append(item)
  for file in sorted(root.iterdir(),key=lambda p:p.name):
   if not file.is_file():continue
   if file.suffix.lower() in EXT_NATIVE:
    skipped.append({"group":group,"file_name":file.name,"reason":"GOOGLE_NATIVE_LINK_REQUIRES_EXPORT"})
    continue
   if file.is_symlink():raise RuntimeError("REFERENCE_MOUNT_SYMLINK_UNREVIEWED:"+str(file))
   matches=providers.get(match_name(file.name),[])
   if len(matches)!=1:
    skipped.append({"group":group,"file_name":file.name,"reason":"MISSING_OR_AMBIGUOUS_DRIVE_FILE_ID","matched":len(matches)})
    continue
   item=matches[0]
   stat=file.stat()
   if item.get("size_bytes") and int(item["size_bytes"])!=stat.st_size:
    skipped.append({"group":group,"file_name":file.name,"reason":"MOUNT_VS_DRIVE_METADATA_SIZE_DIFFERS"})
    continue
   records.append({"group":group,"drive_id":item["file_id"],"name":file.name,
    "source":file,"category":category,"role":role,"size":stat.st_size})
 return sorted(records,key=lambda x:(x["size"],x["group"],x["name"])),skipped
def capture(record,conn):
 origin=record["source"];old=origin.stat()
 fid=record["drive_id"]
 path=WB/record["category"]/"DRIVE_ORIGINALS"/"HNS"/record["group"]
 path.mkdir(parents=True,exist_ok=True)
 desired=path/(fid+"__"+unicodedata.normalize("NFC",record["name"]))
 sid_row=conn.execute("""SELECT s.original_sha256,l.locator FROM source s
    JOIN location l ON s.id=l.source_id WHERE l.provider='GOOGLE_DRIVE'
    AND l.account='HNS' AND l.locator=?""",(fid,)).fetchone()
 if sid_row and sid_row["original_sha256"]:
  prior=conn.execute("""SELECT locator FROM location WHERE source_id=?
    AND provider='LOCAL_FILE' ORDER BY locator""",("raw:"+sid_row["original_sha256"],)).fetchall()
  if any(Path(x[0]).is_file() for x in prior):
   return {"id":fid,"status":"ALREADY_CAPTURED","bytes":0}
 tmp=path/(fid+".capture.partial")
 if tmp.exists():raise RuntimeError("STALE_CAPTURE_TEMP_MANUAL_REVIEW:"+str(tmp))
 digest=hashlib.sha256()
 byte_count=0
 try:
  with origin.open("rb") as inp, tmp.open("xb") as out:
   for block in iter(lambda:inp.read(262144),b""):
    out.write(block);digest.update(block);byte_count+=len(block)
   out.flush();os.fsync(out.fileno())
  after=origin.stat()
  if (old.st_mtime_ns,old.st_size)!=(after.st_mtime_ns,after.st_size) or byte_count!=old.st_size:
   raise RuntimeError("DRIVE_FILE_CHANGED_DURING_GATHER:"+fid)
  file_digest=digest.hexdigest()
  if sha(tmp)!=file_digest:raise RuntimeError("LOCAL_COPY_SHA_MISMATCH:"+fid)
  known=conn.execute("""SELECT locator FROM source s JOIN location l ON l.source_id=s.id
    WHERE s.original_sha256=? AND l.provider='LOCAL_FILE' ORDER BY l.locator""",(file_digest,)).fetchall()
  duplicate=None
  for row in known:
   candidate=Path(row[0])
   if candidate.is_file() and candidate.resolve().is_relative_to(WB.resolve()) and sha(candidate)==file_digest:
    duplicate=candidate;break
  if duplicate:
   final=duplicate
   tmp.unlink()
  else:
   if desired.exists() and sha(desired)!=file_digest:raise RuntimeError("DRIVE_TARGET_ID_COLLISION:"+fid)
   if not desired.exists():os.replace(tmp,desired)
   else:tmp.unlink()
   final=desired
  pre_existing_source=bool(conn.execute("SELECT 1 FROM source WHERE id=?",("raw:"+file_digest,)).fetchone())
  metadata={"source_account":"HNS","origin_file_id":fid,"google_drive_mount":True,
    "source_folder_group":record["group"],"hash_verified":True,
    "review_status":"PENDING","approved":False,"original_display_name":record["name"]}
  canonical=f.register(conn,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",str(final),final.name,
    "REFERENCE_UNREVIEWED",sha=file_digest,size=byte_count,
    modified=str(final.stat().st_mtime_ns),meta=metadata)
  linked=f.register(conn,"GOOGLE_DRIVE","HNS",fid,record["name"],record["role"],
    sha=file_digest,size=byte_count,meta=metadata)
  if canonical!=linked:raise RuntimeError("DRIVE_ID_SHA_MAPPING_MISMATCH")
  if not pre_existing_source:
   for stage,state in (("EXTRACT","PENDING"),("REVIEW","WAITING_CONTENT_REVIEW"),
       ("FORMING","BLOCKED_REVIEW"),("LEARNING","BLOCKED_REVIEW"),
       ("CONSUME","BLOCKED_UNAPPROVED")):
    f.put_stage(conn,linked,stage,state,{"source":"DRIVE_RAW","sha256":file_digest})
  f.event(conn,linked,"DRIVE_MOUNT_RAW_GATHERED",{
    "drive_file_id":fid,"mount_path":str(origin),"physical_canonical":str(final),
    "sha256":file_digest,"deduped_against_existing_local":bool(duplicate)})
  return {"id":fid,"status":"DEDUPED" if duplicate else "CAPTURED",
     "bytes":byte_count,"physical":str(final),"sha256":file_digest,"name":record["name"]}
 finally:
  if tmp.exists():tmp.unlink()
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 p.add_argument("--max-files",type=int,default=45)
 p.add_argument("--max-file-mib",type=int,default=15)
 p.add_argument("--budget-mib",type=int,default=128)
 args=p.parse_args()
 items,skipped=inventory()
 max_bytes=args.max_file_mib*1048576
 batch_bytes=args.budget_mib*1048576
 result=[];total=0
 if args.apply:
  connection=f.connect()
  try:
   for x in items:
    # Verified originals from earlier batches must NOT exhaust the next
    # batch's file-count or byte budget. Preserve previous source identity.
    linked=connection.execute("""SELECT s.original_sha256 FROM location l
      JOIN source s ON s.id=l.source_id WHERE l.provider='GOOGLE_DRIVE'
      AND l.account='HNS' AND l.locator=?""",(x["drive_id"],)).fetchone()
    if linked and linked["original_sha256"]:
     physical=connection.execute("""SELECT locator FROM location
       WHERE source_id=? AND provider='LOCAL_FILE' LIMIT 10""",
       ("raw:"+linked["original_sha256"],)).fetchall()
     if any(Path(k[0]).is_file() for k in physical):
      continue
    if len(result)>=args.max_files:break
    if x["size"]<=0:
     skipped.append({"id":x["drive_id"],"reason":"ZERO_LENGTH"})
     continue
    if x["size"]>max_bytes:
     skipped.append({"id":x["drive_id"],"size":x["size"],"reason":"OVERSIZE_SEPARATE_BATCH"})
     continue
    if total+x["size"]>batch_bytes:
     skipped.append({"id":x["drive_id"],"size":x["size"],"reason":"BUDGET_FOR_LATER_BATCH"})
     continue
    try:
     with connection:
      completed=capture(x,connection)
     result.append(completed)
     total+=completed["bytes"]
     print("CAPTURE",completed["status"],x["group"],x["name"],completed["bytes"],flush=True)
    except Exception as e:
     skipped.append({"id":x["drive_id"],"name":x["name"],"reason":type(e).__name__,"detail":str(e)[:200]})
  finally:connection.close()
 output={"schema":"TAKY_HNS_INTERNAL_GATHER_V1",
   "status":"CAPTURE_BATCH_RECORDED" if args.apply else "INVENTORY_ONLY",
   "discovered_direct_source_files":len(items),"copied_originals":result,
   "skipped_or_future_batch":skipped,"total_copied_bytes":total,
   "drive_files_moved_or_deleted":0,"cloud_write_actions":0,"central_db":str(f.DB),
   "full_original_set_gathered":len(result)==len(items)}
 if args.apply:
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  RECEIPT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  log=RECEIPT.parent/"HNS_DRIVE_MOUNT_GATHER_EVENTS.ndjson"
  with log.open("a",encoding="utf-8") as logfile:
   for item in result:
    logfile.write(json.dumps(item,ensure_ascii=False)+"\n")
 print(json.dumps({"status":output["status"],
  "candidate_count":len(items),"completed_count":len(result),
  "copied_bytes":total,"skips":len(skipped),
  "receipt":str(RECEIPT) if args.apply else None},ensure_ascii=False))
if __name__=="__main__":main()
