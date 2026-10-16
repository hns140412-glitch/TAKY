"""Post-relocation TAKY path/enforcement check; local, bounded, read-only.

This does not validate cloud permissions or move files. It checks physical
path authority, Git worktree registrations, preserved legacy aliases,
critical current app consumer, workspace links, and local collector entrypoints.
"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path

BASE=Path(r"D:\Git PWA")
TAKY=BASE/"TAKY"
WORKBENCH=BASE/"TAKY_AI_WORKBENCH"
VAULT=BASE/"TAKY-SOURCE-VAULT"
REPOS=("TAKY","Ready & Set","Hide & Seek","Snap & Pop","Play Camp",
       "SAVEY","TAKY-MOBILE","TAKY-ASSETS","TAKY_ARCHI GROW")
LINKS={
 "RETIRED_AUDIO_20261010":(
  TAKY/"staging"/"crew_voice_20261010",
  WORKBENCH/"30_AUDIO_STUDIO"/"RECORDING"/"ARCHIVED_CANDIDATES"/"crew_voice_20261010"),
 "BACKUP_EVIDENCE":(
  TAKY/"backup",
  WORKBENCH/"90_ARCHIVE"/"TAKY_LEGACY_BACKUP_20261013"),
 "CONTENT_SUPPLY_P0":(
  TAKY/"staging"/"content_supply_p0",
  WORKBENCH/"50_INTEGRATION_TEST"/"CONTENT_SUPPLY"/"content_supply_p0"),
}
REQUIRED_FILES={
 "CENTRAL_AUTHORITY":TAKY/"CURRENT"/"TAKY_PATH_AUTHORITY.md",
 "WORKBENCH_REGISTRY":WORKBENCH/"00_CONTROL"/"PATH_REGISTRY.json",
 "DRIVE_STORAGE_ID_MAP":TAKY/"OS"/"DRIVE_STORAGE_MAP.json",
 "PLAY_CAMP_SUPPLY_CONSUMER":BASE/"Play Camp"/"src"/"data"/"supplyCandidate.ts",
 "CONTENT_SUPPLY_PRODUCER":TAKY/"ENFORCEMENT"/"content_supply_real_raw_smoke.py",
 "RAW_COLLECTOR_ENTRY":VAULT/"RUN_LOCAL_COLLECTOR_12H_HIDDEN.vbs",
 "SITE_WATCH_ENTRY":VAULT/"RUN_SITE_WATCH_HIDDEN.vbs",
 "NOTION_ENTRY":VAULT/"RUN_NOTION_INCREMENTAL_SCHEDULED.ps1",
 "ACTIVE_CREW_VOICE_PRODUCTION":TAKY/"staging"/"crew_voice_20261012",
 "FAMILY_CURRENT":TAKY/"CURRENT"/"FAMILY_USER_DATA_RUNTIME_CURRENT_2026-10-07.json",
}
def validate(root=BASE):
 errors=[];info={}
 for name in REPOS:
  p=BASE/name
  if not (p/".git").exists():errors.append("MISSING_GIT_ROOT:"+name);continue
  try:
   status=subprocess.run(["git","-C",str(p),"worktree","list","--porcelain"],
    capture_output=True,text=True,encoding="utf-8",errors="replace",
    timeout=15,check=True).stdout
  except (OSError,subprocess.SubprocessError) as e:
   errors.append("GIT_WORKTREE_CHECK_FAILED:"+name+":"+type(e).__name__)
   continue
  if any(line.startswith("prunable ") for line in status.splitlines()):
   errors.append("DANGLING_GIT_WORKTREE:"+name)
 info["git_roots_checked"]=len(REPOS)
 if not VAULT.is_dir() or VAULT.resolve()==TAKY.resolve():
  errors.append("RAW_VAULT_SEPARATE_ROOT_MISSING")
 for name,check in REQUIRED_FILES.items():
  if not check.exists():errors.append("MISSING_"+name)
  if name.endswith("_ENTRY") and not check.is_file():
   errors.append("NOT_A_FILE_"+name)
 for name,(old,new) in LINKS.items():
  if not old.is_dir() or not new.is_dir():
   errors.append("RELOCATION_ALIAS_MISSING:"+name);continue
  if not os.path.samefile(old,new):
   errors.append("RELOCATION_ALIAS_TARGET_MISMATCH:"+name)
  if not old.is_symlink() and not (os.lstat(old).st_file_attributes & 0x400):
   # On Windows a directory junction has REPARSE_POINT even when is_symlink false.
   errors.append("COMPATIBILITY_ALIAS_IS_PHYSICAL_COPY:"+name)
 info["relocation_aliases_checked"]=len(LINKS)
 workspace=BASE/"TAKY_PROJECTS.code-workspace"
 try:
  data=json.loads(workspace.read_text(encoding="utf-8-sig"))
  paths={x["path"] for x in data.get("folders",[]) if "path" in x}
  if "TAKY_AI_WORKBENCH" not in paths:errors.append("WORKBENCH_NOT_IN_SHARED_WORKSPACE")
 except (OSError,ValueError,KeyError,TypeError):
  errors.append("WORKSPACE_CONFIG_INVALID")
 try:
  registry=json.loads((WORKBENCH/"00_CONTROL"/"PATH_REGISTRY.json").read_text(encoding="utf-8-sig"))
  rawpath=registry.get("raw_authority","")
  # CURRENT/TAKY_PATH_AUTHORITY.md: WORKBENCH owns physical references;
  # SOURCE-VAULT remains the collection/transport runtime, not the warehouse.
  if Path(rawpath)!=WORKBENCH/"REFERENCE":errors.append("RAW_SOURCE_AUTHORITY_MISMATCH")
  for key,(_,new) in zip(
   ("archived_crew_audio_20261010","taky_legacy_backups","content_supply_candidate_fixture"),
   LINKS.values()
  ):
   if Path(registry.get(key,""))!=new:
    errors.append("WORKBENCH_REGISTRY_DRIFT:"+key)
  if Path(registry.get("play_camp_candidate_consumer",""))!=REQUIRED_FILES["PLAY_CAMP_SUPPLY_CONSUMER"]:
   errors.append("PLAY_CAMP_CONSUMER_ROUTE_DRIFT")
 except (OSError,ValueError,TypeError) as e:errors.append("WORKBENCH_REGISTRY_INVALID:"+type(e).__name__)
 info["workspace_verified"]=workspace.exists()
 info["source_vault_root_unchanged"]=VAULT.is_dir()
 info["live_voice_work_preserved"]=(TAKY/"staging"/"crew_voice_20261012").is_dir()
 return {"status":"PASS" if not errors else "FAIL","errors":errors,
   "evidence":info,"no_changes_made":True}

if __name__=="__main__":
 result=validate()
 print(json.dumps(result,ensure_ascii=False,indent=2))
 sys.exit(0 if result["status"]=="PASS" else 2)
