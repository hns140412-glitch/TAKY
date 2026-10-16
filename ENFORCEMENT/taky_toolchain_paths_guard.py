"""Read-only TAKY tool/skills/path gate. No secret values reported."""
from __future__ import annotations
import json,os,shutil,subprocess,tomllib
from pathlib import Path
ROOT=Path("D:/Git PWA");TAKY=ROOT/"TAKY";WB=ROOT/"TAKY_AI_WORKBENCH";V=ROOT/"TAKY-SOURCE-VAULT"
ORCH=TAKY/".local"/"TAKY-2.0-ORCH"
OUT=WB/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_TOOLCHAIN_PATHS_GUARD_20261013.json"
PROJECTS=("TAKY","Ready & Set","Hide & Seek","Snap & Pop","Play Camp",
          "SAVEY","TAKY-MOBILE","TAKY-ASSETS","TAKY_ARCHI GROW")
def main():
 checks={};broken=[]
 def check(name,path):
  ok=Path(path).exists()
  checks[name]=bool(ok)
  if not ok:broken.append(name)
 check("raw_separate_root",V)
 check("runtime_collector",V/"RUN_LOCAL_COLLECTOR_12H_HIDDEN.vbs")
 check("site_watch",V/"RUN_SITE_WATCH_HIDDEN.vbs")
 check("notion_schedule",V/"RUN_NOTION_INCREMENTAL_SCHEDULED.ps1")
 check("orchestrator_actual_worktree",ORCH)
 check("ready_real_worktree",ROOT/"Ready & Set")
 check("play_camp_consumer",ROOT/"Play Camp"/"src"/"data"/"supplyCandidate.ts")
 for name in PROJECTS:check("repo:"+name,ROOT/name/".git")
 config_sources={
  "claude_user":Path.home()/".claude"/"settings.json",
  "codex_user":Path.home()/".codex"/"config.toml",
  "claude_desktop":Path(os.environ.get("APPDATA",""))/"Claude"/"claude_desktop_config.json",
  "project_workspace":ROOT/"TAKY_PROJECTS.code-workspace",
 }
 plugin_summary={}
 for key,f in config_sources.items():
  if not f.is_file():
   plugin_summary[key]={"present":False}
   continue
  try:
   data=tomllib.loads(f.read_text(encoding="utf-8-sig")) if f.suffix==".toml" else json.loads(f.read_text(encoding="utf-8-sig"))
  except Exception as e:
   broken.append("INVALID_CONFIG:"+key)
   plugin_summary[key]={"present":True,"parse_ok":False,"error":type(e).__name__}
   continue
  desc={"present":True,"parse_ok":True}
  if key=="codex_user":
   servers=data.get("mcp_servers",{})
   desc["server_count"]=len(servers) if isinstance(servers,dict) else 0
   desc["server_names"]=sorted(servers) if isinstance(servers,dict) else []
  elif key=="claude_desktop":
   servers=data.get("mcpServers",{})
   desc["server_count"]=len(servers) if isinstance(servers,dict) else 0
   desc["server_names"]=sorted(servers) if isinstance(servers,dict) else []
  elif key=="claude_user":
   desc["hooks_present"]=bool(data.get("hooks"))
   desc["enabled_plugin_count"]=len(data.get("enabledPlugins",{}))
  elif key=="project_workspace":
   paths=[x.get("path") for x in data.get("folders",[]) if isinstance(x,dict) and x.get("path")]
   desc["projects"]=len(paths)
   missing=[n for n in paths if not (ROOT/n).is_dir()]
   desc["missing_projects"]=missing
   if missing:broken.append("WORKSPACE_PROJECTS_MISSING")
  plugin_summary[key]=desc
 skill_roots=[
  ORCH/".agents"/"skills",ORCH/".claude"/"skills",
  TAKY/".agents"/"skills",TAKY/".claude"/"skills"
 ]
 skills=[]
 for root in skill_roots:
  if not root.is_dir():continue
  for x in sorted(root.iterdir()):
   if x.is_dir():
    ok=(x/"SKILL.md").is_file()
    skills.append({"root":root.as_posix(),"skill":x.name,"readable":ok,
                   "junction":x.is_junction() if hasattr(x,"is_junction") else False})
    if not ok:broken.append("SKILL_TARGET_UNREADABLE:"+x.name)
 report={"schema":"TAKY_TOOLCHAIN_PATHS_GUARD_V1","checks":checks,
         "settings":plugin_summary,"skills":skills,
         "broken":sorted(set(broken)),"status":"PASS" if not broken else "HOLD",
         "read_only":True,"credential_values_accessed":False,"files_moved":False}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"checked_paths":len(checks),
                   "unreadable_skill_targets":sum(not s["readable"] for s in skills),
                   "skills":len(skills),"broken":report["broken"],
                   "settings":plugin_summary,"report":str(OUT)},ensure_ascii=False))
if __name__=="__main__":main()
