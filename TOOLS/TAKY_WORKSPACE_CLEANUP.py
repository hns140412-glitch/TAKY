"""TAKY controlled cleanup: protected git repositories and RAW remain in place.

Run:
 python TAKY_WORKSPACE_CLEANUP.py --audit
 python TAKY_WORKSPACE_CLEANUP.py --inventory
 python TAKY_WORKSPACE_CLEANUP.py --apply-safe

Apply-safe performs only: backup+prune non-existent Git worktree registrations,
rehome 2026-10-10 retired candidate audio to existing WORKBENCH audio studio
(with an old-path junction), and remove two proved empty TAKY directories.
No Git branches, cloud folders, active collector scripts or live assets removed.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys
from collections import Counter, defaultdict
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

def workspace_inventory():
    """Git-bounded custody census; equal bytes never authorize removal.

    No recursive filesystem scan, link traversal, external source or Git writes.
    Include ignored generated outputs separately so ignore rules cannot make
    them appear physically deleted. Hash only regular Git-visible WIP files.
    """
    report={"repositories":{},"duplicate_content_groups":[],
            "source_owner":str(WB/"REFERENCE"),"deletion_authorized":False}
    hashes=defaultdict(list)
    for name in REPOS:
        repo=ROOT/name
        if repo.is_symlink() or repo.is_junction() or not repo.is_dir():
            raise RuntimeError("INVENTORY_ROOT_UNSAFE:"+name)
        unknown=sorted(set(filter(None,git(repo,"ls-files","--others",
            "--exclude-standard","-z").split("\0"))))
        changed=list(filter(None,git(repo,"diff","--name-only","-z","HEAD").split("\0")))
        # Existing HTML-loaded mock manifest supplies consumer and source-hash
        # evidence for the largest duplicate group; parse JSON, never execute JS.
        bindings={}
        manifest_rel="explorer-crew-voice/data-mock.js"
        manifest=repo/manifest_rel
        if name in {"Ready & Set","Hide & Seek","Snap & Pop"}:
            for candidate in (repo/"index.html",manifest.parent,manifest):
                if candidate.is_symlink() or candidate.is_junction():
                    raise RuntimeError("INVENTORY_CONSUMER_LINK_HOLD:"+str(candidate))
            if manifest_rel in (repo/"index.html").read_text(encoding="utf-8-sig"):
                body=manifest.read_text(encoding="utf-8-sig")
                payload=json.loads(body.split("=",1)[1].strip().rstrip(";"))
                bindings={clip["relative_path"]:clip["wav_sha256"]
                    for clip in payload["clips"] if clip.get("scope")=="MAIN_CREW"}
        rows=[]
        for rel in unknown:
            parts=Path(rel).parts
            if Path(rel).is_absolute() or ".." in parts:
                raise RuntimeError("INVENTORY_INVALID_RELATIVE_PATH:"+rel)
            path=repo
            safe=True
            for part in parts:
                path=path/part
                if path.is_symlink() or path.is_junction():
                    safe=False;break
            row={"path":rel,"category":"UNKNOWN_HOLD"}
            if not safe:
                row["category"]="LINK_HOLD_NOT_READ"
            elif path.is_file():
                low=rel.lower()
                if low.startswith(("audio/","characters/","public/audio/",
                    "public/characters/","badges/","data/","registry/")):
                    row["category"]="PROTECTED_ASSET_OR_DATA"
                elif path.suffix.lower() in {".py",".js",".cjs",".mjs",".ts",
                    ".tsx",".css",".ps1",".html",".yml",".yaml"}:
                    row["category"]="SOURCE_OR_TOOL_WIP"
                elif low.startswith(("artifacts/","c2s/","handoff/","history/")):
                    row["category"]="PRESERVED_EVIDENCE"
                row.update(bytes=path.stat().st_size,sha256=sha_file(path))
                if rel in bindings:
                    row["consumer"]="index.html -> "+manifest_rel
                    row["manifest_sha256_matches"]=bindings[rel]==row["sha256"]
                    if not row["manifest_sha256_matches"]:
                        row["category"]="LIVE_CONSUMER_HASH_MISMATCH_HOLD"
                hashes[row["sha256"]].append(name+"/"+rel)
            else:
                row["category"]="MISSING_OR_SPECIAL_HOLD"
            rows.append(row)
        ignored=list(filter(None,git(repo,"ls-files","--others","--ignored",
            "--exclude-standard","-z","--","artifacts/",".netlify/",
            ".playwright-mcp/").split("\0")))
        report["repositories"][name]={
            "branch":git(repo,"branch","--show-current").strip(),
            "head":git(repo,"rev-parse","HEAD").strip(),
            "remote_refs":git(repo,"for-each-ref","--format=%(refname):%(objectname)",
                              "refs/remotes").splitlines(),
            "remote_refs_are_local_cache":True,
            "modified_paths":changed,"untracked_count":len(rows),
            "categories":dict(Counter(r["category"] for r in rows)),
            "preserved_ignored_output_paths":ignored,"files":rows}
    report["duplicate_content_groups"]=[{"sha256":h,"paths":paths,
        "disposition":"KEEP_CONSUMER_COPIES_PENDING_OWNER_REBIND"}
        for h,paths in hashes.items() if len(paths)>1]
    return report

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
    if os.path.lexists(TARGET_AUDIO):
        raise RuntimeError("AUDIO_DEST_COLLISION")
    files=members_hash(SOURCE_AUDIO)
    if len(files)!=13 or any(Path(n).suffix not in {".mp3",".md"} for n in files):
        raise RuntimeError("AUDIO_CANDIDATE_UNEXPECTED_CONTENT")
    if git(TAKY,"ls-files","--","staging/crew_voice_20261010").strip():
        raise RuntimeError("AUDIO_SOURCE_GIT_TRACKED")
    # Compatibility junction preserves old immutable handoff references.
    if SOURCE_AUDIO.is_symlink() or SOURCE_AUDIO.is_junction():raise RuntimeError("AUDIO_SOURCE_ALREADY_LINK")
    audio_consumer_gate()
    return {"status":"MOVE_CANDIDATE","source":str(SOURCE_AUDIO),"target":str(TARGET_AUDIO),"sha256":files}

def audio_consumer_gate():
    """Fail closed on live executable references until paired code rebind is proven.

    Check Git-known executable code in the nine actual app/control repositories
    plus the source-vault worker entrypoints. Do not crawl the huge RAW warehouse,
    user backups, content vault junctions, .git objects or node_modules.
    A compatibility junction does not substitute for a required code edit.
    """
    suffixes={".py",".pyw",".js",".cjs",".mjs",".ts",".tsx",".jsx",
              ".ps1",".psm1",".cmd",".bat",".sh",".html",".json",
              ".yaml",".yml",".toml",".ini",".cfg",".xml"}
    excluded={Path(__file__).absolute(),REGISTRY.absolute(),TASKS.absolute(),RECEIPT.absolute()}
    needle=SOURCE_AUDIO.name.casefold()
    reviewed=0

    def inspect(root,p):
        nonlocal reviewed
        if p.absolute() in excluded or p.suffix.casefold() not in suffixes:
            return
        if p.is_symlink() or p.is_junction():
            raise RuntimeError("HOLD_AUDIO_CONSUMER_LINK_UNREVIEWED:"+str(p))
        if not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
            raise RuntimeError("HOLD_AUDIO_CONSUMER_PATH_UNREVIEWED:"+str(p))
        if p.stat().st_size>2_000_000:
            raise RuntimeError("HOLD_AUDIO_CONSUMER_FILE_TOO_LARGE:"+str(p))
        try:
            raw=p.read_bytes()
            body=raw.decode("utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")
        except (OSError,UnicodeError) as exc:
            raise RuntimeError("HOLD_AUDIO_CONSUMER_REVIEW_INCOMPLETE:"+str(p)) from exc
        reviewed+=1
        if needle in body.casefold():
            raise RuntimeError("HOLD_AUDIO_CODE_REBIND_REQUIRED:"+str(p))

    for name in REPOS:
        root=ROOT/name
        if not root.is_dir() or root.is_symlink() or root.is_junction():
            raise RuntimeError("HOLD_AUDIO_CONSUMER_ROOT_UNREVIEWED:"+str(root))
        known=git(root,"ls-files","--cached","--others","--exclude-standard","-z")
        for rel in set(x for x in known.split("\0") if x):
            bits=Path(rel.replace("\\","/")).parts
            if not bits or ".." in bits or Path(rel).is_absolute():
                raise RuntimeError("HOLD_AUDIO_CONSUMER_RELATIVE_PATH_INVALID:"+rel)
            if any(bit.casefold() in {".git","node_modules","reference","90_archive","backup"} for bit in bits):
                continue
            inspect(root,root/rel)

    # SOURCE-VAULT hosts the currently active acquisition worker. Keep this
    # deliberate shallow entrypoint scan independent of its large captured RAW.
    worker=ROOT/"TAKY-SOURCE-VAULT"
    if not worker.is_dir() or worker.is_symlink() or worker.is_junction():
        raise RuntimeError("HOLD_AUDIO_COLLECTOR_ROOT_UNREVIEWED")
    for folder in (worker,worker/"scripts",worker/"patch"):
        if not folder.is_dir():continue
        if folder.is_junction() or folder.is_symlink():
            raise RuntimeError("HOLD_AUDIO_COLLECTOR_LINK_UNREVIEWED:"+str(folder))
        for path in folder.iterdir():
            if path.is_file() and path.suffix.casefold() in suffixes:
                inspect(worker,path)
    return {"static_consumer_check":"NO_LITERAL_REFERENCE_FOUND",
            "reviewed_executable_files":reviewed,"code_references_updated":False}

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
    proof=static_source_gate()
    return {"canonical_reference_junctions":evidence,
            "source_record_index":"PASS",
            "runtime_code_consumers":runtime_code_consumer_gates(),
            "runtime_static_dependency_proof":proof,
            "held_backup_roots_intentionally_not_scanned":True}

def run_static_scanner():
    guard=TAKY/"ENFORCEMENT"/"taky_live_app_dependency_guard.py"
    p=subprocess.run([sys.executable,str(guard),"--check"],
        capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=75)
    return p.returncode,p.stdout,p.stderr

def static_source_gate(runner=None):
    """Classify the six-app static scanner without hiding its exit-code contract.

    exit 0 + PASS_STATIC_ONLY*            -> static custody pass, HEAD parity seen.
    exit 3 + WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD with 0 missing/unversioned
                                          -> dependencies preserved, HEAD replay
                                             NOT proven (returned as a HOLD).
    exit 2 + BLOCK caused ONLY by Git-unversioned runtime assets (source missing=0,
    source unversioned=0, runtime asset missing=0, unversioned>0)
                                          -> READONLY ASSET_GATE_HOLD (structured, kept
                                             distinct from source HEAD drift; no PASS).
    anything else (missing source/asset, unversioned code, bad JSON, missing counters)
                                          -> RuntimeError (ERROR/HOLD, never PASS).
    """
    code,out,err=(runner or run_static_scanner)()
    try:
        proof=json.loads(out)
    except (TypeError,ValueError):
        raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_FAILED:exit="+str(code)
            +":"+str(out)[-500:]+str(err)[-250:])
    if not isinstance(proof,dict):
        raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_FAILED:exit="+str(code)+":NOT_OBJECT")
    status=proof.get("status")
    drift=proof.get("head_worktree_source_drift_count") or 0
    asset_checked=proof.get("runtime_asset_files_checked")
    asset_missing=proof.get("runtime_asset_missing_count")
    asset_unver=proof.get("runtime_asset_git_unversioned_count")
    for n in (asset_checked,asset_missing,asset_unver,drift):
        if not isinstance(n,int) or isinstance(n,bool) or n<0:
            raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_DRIFT:exit="+str(code)
                +":status="+str(status)+":RUNTIME_ASSET_PROOF_MALFORMED")
    if (proof.get("apps_checked")!=6
        or proof.get("git_unversioned_count")!=0
        or proof.get("missing_file_count")!=0):
        raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_DRIFT:exit="+str(code)
            +":status="+str(status))
    asset_hold=False
    if code==2 and status=="BLOCK" and asset_missing==0 and asset_unver>0:
        # Only Git custody of runtime assets blocks; source HEAD drift (if any) is
        # reported independently and neither condition is promoted to PASS.
        replay="HEAD_REPLAY_NOT_PROVEN" if drift else "PARTIAL_NOT_BROWSER_PROVEN"
        hold=bool(drift)
        asset_hold=True
    elif asset_missing or asset_unver:
        raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_DRIFT:exit="+str(code)
            +":status="+str(status)+":RUNTIME_ASSET_CUSTODY")
    elif code==0 and isinstance(status,str) and status.startswith("PASS_STATIC_ONLY") and not drift:
        replay="PARTIAL_NOT_BROWSER_PROVEN"
        hold=False
    elif code==3 and status=="WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD" and drift:
        replay="HEAD_REPLAY_NOT_PROVEN"
        hold=True
    else:
        raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_DRIFT:exit="+str(code)
            +":status="+str(status))
    return {"scanner_exit_code":code,"status":status,
            "apps_checked":proof["apps_checked"],
            "source_files_checked":proof.get("source_files_checked"),
            "missing_file_count":0,"git_unversioned_count":0,
            "head_worktree_source_drift_count":drift,
            "runtime_asset_files_checked":asset_checked,
            "runtime_asset_missing_count":0,
            "runtime_asset_git_unversioned_count":asset_unver,
            "runtime_asset_gate_hold":asset_hold,
            "static_dependencies":"STATIC_DEPENDENCIES_PRESERVED",
            "head_replay":replay,"head_replay_hold":hold,
            "binary_runtime_ui_verified":False,
            "binary_assets_or_browser_E2E_approved":False}

def audit():
    report={"schema":"TAKY_WORKSPACE_CLEANUP_RELOCATION_V1",
            "at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "root":str(ROOT),"mode":"READONLY","git_stale":{},
            "completion_scope":"HISTORICAL_RELOCATION_CHECKS_ONLY",
            "global_cleanup_complete":False,
            "audio":None,"empty_candidates":[],"protected_roots":len(ACTIVE_ROOTS)}
    for name in REPOS:
        repo=ROOT/name
        all_w,stale=worktree_status(repo)
        report["git_stale"][name]={"registered":len(all_w),"dangling":stale}
    report["audio"]=audio_preflight()
    report["global_custody_gates"]=global_custody_gates()
    proof=report["global_custody_gates"]["runtime_static_dependency_proof"]
    head_hold=proof["head_replay_hold"]
    asset_hold=proof["runtime_asset_gate_hold"]
    hold=head_hold or asset_hold
    report["custody_status"]=("PARTIAL_CUSTODY_HOLD" if hold
                              else "STATIC_CUSTODY_PASS_NOT_COMPLETE")
    report["source_gate_hold"]=hold
    report["custody_hold_classes"]={
        "source_head_drift":{"hold":head_hold,
            "count":proof["head_worktree_source_drift_count"]},
        "runtime_asset_git_unversioned":{"hold":asset_hold,
            "status":"ASSET_GATE_HOLD" if asset_hold else "CLEAR",
            "count":proof["runtime_asset_git_unversioned_count"],
            "missing_count":proof["runtime_asset_missing_count"]},
        "essential_assets_must_not_be_deleted":True}
    report["production_ready"]=False
    report["deployment_allowed"]=False
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

def rollback_audio(transaction):
    """Compensate only this invocation, never overwrite an occupied old path."""
    if not transaction:return {"status":"NO_AUDIO_MUTATION"}
    old=SOURCE_AUDIO;new=TARGET_AUDIO
    try:
        if not transaction.get("moved"):
            if (old.exists() and old.stat().st_ino==transaction["inode"]
                and not os.path.lexists(new)):
                return {"status":"NO_AUDIO_MUTATION"}
            raise RuntimeError("MOVE_OUTCOME_UNCERTAIN")
        if (new.is_symlink() or new.is_junction() or not new.is_dir()
            or new.stat().st_ino!=transaction["inode"]
            or members_hash(new)!=transaction["sha256"]):
            raise RuntimeError("MOVED_DATA_CHANGED_OR_UNVERIFIABLE")
        if os.path.lexists(old):
            if (not transaction.get("junction_inode") or not old.is_junction()
                or old.lstat().st_ino!=transaction["junction_inode"]
                or not os.path.samefile(old,new)):
                raise RuntimeError("OLD_PATH_OCCUPIED_OR_ALIAS_NOT_OWNED")
            old.rmdir()  # unlink only the verified junction, never its contents
        os.rename(new,old)
        transaction.clear()
        return {"status":"AUDIO_MOVE_ROLLED_BACK"}
    except Exception as exc:
        return {"status":"HOLD_AUDIO_ROLLBACK_UNSAFE","reason":str(exc)}

def move_audio(entry,transaction=None):
    if entry["status"]=="ALREADY_MOVED":return entry
    if entry["status"]=="ALREADY_MOVED_NO_COMPAT_ALIAS":raise RuntimeError('AUDIO_COMPAT_PATH_MISSING')
    # Recheck immediately before mutation; an audit result is not authorization
    # to relocate data after consumers or content have changed.
    fresh=audio_preflight()
    if fresh["status"]!="MOVE_CANDIDATE" or fresh["sha256"]!=entry["sha256"]:
        raise RuntimeError("HOLD_AUDIO_PREFLIGHT_CHANGED")
    update_refs()
    if transaction is None:transaction={}
    old=SOURCE_AUDIO;new=TARGET_AUDIO
    new.parent.mkdir(parents=True,exist_ok=True)
    transaction.update(inode=old.stat().st_ino,sha256=entry["sha256"],moved=False)
    try:
        os.rename(old,new) # same disk D:, atomic, no copy/partial transfer.
        transaction["moved"]=True
        # Use literal PowerShell paths, avoiding cmd.exe path interpolation.
        quote=lambda p: "'"+str(p).replace("'","''")+"'"
        p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",
            "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path "
            +quote(old)+" -Target "+quote(new)+" | Out-Null"],
            capture_output=True,text=True,errors="replace",timeout=20)
        if old.is_junction() and os.path.samefile(old,new):
            transaction["junction_inode"]=old.lstat().st_ino
        if p.returncode or not transaction.get("junction_inode"):
            raise RuntimeError("AUDIO_COMPAT_JUNCTION_FAILED")
        if entry["sha256"]!=members_hash(new):
            raise RuntimeError("AUDIO_AFTER_MOVE_HASH_MISMATCH")
        update_refs()
    except Exception as exc:
        compensation=rollback_audio(transaction)
        raise RuntimeError(str(exc)+":"+json.dumps(compensation)) from exc
    return {"status":"MOVED_WITH_COMPAT_JUNCTION","source":str(old),"target":str(new),
            "files":len(entry["sha256"]),"old_path_resolves":True,
            "code_references_updated":False,
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
    expected={"cleanup_controller":ROOT/"TAKY"/"TOOLS"/"TAKY_WORKSPACE_CLEANUP.py",
              "archived_crew_audio_20261010":TARGET_AUDIO,
              "crew_audio_legacy_compatible_path":SOURCE_AUDIO,
              "global_reference_physical_root":WB/"REFERENCE"}
    for key,value in expected.items():
        if Path(data[key])!=value:raise RuntimeError("REGISTRY_PATH_MISMATCH:"+key)
    tasks=json.loads(TASKS.read_text(encoding="utf-8-sig"))
    if not {"CLN-001","CLN-002","CLN-003","CLN-005"}.issubset(
        {t["id"] for t in tasks["tasks"]}):raise RuntimeError("TASK_REGISTRY_MISMATCH")
    # The immutable operation receipt records this run. User intent or
    # separately verified task evidence controls later CURRENT changes.
    return {"registry_checked":True,"task_registry_checked":True,
            "code_references_updated":False,
            "authorities_rewritten":False,"task_statuses_rewritten":False}

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--audit",action="store_true")
    g.add_argument("--apply-safe",action="store_true")
    g.add_argument("--inventory",action="store_true",
                   help="Read-only nine-repository WIP custody and duplicate census")
    a=ap.parse_args()
    if a.inventory:
        print(json.dumps(workspace_inventory(),ensure_ascii=False,indent=2));return 0
    try:
        result=audit()
    except RuntimeError as exc:
        # Fatal custody breakage is a structured ERROR/HOLD, never PASS; no mutation yet.
        print(json.dumps({"status":"ERROR_HOLD","reason":str(exc),
            "global_cleanup_complete":False,"production_ready":False,
            "deployment_allowed":False,"mutation_performed":False},ensure_ascii=False))
        return 2
    if a.audit:
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    converged=(all(not x["dangling"] for x in result["git_stale"].values())
        and result["audio"]["status"]=="ALREADY_MOVED"
        and all(not x["present"] for x in result["empty_candidates"]))
    if result["source_gate_hold"]:
        # Fail closed before any mutation; a converged no-op is reported
        # separately and never implies global completion.
        print(json.dumps({"status":"HOLD_SOURCE_GATE_NO_MUTATION",
          "custody_status":result["custody_status"],
          "historical_convergence_noop":converged,
          "custody_hold_classes":result["custody_hold_classes"],
          "global_cleanup_complete":False,"production_ready":False,
          "deployment_allowed":False,
          "global_custody_gates":result["global_custody_gates"],
          "paths_moved":0,"git_worktree_metadata_pruned":0,
          "existing_registry_rewritten":False,"receipt_written":False},ensure_ascii=False))
        return 3
    # Idempotent: converged workspaces must not re-run historical migrations or
    # overwrite up-to-date CURRENT registries with retired stage-1 defaults.
    if converged:
        print(json.dumps({"status":"ALREADY_CONVERGED_NO_MUTATION",
          "completion_scope":result["completion_scope"],
          "global_cleanup_complete":False,
          "global_custody_gates":result["global_custody_gates"],
          "git_worktree_metadata_pruned":0,
          "original_user_files_deleted":0,
          "paths_moved":0,"existing_registry_rewritten":False},ensure_ascii=False))
        return 0
    result["mode"]="APPLY_SAFE"
    # Preserve record even if later operation is stopped.
    RECEIPT.parent.mkdir(parents=True,exist_ok=True)
    transaction={}
    try:
        saved,pruned=backup_and_prune(result)
        result["worktree_metadata_backups"]=saved
        result["worktrees_pruned"]=pruned
        result["audio_result"]=move_audio(result["audio"],transaction)
        result["empty_dirs_removed"]=remove_empty()
        result["reference_checks"]=update_refs()
        result["status"]="APPLIED_WITH_COMPATIBILITY_REFERENCES_CHECKED"
        result["root_source_vault_moved"]=False
        result["git_branch_deleted"]=False
        result["cloud_modified"]=False
        RECEIPT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except Exception as exc:
        result["status"]="PARTIAL_HOLD"
        result["error"]=str(exc)
        result["audio_compensation"]=rollback_audio(transaction)
        try:
            RECEIPT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as receipt_exc:
            result["receipt_error"]=str(receipt_exc)
        print(json.dumps({"status":result["status"],"reason":result["error"],"receipt":str(RECEIPT)},ensure_ascii=False))
        raise
    print(json.dumps({"status":result["status"],
        "worktrees_pruned":result["worktrees_pruned"],
        "audio":result["audio_result"]["status"],
        "empty_dirs_removed":result["empty_dirs_removed"],
        "receipt":str(RECEIPT)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    sys.exit(main())
