"""Physical reference authority migration: SOURCE-VAULT -> TAKY_AI_WORKBENCH.

The old source becomes a directory junction so existing ingestion paths remain
functional. Same D volume, atomic rename, NO 2.3 GB copy, NO Git/Drive writes.
Source-Vault remains the gathering/extraction WORKER, never reference owner.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path(r"D:\Git PWA")
FROM=R/"TAKY-SOURCE-VAULT"/"REFERENCE"
TO=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
OLD_TAKY=R/"TAKY"/"REFERENCE"
OLD_ARCH=R/"TAKY_ARCHI GROW"/"REFERENCE"
OLD_WEB=R/"TAKY_ARCHI GROW"/"SOURCE_ARCHIVE"
OLD_META=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"CENTRAL_REFERENCE_REHOME_RECEIPT_20261013.json"
RECEIPT=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"WORKBENCH_REFERENCE_PHYSICAL_REHOME_20261013.json"
ALIAS_PATHS=(FROM,OLD_TAKY,OLD_ARCH)
def meta(file):
 st=file.stat()
 return (st.st_size,st.st_mtime_ns)
def fast_inventory(root):
 records={}
 for base,dirs,files in os.walk(root):
  dirs[:]=[d for d in dirs if not (Path(base)/d).is_symlink()]
  for name in files:
   p=Path(base)/name
   if p.is_symlink():raise RuntimeError("UNREVIEWED_SYMLINK:"+str(p))
   records[p.relative_to(root).as_posix()]=meta(p)
 return records
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(256*1024),b""):h.update(chunk)
 return h.hexdigest()
def preflight():
 if TO.exists():raise RuntimeError("WORKBENCH_REFERENCE_TARGET_EXISTS")
 if not FROM.is_dir() or FROM.is_symlink() or os.path.isjunction(FROM):
  raise RuntimeError("SOURCE_VAULT_REFERENCE_NOT_PHYSICAL")
 for p in (OLD_TAKY,OLD_ARCH):
  if not p.is_dir() or not os.path.samefile(p,FROM) or not os.path.isjunction(p):
   raise RuntimeError("PREVIOUS_PROJECT_CONSUMER_ALIAS_DRIFT:"+str(p))
 if not OLD_WEB.is_dir() or not os.path.samefile(OLD_WEB,FROM/"WEB_SOURCE_ARCHIVE"):
  raise RuntimeError("OLD_WEB_CAPTURE_ALIAS_DRIFT")
 if not OLD_META.is_file():
  raise RuntimeError("PREVIOUS_REFERENCE_RECEIPT_MISSING")
 previously=json.loads(OLD_META.read_text(encoding="utf-8-sig"))
 if len(previously.get("file_sha256",{}))!=221:
  raise RuntimeError("221_REFERENCE_ORIGINAL_PROVENANCE_MISSING")
 for rel,expected in previously["file_sha256"].items():
  if digest(FROM/rel)!=expected:
   raise RuntimeError("221_REFERENCE_ORIGINAL_HASH_CHANGED:"+rel)
 items=fast_inventory(FROM)
 if len(items)!=9315:
  raise RuntimeError("SOURCE_INVENTORY_CHANGED_REQUIRE_REVIEW:"+str(len(items)))
 total=sum(v[0] for v in items.values())
 if total<2_300_000_000 or total>2_500_000_000:
  raise RuntimeError("WEB_CAPTURE_SIZE_UNEXPECTED:"+str(total))
 web=[k for k in items if k.startswith("WEB_SOURCE_ARCHIVE/")]
 if len(web)!=9094:
  raise RuntimeError("WEB_CAPTURE_FILESET_DRIFT:"+str(len(web)))
 samples=sorted(items)[::max(1,len(items)//20)][:20]
 samples_hashes={k:digest(FROM/k) for k in samples}
 return items,total,samples_hashes
def write_result(data):
 tmp=RECEIPT.with_suffix(".json.pending")
 tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 os.replace(tmp,RECEIPT)
def make_alias(old,target):
 if old.exists():
  if os.path.isjunction(old) and os.path.samefile(old,target):return
  raise RuntimeError("ALIAS_CONFLICT:"+str(old))
 proc=subprocess.run(["cmd.exe","/c","mklink","/J",str(old),str(target)],
  capture_output=True,text=True,errors="replace",timeout=20)
 if proc.returncode or not old.is_dir() or not os.path.samefile(old,target):
  raise RuntimeError("JUNCTION_FAIL:"+str(old)+":"+proc.stderr[-250:])
def verify():
 if not TO.is_dir() or not RECEIPT.is_file():raise RuntimeError("NO_WORKBENCH_CANONICAL_RECEIPT")
 proof=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 for old in ALIAS_PATHS:
  if not old.is_dir() or not os.path.samefile(old,TO):
   raise RuntimeError("BROKEN_CONSUMER_REFERENCE_ALIAS:"+str(old))
 if not os.path.samefile(OLD_WEB,TO/"WEB_SOURCE_ARCHIVE"):
  raise RuntimeError("ARCHIGROW_WEB_ARCHIVE_ALIAS_BROKEN")
 now=fast_inventory(TO)
 if len(now)!=proof["files"] or sum(x[0] for x in now.values())!=proof["total_bytes"]:
  raise RuntimeError("WORKBENCH_REFERENCE_SIZE_OR_COUNT_DRIFT")
 for k,h in proof["sample_sha256"].items():
  if digest(TO/k)!=h:raise RuntimeError("REFERENCE_SAMPLE_HASH_CHANGED:"+k)
 return {"status":"WORKBENCH_REFERENCE_SINGLE_ROOT_VERIFIED","files":len(now),
  "total_bytes":sum(x[0] for x in now.values()),
  "canonical":str(TO),"consumer_aliases":len(ALIAS_PATHS)+1}
def execute():
 if TO.exists():return verify()
 items,total,sample=preflight()
 if FROM.drive.casefold()!=TO.drive.casefold():raise RuntimeError("NOT_SAME_VOLUME")
 os.rename(FROM,TO)
 try:
  make_alias(FROM,TO)
  for p in (OLD_TAKY,OLD_ARCH):
   # They currently point to the former path; they continue through FROM.
   if not p.is_dir() or not os.path.samefile(p,TO):
    raise RuntimeError("LEGACY_PROJECT_ALIAS_DID_NOT_SURVIVE")
  if not OLD_WEB.is_dir() or not os.path.samefile(OLD_WEB,TO/"WEB_SOURCE_ARCHIVE"):
   raise RuntimeError("OLD_WEB_ARCHIVE_REF_DID_NOT_SURVIVE")
  for k,h in sample.items():
   if digest(TO/k)!=h:raise RuntimeError("POSTMOVE_SAMPLE_HASH_MISMATCH:"+k)
  after=fast_inventory(TO)
  if items!=after:raise RuntimeError("POSTMOVE_INVENTORY_OR_MODIFIED_TIME_DRIFT")
  out={"status":"WORKBENCH_PHYSICAL_REFERENCE_REHOMED",
   "former_physical_root":str(FROM),"canonical_root":str(TO),
   "file_count":len(after),"files":len(after),"total_bytes":total,
   "sample_sha256":sample,"legacy_aliases":[str(p) for p in ALIAS_PATHS],
   "legacy_web_alias":str(OLD_WEB),
   "source_vault_role":"INGEST_EXTRACT_INDEX_PIPELINE_ONLY",
   "no_copy_or_drive_mutation":True,"no_automatic_deletion":True,
   "verification":"FULL_METADATA_INVENTORY_AND_20_PREPOST_SHA_SAMPLES_WITH_EXISTING_221_FULL_HASH"}
  write_result(out)
  return verify()
 except Exception:
  # Preserve bytes and allow deterministic recovery: never delete destination.
  if TO.is_dir() and not FROM.exists():os.rename(TO,FROM)
  raise
if __name__=="__main__":
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 args=p.parse_args()
 if args.audit:
  if TO.is_dir():result=verify()
  else:
   items,total,_=preflight()
   result={"status":"READY","files":len(items),"total_bytes":total,"workbench_target":str(TO)}
 else:result=execute()
 print(json.dumps(result,ensure_ascii=False))
