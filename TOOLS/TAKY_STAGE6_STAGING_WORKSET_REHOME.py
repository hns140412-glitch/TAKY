"""TAKY staging root cleanup: archived 2026-10-08 to 10-10 workset only.

Never move active 2026-10-12 crew voice, any staging subfolder/junction,
Git-tracked files, RAW, or application code. --audit and --apply.
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
BASE=Path(r"D:\Git PWA")
ROOT=BASE/"TAKY"
SRC=ROOT/"staging"
DEST=BASE/"TAKY_AI_WORKBENCH"/"90_ARCHIVE"/"TAKY_STAGING_REF095_096_WORKSET_20261008_10"
MAP=BASE/"TAKY_AI_WORKBENCH"/"00_CONTROL"/"TAKY_LEGACY_STAGING_PATH_MAP_20261013.json"
RECEIPT=BASE/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_STAGE6_STAGING_WORKSET_RELOCATION_20261013.json"
FILES=set("""
bind_v34_source_drive_id.py
build_ref095_mining_and_v34.py
close_s3_remote_drive_ingress_20261009.py
crew_voice_20261010_execution.json
DATA_SOURCE_INDEX_2026-10-04_V11.drive.json
DATA_SOURCE_INDEX_2026-10-08_V12.json
DATA_UTILIZATION_INDEX_2026-10-04_V31.drive.json
DATA_UTILIZATION_INDEX_2026-10-08_V34.json
execute_ref095_intake.py
execute_ref096_remote_drive_intake.py
finalize_ref095_e2e_receipts.py
fold_full_indices_v12_v34.py
inspect_delta_shapes.py
inspect_drivefs_upload.py
inspect_full_index_headers.py
inspect_ref087_095_ledger.py
inspect_ref095_upstream.py
inspect_v11_v31.py
migrate_v32_reference_ledger.py
patch_ai_learning_style_signal_rule.py
patch_ai_learning_style_signal_test.py
patch_drive_storage_validator_remote_primary.py
patch_remote_drive_ingress_authority_20261009.py
patch_v32_migration_intent.py
readback_ref095_final.py
readback_ref095.py
REF095_READBACK_20261008.json
register_safeexec_rule.py
update_s3_real_ingress_blocker.py
""".strip().splitlines())
EXPECTED_ACTIVE={"crew_voice_20261012","crew_voice_20261010","content_supply_p0"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as inp:
  for b in iter(lambda:inp.read(262144),b""):h.update(b)
 return h.hexdigest()
def scan():
 if not SRC.is_dir():raise RuntimeError("STAGING_ROOT_MISSING")
 active={p.name for p in SRC.iterdir() if p.is_dir()}
 if active!=EXPECTED_ACTIVE:raise RuntimeError("ACTIVE_STAGING_LAYOUT_CHANGED:"+repr(active))
 names={p.name for p in SRC.iterdir() if p.is_file() and not p.is_dir()}
 remain=names & FILES
 if names-FILES:raise RuntimeError("UNREVIEWED_ROOT_FILES:"+repr(sorted(names-FILES)))
 if remain and DEST.exists():raise RuntimeError("DESTINATION_EXISTS_BEFORE_FULL_MOVE")
 if remain and remain!=FILES:raise RuntimeError("SOURCE_PARTIAL_SET:"+repr(sorted(FILES-remain)))
 if not remain:
  if not DEST.is_dir():raise RuntimeError("STAGING_FILES_LOST")
  actual={p.name for p in DEST.iterdir() if p.is_file()}
  if actual!=FILES:raise RuntimeError("RELOCATED_FILE_SET_MISMATCH")
  if not RECEIPT.is_file() or not MAP.is_file():raise RuntimeError("RELOCATION_METADATA_MISSING")
  saved=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
  if saved.get("status")!="REHOMED_SHA_VERIFIED":raise RuntimeError("RELOCATION_RECEIPT_UNCONFIRMED")
  if {x["filename"]:x["sha256"] for x in saved["files"]}!={p.name:sha(p) for p in DEST.iterdir() if p.is_file()}:
   raise RuntimeError("ARCHIVED_BYTES_DRIFT")
  return {"status":"ALREADY_REHOMED","files":len(FILES),"active_dirs":sorted(active)}
 if subprocess.run(["git","-C",str(ROOT),"ls-files","--","staging"],capture_output=True,text=True,timeout=15,check=True).stdout.strip():
  raise RuntimeError("SOURCE_FILES_GIT_TRACKED")
 items=[{"filename":n,"old_path":str(SRC/n),"new_path":str(DEST/n),
        "sha256":sha(SRC/n),"bytes":(SRC/n).stat().st_size,
        "status":"RETIRED_WORKSET_NOT_ACTIVE_EXECUTOR"} for n in sorted(FILES)]
 return {"status":"READY_TO_REHOME","files":items,"active_dirs":sorted(active)}
def apply():
 plan=scan()
 if plan["status"]=="ALREADY_REHOMED":return plan
 entries=plan["files"]
 if len(entries)!=29:raise RuntimeError("REVIEWED_29_FILE_SET_REQUIRED")
 DEST.mkdir(parents=True,exist_ok=False)
 moved=[]
 try:
  for x in entries:
   src=Path(x["old_path"]); dst=Path(x["new_path"])
   os.replace(src,dst)
   moved.append(x)
   if sha(dst)!=x["sha256"]:raise RuntimeError("SHA_MISMATCH:"+x["filename"])
  if list(p for p in SRC.iterdir() if p.is_file()):
   raise RuntimeError("STAGING_ROOT_FILES_REMAIN")
  if {p.name for p in SRC.iterdir() if p.is_dir()}!=EXPECTED_ACTIVE:
   raise RuntimeError("ACTIVE_STAGING_DIRECTORY_CHANGED")
  mapping={"schema":"TAKY_LEGACY_STAGING_PATH_MAP_V1","version":"2026-10-13",
   "old_directory":str(SRC),"new_archive":str(DEST),
   "use_new_paths_for_historical_lookup_only":True,
   "rerun_legacy_mutating_scripts":False,
   "active_directories_unchanged":sorted(EXPECTED_ACTIVE),
   "paths":{x["old_path"]:x["new_path"] for x in entries}}
  result={"schema":"TAKY_STAGE6_RELOCATION_RECEIPT_V1",
   "status":"REHOMED_SHA_VERIFIED","files":entries,
   "file_count":len(entries),"sum_bytes":sum(x["bytes"] for x in entries),
   "historical_scripts_read_only_by_policy":True,
   "active_voice_directory_moved":False,"active_collector_directory_moved":False,
   "git_branches_moved":False,"cloud_modified":False,
   "rollback_command":"python \"D:/Git PWA/TAKY/TOOLS/TAKY_STAGE6_STAGING_WORKSET_REHOME.py\" --rollback"}
  # Metadata is written only after all 29 bytes and active folder checks.
  for path,data in ((MAP,mapping),(RECEIPT,result)):
   path.parent.mkdir(parents=True,exist_ok=True)
   tmp=path.with_name(path.name+".stage6.tmp")
   tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
   os.replace(tmp,path)
  return {"status":result["status"],"moved":len(entries),"bytes":result["sum_bytes"],"mapping":str(MAP),"receipt":str(RECEIPT)}
 except BaseException:
  for x in reversed(moved):
   old=Path(x["old_path"]);new=Path(x["new_path"])
   if new.is_file() and not old.exists():os.replace(new,old)
  if DEST.exists() and not any(DEST.iterdir()):DEST.rmdir()
  raise
def rollback():
 if not RECEIPT.is_file() or not MAP.is_file():raise RuntimeError("NO_RECEIPT_FOR_ROLLBACK")
 result=json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
 if result.get("status")!="REHOMED_SHA_VERIFIED":raise RuntimeError("ROLLBACK_REFUSES_NON_VERIFIED_RECEIPT")
 files=result["files"]
 if any(Path(x["old_path"]).exists() or not Path(x["new_path"]).is_file() or sha(Path(x["new_path"]))!=x["sha256"] for x in files):
  raise RuntimeError("ROLLBACK_CONFLICT_OR_DATA_DRIFT")
 for x in files:os.replace(x["new_path"],x["old_path"])
 if DEST.exists() and not any(DEST.iterdir()):DEST.rmdir()
 RECEIPT.rename(RECEIPT.with_suffix(".json.rolled_back"))
 MAP.rename(MAP.with_suffix(".json.rolled_back"))
 return {"status":"ROLLED_BACK","files":len(files)}
if __name__=="__main__":
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true");g.add_argument("--apply",action="store_true");g.add_argument("--rollback",action="store_true")
 args=p.parse_args()
 print(json.dumps(rollback() if args.rollback else apply() if args.apply else scan(),ensure_ascii=False,indent=2 if args.audit else None))
