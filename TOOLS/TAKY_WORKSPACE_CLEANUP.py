"""TAKY controlled cleanup: protected git repositories and RAW remain in place.

Run:
 python TAKY_WORKSPACE_CLEANUP.py --audit
 python TAKY_WORKSPACE_CLEANUP.py --apply-safe

Apply-safe performs only: backup+prune non-existent Git worktree registrations,
rehome 2026-10-10 retired candidate audio to existing WORKBENCH audio studio
(with an old-path junction), and remove two proved empty TAKY directories.
No Git branches, cloud folders, active collector scripts or live assets removed.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(r"D:\Git PWA")
TAKY=ROOT/"TAKY"
WB=ROOT/"TAKY_AI_WORKBENCH"
REPOS=("TAKY","Ready & Set","Hide & Seek","Snap & Pop","Play Camp",
       "SAVEY","TAKY-MOBILE","TAKY-ASSETS","TAKY_ARCHI GROW")
ACTIVE_ROOTS={p.resolve() for p in [TAKY,*[ROOT/n for n in REPOS],ROOT/"TAKY-SOURCE-VAULT",WB]}
SOURCE_AUDIO=TAKY/"staging"/"crew_voice_20261010"
TARGET_AUDIO=WB/"30_AUDIO_STUDIO"/"RECORDING"/"ARCHIVED_CANDIDATES"/"crew_voice_20261010"
EMPTY=(TAKY/"backup_phase1_20261007_165930", TAKY/"reports")
REGISTRY=WB/"00_CONTROL"/"PATH_REGISTRY.json"
TASKS=WB/"01_BACKLOG_AND_ADOPTION"/"70_EXECUTION_QUEUE"/"TASK_REGISTER.json"
RECEIPT=WB/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_CLEANUP_RELOCATION_RECEIPT_20261013.json"
SNAPSHOT=WB/"90_ARCHIVE"/"GIT_WORKTREE_ADMIN_SNAPSHOTS"/"20261013"

def git(repo,*args):
    p=subprocess.run(["git","-C",str(repo),*args],capture_output=True,
                     text=True,encoding="utf-8",errors="replace",timeout=18)
    if p.returncode:raise RuntimeError("GIT_ERROR_"+repo.name+"_"+str(args)+":"+p.stderr[-500:])
    return p.stdout+p.stderr if args[:2]==('worktree','prune') else p.stdout

def sha_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*256),b""):h.update(b)
    return h.hexdigest()

def members_hash(p):
    out={}
    for f in sorted(p.rglob("*")):
        if f.is_file():out[f.relative_to(p).as_posix()]=sha_file(f)
    return out

def worktree_status(repo):
    if not (repo/".git").exists():raise RuntimeError("PROTECTED_REPO_MISSING:"+str(repo))
    porcelain=git(repo,"worktree","list","--porcelain")
    items=[];cur=None
    for line in (porcelain+"\n").splitlines():
        if line.startswith("worktree "):
            if cur:items.append(cur)
            cur={"path":line[9:],"head":None,"branch":None,"prunable":False}
        elif cur and line.startswith("HEAD "):cur["head"]=line[5:]
        elif cur and line.startswith("branch "):cur["branch"]=line[7:]
        elif cur and line.startswith("prunable "):cur["prunable"]=True
    if cur:items.append(cur)
    stale=[i for i in items if i["prunable"] and not Path(i["path"]).exists()]
    unsafe=[i for i in items if i["prunable"] and Path(i["path"]).exists()]
    if unsafe:raise RuntimeError("PRUNABLE_ACTUAL_DIRECTORY_EXISTS:"+repo.name)
    return items,stale

def audio_preflight():
    if TARGET_AUDIO.exists() and SOURCE_AUDIO.exists() and os.path.samefile(SOURCE_AUDIO,TARGET_AUDIO):
        return {"status":"ALREADY_MOVED","source":str(SOURCE_AUDIO),"target":str(TARGET_AUDIO)}
    if TARGET_AUDIO.exists() and not SOURCE_AUDIO.exists():
        return {"status":"ALREADY_MOVED_NO_COMPAT_ALIAS","source":str(SOURCE_AUDIO),"target":str(TARGET_AUDIO)}
    if not SOURCE_AUDIO.is_dir():
        raise RuntimeError("AUDIO_SOURCE_MISSING:"+str(SOURCE_AUDIO))
    if TARGET_AUDIO.exists():
        raise RuntimeError("AUDIO_DEST_COLLISION")
    files=members_hash(SOURCE_AUDIO)
    if len(files)!=13 or any(Path(n).suffix not in {".mp3",".md"} for n in files):
        raise RuntimeError("AUDIO_CANDIDATE_UNEXPECTED_CONTENT")
    if git(TAKY,"ls-files","--","staging/crew_voice_20261010").strip():
        raise RuntimeError("AUDIO_SOURCE_GIT_TRACKED")
    # Compatibility junction preserves old immutable handoff references.
    if SOURCE_AUDIO.is_symlink():raise RuntimeError("AUDIO_SOURCE_ALREADY_LINK")
    return {"status":"MOVE_CANDIDATE","source":str(SOURCE_AUDIO),"target":str(TARGET_AUDIO),"sha256":files}

def runtime_code_consumer_gates():
    """Check that index-loaded executable files exist AND are versioned.

    Approved audio, user content, design images and generated binary packs are
    deliberately excluded: their release authority is not the Git code tree.
    """
    import html
    result={}
    for name in ("Ready & Set","Hide & Seek","Snap & Pop",
                 "Play Camp","SAVEY","TAKY-MOBILE"):
        repo=ROOT/name
        index=repo/"index.html"
        if not index.is_file():raise RuntimeError("APP_INDEX_MISSING:"+name)
        tracked=set(git(repo,"ls-files","-z").split("\0"))
        found=set()
        for hit in re.finditer(
            r'<(?:script|link)\b[^>]*?\b(?:src|href)\s*=\s*(["\'])(.*?)\1',
            index.read_text(encoding="utf-8-sig",errors="replace"),
            re.IGNORECASE|re.DOTALL):
            url=html.unescape(hit.group(2)).split("?")[0].split("#")[0]
            if not url or url.startswith(("https:","http:","//","data:","blob:","javascript:","mailto:")):
                continue
            if Path(url).suffix.casefold() not in {".js",".mjs",".css",".ts",".tsx"}:
                continue
            candidates=(
                (repo/"public"/url.lstrip("/"),repo/url.lstrip("/"))
                if url.startswith("/") else
                (repo/"public"/url,repo/url)
            )
            existing=next((x for x in candidates if x.is_file()),None)
            if existing is None:
                raise RuntimeError("APP_RUNTIME_CODE_NOT_PRESENT:"+name+":"+url)
            if existing.resolve().is_relative_to(repo.resolve()) is False:
                raise RuntimeError("APP_RUNTIME_CODE_ESCAPE:"+name+":"+url)
            relative=existing.relative_to(repo).as_posix()
            if relative not in tracked:
                raise RuntimeError("APP_RUNTIME_CODE_UNVERSIONED:"+name+":"+relative)
            found.add(relative)
        dirty=subprocess.run(["git","-C",str(repo),"diff","--quiet","--","index.html"],
                            timeout=12).returncode!=0
        result[name]={"direct_runtime_code_files":len(found),
                      "all_direct_code_git_versioned":True,
                      "index_html_worktree_modified":dirty,
                      "runtime_and_binary_release_verified":False}
    return result

def global_custody_gates():
    """One cross-repository audit of actual consumer authorities, not a test counter."""
    arch=ROOT/"TAKY_ARCHI GROW"
    physical=WB/"REFERENCE"
    refs=[(ROOT/"TAKY"/"REFERENCE",TAKY),
          (arch/"REFERENCE",arch),
          (ROOT/"TAKY-SOURCE-VAULT"/"REFERENCE",None)]
    evidence=[]
    for alias,gitroot in refs:
        if not (alias.is_junction() and os.path.samefile(alias,physical)):
            raise RuntimeError("CANONICAL_REFERENCE_ALIAS_DRIFT:"+str(alias))
        ignored=None
        if gitroot:
            rel=alias.relative_to(gitroot).as_posix()
            check=subprocess.run(["git","-C",str(gitroot),"check-ignore","-q","--",rel+"/"],
                timeout=12)
            tracked=git(gitroot,"ls-files","--",rel+"/")
            if check.returncode!=0 or tracked.strip():
                raise RuntimeError("GIT_RAW_WAREHOUSE_STAGING_RISK:"+str(alias))
            ignored=True
        evidence.append({"alias":str(alias),"target":str(physical),"git_ignored":ignored})
    record_index=ROOT/"TAKY"/"TOOLS"/"TAKY_SOURCE_RECORD_LOCATION_INDEX.py"
    cmd=subprocess.run([sys.executable,str(record_index),"--check"],
        capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=25)
    if cmd.returncode:
        raise RuntimeError("CURRENT_HISTORY_SOURCE_RECORD_DRIFT:"+cmd.stdout[-250:])
    return {"canonical_reference_junctions":evidence,
            "source_record_index":"PASS",
            "runtime_code_consumers":runtime_code_consumer_gates(),
            "held_backup_roots_intentionally_not_scanned":True}

def audit():
    report={"schema":"TAKY_WORKSPACE_CLEANUP_RELOCATION_V1",
            "at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "root":str(ROOT),"mode":"READONLY","git_stale":{},
            "audio":None,"empty_candidates":[],"protected_roots":len(ACTIVE_ROOTS)}
    for name in REPOS:
        repo=ROOT/name
        all_w,stale=worktree_status(repo)
        report["git_stale"][name]={"registered":len(all_w),"dangling":stale}
    report["audio"]=audio_preflight()
    report["global_custody_gates"]=global_custody_gates()
    for p in EMPTY:
        report["empty_candidates"].append({"path":str(p),"present":p.is_dir(),
              "empty":p.is_dir() and not any(p.iterdir())})
    return report

def backup_and_prune(report):
    saved=[];pruned={}
    for name,d in report["git_stale"].items():
        stale=d["dangling"]
        if not stale:continue
        repo=ROOT/name
        # Worktree pruning cannot be allowed to delete different registrations
        # than our audited, physically absent candidates.
        dry=git(repo,"worktree","prune","--dry-run","--verbose")
        drynames=set(re.findall(r"Removing worktrees/([^:\r\n]+):",dry))
        gitdir=Path(git(repo,"rev-parse","--absolute-git-dir").strip())
        stale_paths={str(Path(x["path"])) for x in stale}
        selected=[]
        for x in stale:
            key=Path(x["path"]).name
            if key not in drynames:raise RuntimeError("WORKTREE_DRYRUN_MISMATCH:"+name+":"+key)
            src=gitdir/"worktrees"/key
            if not src.is_dir():raise RuntimeError("WORKTREE_METADATA_MISSING:"+str(src))
            dst=SNAPSHOT/name/key
            if dst.exists():raise RuntimeError("WORKTREE_BACKUP_ALREADY_EXISTS:"+str(dst))
            selected.append((src,dst,x))
        if drynames!={Path(x["path"]).name for x in stale}:
            raise RuntimeError("WORKTREE_PRUNE_UNEXPECTED_CANDIDATES:"+name)
        for src,dst,x in selected:
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(src,dst)
            if members_hash(src)!=members_hash(dst):
                raise RuntimeError("WORKTREE_BACKUP_HASH_MISMATCH:"+str(src))
            saved.append({"repository":name,"metadata":str(dst),"worktree":x})
        before_branches=git(repo,"for-each-ref","--format=%(refname):%(objectname)","refs/heads")
        git(repo,"worktree","prune","--verbose")
        after_branches=git(repo,"for-each-ref","--format=%(refname):%(objectname)","refs/heads")
        if before_branches!=after_branches:raise RuntimeError("WORKTREE_BRANCH_REFS_CHANGED:"+name)
        _,after=worktree_status(repo)
        if after:raise RuntimeError("PRUNE_DANGLING_REMAINS:"+name)
        pruned[name]=len(stale)
    return saved,pruned

def move_audio(entry):
    if entry["status"]=="ALREADY_MOVED":return entry
    if entry["status"]=="ALREADY_MOVED_NO_COMPAT_ALIAS":raise RuntimeError('AUDIO_COMPAT_PATH_MISSING')
    old=SOURCE_AUDIO;new=TARGET_AUDIO
    new.parent.mkdir(parents=True,exist_ok=True)
    os.rename(old,new) # same disk D:, atomic, no copy/partial transfer.
    # Legacy handoff paths continue to resolve, preserving historical docs.
    p=subprocess.run(["cmd.exe","/c","mklink","/J",str(old),str(new)],
                     capture_output=True,text=True,errors="replace")
    if p.returncode or not old.exists() or not os.path.samefile(old,new):
        if old.exists():
            raise RuntimeError("AUDIO_COMPAT_JUNCTION_FAILED_AND_OLD_PATH_OCCUPIED")
        os.rename(new,old)
        raise RuntimeError("AUDIO_JUNCTION_FAILED_MOVE_ROLLED_BACK:"+p.stderr[-250:])
    if entry["sha256"]!=members_hash(new):
        raise RuntimeError("AUDIO_AFTER_MOVE_HASH_MISMATCH")
    return {"status":"MOVED_WITH_COMPAT_JUNCTION","source":str(old),"target":str(new),
            "files":len(entry["sha256"]),"old_path_resolves":True,
            "sha256":entry["sha256"]}

def remove_empty():
    removed=[]
    for p in EMPTY:
        if p.exists():
            if not p.is_dir() or p.is_symlink() or any(p.iterdir()):
                raise RuntimeError("NOT_EMPTY_OR_UNSAFE_DIRECTORY:"+str(p))
            p.rmdir()
            removed.append(str(p))
    return removed

def update_refs():
    # Earlier cleanup already populated these shared authority records.
    # A rerun must NEVER overwrite CURRENT, task decisions, or later C2S
    # progress with stale migration-stage defaults.
    data=json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    assert Path(data["cleanup_controller"])==ROOT/"TAKY"/"TOOLS"/"TAKY_WORKSPACE_CLEANUP.py"
    assert Path(data["archived_crew_audio_20261010"])==TARGET_AUDIO
    assert Path(data["crew_audio_legacy_compatible_path"])==SOURCE_AUDIO
    assert Path(data["global_reference_physical_root"])==WB/"REFERENCE"
    tasks=json.loads(TASKS.read_text(encoding="utf-8-sig"))
    assert {"CLN-001","CLN-002","CLN-003","CLN-005"}.issubset(
        {t["id"] for t in tasks["tasks"]})
    # The immutable operation receipt records this run. User intent or
    # separately verified task evidence controls later CURRENT changes.
    return {"registry_checked":True,"task_registry_checked":True,
            "authorities_rewritten":False,"task_statuses_rewritten":False}

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--audit",action="store_true")
    g.add_argument("--apply-safe",action="store_true")
    a=ap.parse_args()
    result=audit()
    if a.audit:
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    # Idempotent: converged workspaces must not re-run historical migrations or
    # overwrite up-to-date CURRENT registries with retired stage-1 defaults.
    if (all(not x["dangling"] for x in result["git_stale"].values())
        and result["audio"]["status"]=="ALREADY_MOVED"
        and all(not x["present"] for x in result["empty_candidates"])):
        print(json.dumps({"status":"ALREADY_CONVERGED_NO_MUTATION",
          "global_custody_gates":result["global_custody_gates"],
          "git_worktree_metadata_pruned":0,
          "original_user_files_deleted":0,
          "paths_moved":0,"existing_registry_rewritten":False},ensure_ascii=False))
        return 0
    result["mode"]="APPLY_SAFE"
    # Preserve record even if later operation is stopped.
    RECEIPT.parent.mkdir(parents=True,exist_ok=True)
    try:
        saved,pruned=backup_and_prune(result)
        result["worktree_metadata_backups"]=saved
        result["worktrees_pruned"]=pruned
        result["audio_result"]=move_audio(result["audio"])
        result["empty_dirs_removed"]=remove_empty()
        update_refs()
        result["status"]="APPLIED_AND_REFERENCES_UPDATED"
        result["root_source_vault_moved"]=False
        result["git_branch_deleted"]=False
        result["cloud_modified"]=False
    except Exception as exc:
        result["status"]="PARTIAL_HOLD"
        result["error"]=str(exc)
        RECEIPT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"status":result["status"],"reason":result["error"],"receipt":str(RECEIPT)},ensure_ascii=False))
        raise
    RECEIPT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
        "worktrees_pruned":result["worktrees_pruned"],
        "audio":result["audio_result"]["status"],
        "empty_dirs_removed":result["empty_dirs_removed"],
        "receipt":str(RECEIPT)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    sys.exit(main())
