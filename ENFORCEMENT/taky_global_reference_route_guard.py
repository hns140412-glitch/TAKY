"""Validate single physical reference authority across TAKY projects.

Does not move app runtime data, physical RAW collector sources or modify folders.
"""
from pathlib import Path
import json,os,subprocess,sys
BASE=Path("D:/Git PWA")
TAKY=BASE/"TAKY"
CANON=BASE/"TAKY_AI_WORKBENCH"/"REFERENCE"
ALIAS={
 "TAKY":BASE/"TAKY"/"REFERENCE",
 "TAKY_ARCHI_GROW":BASE/"TAKY_ARCHI GROW"/"REFERENCE",
 "SOURCE_VAULT_PIPELINE_COMPAT":BASE/"TAKY-SOURCE-VAULT"/"REFERENCE"
}
PROJECTS=("Ready & Set","Hide & Seek","Snap & Pop","Play Camp",
          "SAVEY","TAKY-MOBILE","TAKY-ASSETS","TAKY_ARCHI GROW","TAKY")
INDEX=BASE/"TAKY_AI_WORKBENCH"/"00_CONTROL"/"TAKY_REFERENCE_UNIVERSE_INDEX.json"
VAULT=BASE/"TAKY-SOURCE-VAULT"
WB=BASE/"TAKY_AI_WORKBENCH"
SOURCE_VAULT_REHOME_ROUTES={
 "RUNTIME/TAKY_TMP/TOEFL_PRIMARY_20261008":"REFERENCE/10_LEARNING/TOEFL/WORKING_AUDIO_20261008",
 "data/source_universe":"REFERENCE/99_CONTROL/SOURCE_UNIVERSE",
 "data/source_acquisition/deep_original":"REFERENCE/80_UNCLASSIFIED/DEEP_ORIGINAL_ACQUIRED",
 "data/source_acquisition/guide_catalog":"REFERENCE/90_DERIVED/GUIDE_CATALOG",
 "data/source_acquisition/http_recovery_pilot":"REFERENCE/90_DERIVED/HTTP_RECOVERY_PILOT",
 "reports/LOCAL_AUDIT":"90_ARCHIVE/TAKY_LOCAL_AUDIT_HISTORY",
 "TOOLS/TAKY_AI_WORKBENCH":"90_ARCHIVE/LEGACY_STANDALONE_WORKBENCH_20260929",
 "exports/NOTION_COLLECTOR_CODE_AUDIT_20261005":"90_ARCHIVE/NOTION_COLLECTOR_CODE_AUDIT_20261005",
 "data/direction_intake":"REFERENCE/00_INBOX/DIRECTION_INTAKE",
 "data/external_raw":"REFERENCE/00_INBOX/EXTERNAL_RAW",
 "data/mining_discovery_intake_inputs":"REFERENCE/00_INBOX/DISCOVERY_INTAKE",
 "data/mining_manual_intake_inputs":"REFERENCE/00_INBOX/MANUAL_INTAKE",
 "data/notion_incremental":"REFERENCE/00_INBOX/NOTION_INCREMENTAL",
 "data/play_camp_gap_inputs":"REFERENCE/10_LEARNING/PLAY_CAMP_INPUTS",
 "data/reference_inbox":"REFERENCE/00_INBOX/REFERENCE_INBOX",
 "data/reference_intake":"REFERENCE/00_INBOX/REFERENCE_INTAKE",
 "data/remote_drive_inbox":"REFERENCE/00_INBOX/DRIVE_INBOX",
 "data/visual_evidence":"REFERENCE/40_DESIGN_MEDIA/VISUAL_EVIDENCE"
}
def audit():
 failures=[]
 if not CANON.is_dir():failures.append("CANONICAL_REFERENCE_ROOT_MISSING")
 for name,p in ALIAS.items():
  if not p.is_dir() or not bool(os.lstat(p).st_file_attributes & 0x400) or not os.path.samefile(p,CANON):
   failures.append("DUPLICATED_OR_BROKEN_PROJECT_REFERENCE:"+name)
 unexpected=[]
 for proj in PROJECTS:
  root=BASE/proj
  if not root.is_dir():continue
  for name in ("REFERENCE","REFERENCES"):
   p=root/name
   if p.exists() and p not in ALIAS.values():
    if not p.is_dir() or not os.path.samefile(p,CANON):
     unexpected.append(str(p))
 if unexpected:failures.append("SEPARATE_REFERENCE_ROOTS_PRESENT")
 for original,target in SOURCE_VAULT_REHOME_ROUTES.items():
  previous=VAULT/original
  canonical=WB/target
  if not previous.is_dir() or not canonical.is_dir():
   failures.append("REFERENCE_STORAGE_MISSING:"+original)
   continue
  if not previous.is_junction() or not os.path.samefile(previous,canonical):
   failures.append("REFERENCE_DATA_REAPPEARED_OUTSIDE_WORKBENCH:"+original)
 # The 3+ GB local voice runtime is a tool dependency, not reference RAW.
 if not (VAULT/"RUNTIME"/"TAKY_LOCAL_VOICE"/"venv").is_dir():
  failures.append("VOICE_EXECUTION_ENVIRONMENT_MISSING")
 if not (VAULT/"data"/"source_acquisition"/"runs").is_dir():
  failures.append("ACQUISITION_RUN_STATE_MISSING")
 # Runtime data directories such as Play Camp/reference_captions are not
 # master reference folders and are intentionally left untouched.
 try:
  data=json.loads(INDEX.read_text(encoding="utf-8-sig"))
  if Path(data["single_physical_root"])!=CANON or data["file_count"]!=221:
   failures.append("REFERENCE_GLOBAL_INDEX_AUTHORITY_DRIFT")
  if data["unique_content_count"]+data["duplicate_extra_paths"]!=data["file_count"]:
   failures.append("REFERENCE_SHA_UNIQUENESS_ACCOUNTING_DRIFT")
 except (OSError,ValueError,KeyError):
  failures.append("REFERENCE_GLOBAL_INDEX_MISSING_OR_INVALID")
 return {"status":"PASS" if not failures else "FAIL","canonical":str(CANON),
  "consumer_aliases_verified":len(ALIAS),
  "source_vault_storage_junctions_checked":len(SOURCE_VAULT_REHOME_ROUTES),
  "unexpected_physical_reference_roots":unexpected,
  "app_runtime_asset_directories_untouched":True,
  "failures":failures,"read_only":True}
if __name__=="__main__":
 result=audit()
 print(json.dumps(result,ensure_ascii=False))
 sys.exit(0 if result["status"]=="PASS" else 2)
