#!/usr/bin/env python3
"""TAKY read-only, concrete local work executors for existing portfolio IDs.

Capture evidence, do not alter source files, settings, registries, Git or cloud.
No LLM inference. Never infer product readiness from passing a local inventory.
"""
from __future__ import annotations
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(r"D:\Git PWA")
TAKY=ROOT/"TAKY"
GUARDS=TAKY/"ENFORCEMENT"
REPOS=("TAKY","Ready & Set","Hide & Seek","Snap & Pop","Play Camp",
       "SAVEY","TAKY-MOBILE","TAKY-ASSETS","TAKY_ARCHI GROW")

def git(args: list[str], repo: Path, timeout: int=18) -> tuple[int,str]:
    try:
        p=subprocess.run(["git","-C",str(repo),*args],capture_output=True,
                         encoding="utf-8",errors="replace",timeout=timeout,check=False)
        return p.returncode,p.stdout.strip()
    except (OSError,subprocess.TimeoutExpired):
        return 2,""

def inventory_worktrees() -> list[dict]:
    rows=[]
    for name in REPOS:
        repo=ROOT/name
        record={"repo":name,"path":str(repo),"exists":repo.is_dir(),
                "git_metadata_present":(repo/".git").exists(),
                "worktrees":[],"head":None,"branch":None,"status":"UNAVAILABLE"}
        if record["git_metadata_present"]:
            code,raw=git(["worktree","list","--porcelain"],repo)
            if code==0:
                for block in raw.split("\n\n"):
                    if not block.strip():continue
                    worktree={}
                    for line in block.splitlines():
                        if line.startswith("worktree "):worktree["path"]=line[9:]
                        elif line.startswith("HEAD "):worktree["head"]=line[5:17]
                        elif line.startswith("branch "):worktree["branch"]=line[7:]
                        elif line.startswith("prunable "):worktree["prunable_reason"]=line[9:]
                        elif line=="locked":worktree["locked"]=True
                    record["worktrees"].append(worktree)
                ec,head=git(["rev-parse","--short=12","HEAD"],repo)
                eb,branch=git(["branch","--show-current"],repo)
                if ec==0:record["head"]=head
                if eb==0:record["branch"]=branch
                record["status"]="OBSERVED"
        rows.append(record)
    return rows

def worktree_inventory(_: int=75) -> list[dict]:
    rows=inventory_worktrees()
    missing=[x["repo"] for x in rows if not x["git_metadata_present"]]
    prunable=[{"repo":x["repo"],"worktree":w.get("path"),"reason":w.get("prunable_reason")}
              for x in rows for w in x["worktrees"] if w.get("prunable_reason")]
    return [{"name":"LOCAL_GIT_WORKTREE_INVENTORY",
             "status":"PASS" if not missing else "HOLD",
             "repo_count":len(rows),"missing_git_roots":missing,
             "prunable_entries":prunable,
             "repositories":rows,
             "no_prune_or_delete":True,
             "done_claim":"INVENTORY_ONLY_EXTERNAL_REFERENCES_AND_DUPLICATE_HASHES_NOT_COMPLETE"}]

def _toolchain_guard(timeout: int=75) -> dict:
    source=GUARDS/"taky_toolchain_paths_guard.py"
    with tempfile.TemporaryDirectory(prefix="TAKY_WORKER_CONFIG_AUDIT_") as td:
        report=Path(td)/"toolchain.json"
        script=("import importlib.util,sys;from pathlib import Path;"
                "spec=importlib.util.spec_from_file_location('taky_catalog_probe',sys.argv[1]);"
                "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
                "m.OUT=Path(sys.argv[2]);m.main()")
        p=subprocess.run([sys.executable,"-B","-X","utf8","-c",script,
                          str(source),str(report)],capture_output=True,text=True,
                         errors="replace",encoding="utf-8",timeout=timeout,check=False)
        if p.returncode not in (0,2) or not report.is_file():
            raise RuntimeError("TOOLCHAIN_CONFIG_OBSERVATION_UNAVAILABLE")
        data=json.loads(report.read_text(encoding="utf-8-sig"))
        if data.get("schema")!="TAKY_TOOLCHAIN_PATHS_GUARD_V1" or data.get("read_only") is not True:
            raise ValueError("TOOLCHAIN_CONFIG_PROOF_INVALID")
        return data

def connected_tool_inventory(timeout: int=75) -> list[dict]:
    data=_toolchain_guard(timeout)
    settings={k:v for k,v in data.get("settings",{}).items()
              if k in ("claude_user","claude_desktop","codex_user")}
    present={k:v for k,v in settings.items() if v.get("present")}
    failures=[k for k,v in settings.items() if v.get("present") and not v.get("parse_ok",False)]
    return [{"name":"MCP_CONFIG_AND_PERMISSION_METADATA_INVENTORY",
             "status":"PASS" if present and not failures else "HOLD",
             "config_source_count":len(settings),"config_sources_present":list(present),
             "client_metadata":settings,
             "invalid_config_sources":failures,
             "authorization_scopes_not_confirmed":True,
             "protocol_handshake_not_performed":True,
             "credential_values_accessed":False,
             "external_calls":False,
             "done_claim":"CONFIG_METADATA_ONLY_NOT_ALL_CONNECTED_PLUGIN_PERMISSIONS"}]

def skill_inventory(timeout: int=75) -> list[dict]:
    data=_toolchain_guard(timeout)
    skills=data.get("skills",[])
    invalid=[{"root":s["root"],"skill":s["skill"]} for s in skills
             if not s.get("readable")]
    return [{"name":"CLAUDE_CODEX_LOCAL_SKILL_CATALOG",
             "status":"PASS" if not invalid else "HOLD",
             "found":len(skills),"skills":skills,
             "invalid_skill_targets":invalid,
             "actual_trigger_runtime_not_tested":True,
             "no_skills_installed_or_updated":True,
             "done_claim":"FILE_MANIFEST_ONLY_NOT_RUNTIME_TRIGGER_COMPATIBILITY"}]

WORKERS={
    "CLN-001":worktree_inventory,
    "MCP-001":connected_tool_inventory,
    "SKL-001":skill_inventory,
}
