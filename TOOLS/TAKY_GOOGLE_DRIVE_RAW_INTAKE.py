"""Verify raw Drive bytes staged from authenticated connected accounts.

Base64 staging is transport scratch ONLY. Persist one SHA-verified original
inside WORKBENCH/REFERENCE; bind BOTH original Drive file ID and local bytes to
the same source_id. No Drive mutation, user records, auto-learning or deletion
of any original data.

Python standard library + existing central source factory.
"""
import base64,binascii,hashlib,json,os,sys,unicodedata
from pathlib import Path
R=Path(r"D:\Git PWA")
WB=R/"TAKY_AI_WORKBENCH"
WAREHOUSE=WB/"REFERENCE"
STAGE=WAREHOUSE/"00_INBOX"/"DRIVE_RAW_STAGE"
sys.path.insert(0,str(R/"TAKY"/"ENFORCEMENT"))
import taky_central_source_factory as factory
RECEIPT=WAREHOUSE/"99_CONTROL"/"DRIVE_RAW_CAPTURE_CURRENT.json"
ITEMS=[
 {"account":"HNS","drive_id":"11-gouremXEu81mFk_q-2BKLRuJMdSFX0","file_name":"ARCHIGROW_ACCOUNT_CONVERSATION_MINING_2026-09-30_V1.md","bytes":38534,"category":"20_ARCHITECTURE"},
 {"account":"HNS","drive_id":"1sevykEumN_P1oRbuK0t9jW8BZjyvXzbL","file_name":"단면도.png","bytes":99890,"category":"20_ARCHITECTURE"},
 {"account":"SIEZEALL","drive_id":"1EEqI7urtdYZnt1vvMXX-cWdVylOVwCl7","file_name":"한글_쑥쑥_카드.pdf","bytes":168491,"category":"10_LEARNING"},
]
def hash_file(p):
 h=hashlib.sha256()
 with p.open("rb") as reader:
  for block in iter(lambda:reader.read(256*1024),b""):h.update(block)
 return h.hexdigest()
def original(item):
 staged=STAGE/(item["account"]+"_"+item["drive_id"]+".b64")
 if not staged.is_file():raise RuntimeError("STAGED_DRIVE_BYTES_MISSING:"+str(staged))
 binary=base64.b64decode("".join(staged.read_text(encoding="ascii").split()),validate=True)
 if len(binary)!=item["bytes"]:raise RuntimeError("DRIVE_DOWNLOAD_BYTE_COUNT_MISMATCH:"+item["drive_id"])
 digest=hashlib.sha256(binary).hexdigest()
 with factory.connect() as c:
  known=c.execute("""SELECT l.locator FROM source s JOIN location l ON l.source_id=s.id
    WHERE s.original_sha256=? AND l.provider='LOCAL_FILE' ORDER BY l.locator""",(digest,)).fetchall()
  found=None
  for x in known:
   p=Path(x["locator"])
   if p.is_file() and p.resolve().is_relative_to(WAREHOUSE.resolve()) and hash_file(p)==digest:
    found=p;break
  fresh=found is None
  if fresh:
   name=unicodedata.normalize("NFC",item["file_name"])
   # Use ID in the path to avoid accidental title/Drive duplicate collision.
   folder=WAREHOUSE/item["category"]/"DRIVE_ORIGINALS"/item["account"]
   folder.mkdir(parents=True,exist_ok=True)
   target=folder/(item["drive_id"]+"__"+name)
   if target.exists():
    if hash_file(target)!=digest:raise RuntimeError("DRIVE_TARGET_NAME_COLLISION")
   else:
    tmp=target.with_name(target.name+".capture.tmp")
    try:
     with tmp.open("wb") as out:
      out.write(binary)
      out.flush()
      os.fsync(out.fileno())
     if hash_file(tmp)!=digest:raise RuntimeError("DRIVE_CAPTURE_WRITE_HASH_MISMATCH")
     os.replace(tmp,target)
    finally:tmp.unlink(missing_ok=True)
  else:target=found
  category=item["category"]
  native_export=bool(item.get("native_export"))
  meta={"origin":"GOOGLE_DRIVE_NATIVE_TEXT_EXPORT" if native_export else "GOOGLE_DRIVE_VERIFIED_FETCH","cloud_file_id":item["drive_id"],
   "source_account":item["account"],"file_name":item["file_name"],
   "original_drive_title":item.get("source_title",item["file_name"]),
   "capture_sha256":digest,"content_verified":True,
   "reviewed":False,"approval":False,"category":category}
  pre_existing_source=bool(c.execute("SELECT 1 FROM source WHERE id=?",("raw:"+digest,)).fetchone())
  source_id=factory.register(c,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",str(target),
   target.name,"REFERENCE_UNREVIEWED",sha=digest,size=len(binary),
   modified=str(target.stat().st_mtime_ns),meta=meta)
  drive_id=factory.register(c,"GOOGLE_DRIVE",item["account"],item["drive_id"],
   item["file_name"],"REFERENCE_NATIVE_EXPORT_PENDING_REVIEW" if native_export else "REFERENCE_ORIGINAL_CAPTURED",sha=digest,size=len(binary),meta=meta)
  if drive_id!=source_id:raise RuntimeError("DRIVE_SOURCE_ID_CONFLICT")
  if not pre_existing_source:
   for phase,status in (("EXTRACT","PENDING"),("REVIEW","WAITING_CONTENT_REVIEW"),
     ("FORMING","BLOCKED_UNREVIEWED"),("LEARNING","BLOCKED_UNREVIEWED"),("CONSUME","BLOCKED_NOT_APPROVED")):
    factory.put_stage(c,source_id,phase,status,{"raw_sha256":digest,"provenance":"HNS" if item["account"]=="HNS" else "SIEZEALL"})
  factory.event(c,source_id,"DRIVE_RAW_CENTRALIZED",{
   "origin_account":item["account"],"file_id":item["drive_id"],
   "original_local_bytes":str(target),"hash":digest,
   "dedupe_reused_existing_original":not fresh})
  receipt={"account":item["account"],"file_id":item["drive_id"],
   "original_title":item["file_name"],"source_id":source_id,
   "physical_canonical":str(target),"size_bytes":len(binary),
   "sha256":digest,"new_physical_copy_created":fresh,
   "state":"NATIVE_TEXT_EXPORT_VERIFIED_REVIEW_PENDING" if native_export else "ORIGINAL_BYTES_VERIFIED_REVIEW_PENDING"}
 # Temporary base64 transport is deleted ONLY after physical original bytes
 # + provenance rows commit and both can be reread.
 if hash_file(target)!=digest:raise RuntimeError("DRIVE_CANONICAL_VERIFY_FAILED")
 staged.unlink()
 return receipt
def main():
 results=[]
 for item in ITEMS:
  results.append(original(item))
 report={"schema":"TAKY_DRIVE_ORIGINAL_RAW_CAPTURE_V1",
  "status":"3_ORIGINALS_VERIFIED","results":results,
  "cloud_files_moved_or_deleted":0,"user_data_acquired":False,
  "forminglearning_auto_approved":False}
 RECEIPT.parent.mkdir(parents=True,exist_ok=True)
 RECEIPT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"files":len(results),
  "total_bytes":sum(x["size_bytes"] for x in results),
  "physical_files":[x["physical_canonical"] for x in results],
  "source_ids":[x["source_id"] for x in results]},ensure_ascii=False))
if __name__=="__main__":main()
