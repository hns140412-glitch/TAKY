"""Single physical reference source, many semantic consumers. Windows D: only.

Canonical: TAKY_AI_WORKBENCH/REFERENCE
Compatibility junctions: TAKY/REFERENCE and TAKY_ARCHI GROW/REFERENCE.
Generated examples remain labelled derived; never promote to immutable RAW.
No data duplication, delete, Git branch operation, cloud or deployment.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path(r"D:\Git PWA")
SOURCE=R/"TAKY_ARCHI GROW"/"REFERENCE"
TARGET=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
LEGACY=R/"TAKY"/"REFERENCE"
WB=R/"TAKY_AI_WORKBENCH"
PREP=WB/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"CENTRAL_REFERENCE_REHOME_PREFLIGHT_20261013.json"
RECEIPT=WB/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"CENTRAL_REFERENCE_REHOME_RECEIPT_20261013.json"
INDEX=WB/"00_CONTROL"/"TAKY_REFERENCE_UNIVERSE_INDEX.json"
ORIGINAL_COUNT=221

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(262144),b""):h.update(b)
 return h.hexdigest()

def all_files(p):
 if not p.is_dir():raise RuntimeError("REFERENCE_SOURCE_FOLDER_MISSING:"+str(p))
 records={}
 for root_item in sorted(p.iterdir()):
  if root_item.is_file():
   records[root_item.name]=sha(root_item)
  elif root_item.name in ("ARCHCOMP_OUTPUT_BUILD_TEST","CLAUDE_SKILLS"):
   for f in root_item.rglob("*"):
    if f.is_file():
     if f.is_symlink():raise RuntimeError("LEGACY_FILE_SYMLINK_UNREVIEWED")
     records[f.relative_to(p).as_posix()]=sha(f)
 # WEB_SOURCE_ARCHIVE is a compatibility directory of links; the actual 9,094
 # captured files are physically sorted inside WORKBENCH domain buckets.
 # WORKBENCH/REFERENCE/99_CONTROL is metadata, not an original reference.
 if len(records)!=ORIGINAL_COUNT:raise RuntimeError("LEGACY_221_REFERENCE_FILESET_DRIFT:"+str(len(records)))
 return records

def junction(p):
 return p.is_dir() and bool(os.lstat(p).st_file_attributes & 0x400)

def ensure_same_alias(p):
 if p.is_dir():
  if not junction(p) or not os.path.samefile(p,TARGET):
   raise RuntimeError("ALIAS_CONFLICT_OR_UNSAFE_NONJUNCTION:"+str(p))
  return
 if p.exists():raise RuntimeError("ALIAS_PATH_EXISTS_NOT_DIR:"+str(p))
 out=subprocess.run(["cmd.exe","/c","mklink","/J",str(p),str(TARGET)],
   capture_output=True,text=True,errors="replace",timeout=12)
 if out.returncode or not p.is_dir() or not os.path.samefile(p,TARGET):
  raise RuntimeError("REFERENCE_ALIAS_CREATE_FAILED:"+str(p)+":"+out.stderr[-200:])

def write_json_atomic(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+".tmp")
 temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 os.replace(temp,p)

def physical_category_path(rel):
 if rel.startswith("ARCHCOMP_OUTPUT_BUILD_TEST/"):
  return TARGET/"90_DERIVED"/rel
 if rel.startswith("CLAUDE_SKILLS/"):
  return TARGET/"30_AI_TECH"/rel
 return TARGET/"20_ARCHITECTURE"/"PROJECT_RECORDS"/rel

def index_for(records):
 items=[]
 source_by_digest={}
 grouped={}
 for rel,digest in sorted(records.items()):
  source_by_digest.setdefault(digest,rel)
  grouped.setdefault(digest,[]).append(rel)
 for rel,digest in sorted(records.items()):
  group="DERIVED_EXAMPLE" if rel.startswith("ARCHCOMP_OUTPUT_BUILD_TEST/") else (
    "TOOL_REFERENCE" if rel.startswith("CLAUDE_SKILLS/") else "REFERENCE_CANDIDATE")
  principal=source_by_digest[digest]
  items.append({
   "source_id":"TAKY_REF_"+digest[:24],
   "canonical_path":str(physical_category_path(principal)),
   "physical_path":str(physical_category_path(rel)),
   "relative_path":rel,"sha256":digest,"role":group,
   "duplicate_content_alias_of":principal if rel!=principal else None,
   "project_consumers":["TAKY_ARCHI GROW"],
   "approval_state":"NOT_INFERRED_FROM_FILENAME_OR_LOCATION",
   "source_authority":"SINGLE_PHYSICAL_REFERENCE_FOLDER",
   "raw_source_evidence":"NOT_AUTO_ELEVATED",
  })
 duplicates=[{"sha256":key,"primary_path":source_by_digest[key],"paths":values}
   for key,values in sorted(grouped.items()) if len(values)>1]
 return {
  "schema":"TAKY_GLOBAL_REFERENCE_UNIVERSE_INDEX_V1",
  "authority":"TAKY_AI_WORKBENCH/REFERENCE single physical reference warehouse; SOURCE-VAULT is a pipeline worker",
  "single_physical_root":str(TARGET),
  "aliases":[str(SOURCE),str(LEGACY),str(R/"TAKY-SOURCE-VAULT"/"REFERENCE")],
  "index_role":"DERIVED_REBUILDABLE_NOT_SECOND_ORIGINAL",
  "file_count":len(items),"unique_content_count":len(grouped),
  "duplicate_content_groups":len(duplicates),
  "duplicate_extra_paths":sum(len(g["paths"])-1 for g in duplicates),
  "duplicate_evidence":duplicates,
  "deduplication_policy":"SEMANTIC_SHA_GROUP_ONLY__KEEP_FILE_PATHS_TO_PRESERVE_BUILD_REFERENCES",
  "items":items,"duplicate_physical_copies_created_by_rehome":0,
  "cross_domain_indexing":"ONE_INDEX_MULTI_CONSUMER_NO_PROJECT_REFERENCE_DUPLICATION"
 }

def baseline():
 if not SOURCE.is_dir():raise RuntimeError("ARCHI_REFERENCE_SOURCE_MISSING")
 tracked=subprocess.run(["git","-C",str(R/"TAKY_ARCHI GROW"),"ls-files","--","REFERENCE"],
  capture_output=True,text=True,encoding="utf-8",timeout=15,check=True).stdout.strip()
 if tracked:raise RuntimeError("GIT_TRACKED_REFERENCE_REFUSE_MOVE")
 if not LEGACY.is_dir() or not junction(LEGACY) or not os.path.samefile(LEGACY,SOURCE):
  raise RuntimeError("EXISTING_LEGACY_REFERENCE_ALIAS_DRIFT")
 if TARGET.exists():raise RuntimeError("TARGET_ALREADY_EXISTS")
 if junction(SOURCE):raise RuntimeError("SOURCE_NOT_PHYSICAL_DIRECTORY")
 records=all_files(SOURCE)
 if len(records)!=ORIGINAL_COUNT:raise RuntimeError("REFERENCE_COUNT_CHANGED:"+str(len(records)))
 return records

def check_applied():
 if not TARGET.is_dir() or not all(p.is_dir() for p in (SOURCE,LEGACY)):
  raise RuntimeError("CENTRAL_REFERENCE_FOLDER_OR_ALIAS_MISSING")
 for p in (SOURCE,LEGACY):
  if not junction(p) or not os.path.samefile(p,TARGET):
   raise RuntimeError("REFERENCE_ALIAS_NOT_CENTRAL:"+str(p))
 if not RECEIPT.is_file() or not INDEX.is_file():
  raise RuntimeError("CENTRAL_REFERENCE_RECEIPT_OR_INDEX_MISSING")
 data=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 actual=all_files(TARGET)
 if data.get("file_sha256")!=actual or len(actual)!=ORIGINAL_COUNT:
  raise RuntimeError("CENTRAL_REFERENCE_SOURCE_BYTES_CHANGED")
 indexed=json.loads(INDEX.read_text(encoding="utf-8-sig"))
 if indexed!=index_for(actual):raise RuntimeError("CENTRAL_REFERENCE_INDEX_DRIFT")
 return {"status":"SINGLE_CANONICAL_PHYSICAL_REFERENCE_VERIFIED","files":len(actual),"aliases":2}

def execute():
 if TARGET.exists():
  return check_applied()
 originals=baseline()
 write_json_atomic(PREP,{"preflight":"HASHED_PRE_MOVE",
   "source":str(SOURCE),"target":str(TARGET),
   "old_legacy":str(LEGACY),"file_sha256":originals,
   "will_not_relocate_collector_raw":True})
 os.rename(SOURCE,TARGET)
 try:
  ensure_same_alias(SOURCE)
  if not LEGACY.is_dir() or not junction(LEGACY):
   raise RuntimeError("LEGACY_ALIAS_LOST_DURING_MOVE")
  # Rebind legacy path directly to the central store instead of an alias chain.
  os.rmdir(LEGACY)  # Windows junction only; never follows to delete target.
  ensure_same_alias(LEGACY)
  if all_files(TARGET)!=originals or all_files(SOURCE)!=originals or all_files(LEGACY)!=originals:
   raise RuntimeError("CENTRAL_REFERENCE_POST_MOVE_HASH_MISMATCH")
  write_json_atomic(INDEX,index_for(originals))
  write_json_atomic(RECEIPT,{"status":"SINGLE_PHYSICAL_CENTRAL_REFERENCE_REHOMED",
   "canonical_reference_root":str(TARGET),"consumer_aliases":[str(SOURCE),str(LEGACY)],
   "file_sha256":originals,"file_count":len(originals),
   "git_files_modified":0,"collector_raw_files_moved":0,
   "duplicate_physical_copies":0,"cloud_modified":False})
  return check_applied()
 except BaseException:
  # Do not remove the 221 real files. Leave a precise recoverable error.
  # If the original directory is now a junction, the canonical bytes are at TARGET.
  raise

def refresh_index():
 if not RECEIPT.is_file() or not TARGET.is_dir():
  raise RuntimeError("CENTRAL_REFERENCE_RECEIPT_OR_ORIGINAL_MISSING")
 meta=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 records=all_files(TARGET)
 if records!=meta.get("file_sha256"):
  raise RuntimeError("CENTRAL_REFERENCE_BYTES_CHANGED_REFUSE_REINDEX")
 for p in (SOURCE,LEGACY):
  if not p.is_dir() or not junction(p) or not os.path.samefile(p,TARGET):
   raise RuntimeError("REFERENCE_CONSUMER_ALIAS_DRIFT")
 write_json_atomic(INDEX,index_for(records))
 return check_applied()

def recover_interrupted():
 if not TARGET.is_dir() or not PREP.is_file():
  raise RuntimeError("NO_VERIFIABLE_INCOMPLETE_REHOME")
 plan=json.loads(PREP.read_text(encoding="utf-8-sig"))
 records=all_files(TARGET)
 if records!=plan.get("file_sha256"):raise RuntimeError("RECOVERY_SOURCE_HASH_MISMATCH")
 for p in (SOURCE,LEGACY):
  if p.is_dir() and junction(p) and not os.path.samefile(p,TARGET):
   os.rmdir(p)
  ensure_same_alias(p)
 write_json_atomic(INDEX,index_for(records))
 write_json_atomic(RECEIPT,{"status":"SINGLE_PHYSICAL_CENTRAL_REFERENCE_REHOMED",
  "canonical_reference_root":str(TARGET),"consumer_aliases":[str(SOURCE),str(LEGACY)],
  "file_sha256":records,"file_count":len(records),
  "git_files_modified":0,"collector_raw_files_moved":0,
  "duplicate_physical_copies":0,"cloud_modified":False,"recovered_after_interruption":True})
 return check_applied()

if __name__=="__main__":
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 g.add_argument("--recover",action="store_true")
 g.add_argument("--refresh-index",action="store_true")
 a=p.parse_args()
 if a.refresh_index:r=refresh_index()
 elif a.recover:r=recover_interrupted()
 elif a.apply:r=execute()
 elif TARGET.exists():r=check_applied()
 else:
  files=baseline()
  r={"status":"READY_TO_CENTRALIZE","files":len(files),
     "source":str(SOURCE),"destination":str(TARGET)}
 print(json.dumps(r,ensure_ascii=False))
