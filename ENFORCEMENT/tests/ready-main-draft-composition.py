#!/usr/bin/env python3
"""Read-only three-way snapshot composition of exact Ready main and Draft #100.

Creates ONLY a disposable untracked combined directory in audit CI. Uses the
actual merge-base/source trees, byte-level tracked-file comparison, and aborts
on conflicting files. No Git ref, remote branch, PR, main or source copy changes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import stat
import subprocess
from pathlib import Path

MAIN="1d672d862cc8329a5f19ca91c9ed6a338752f5ae"
BASE="98df214a6078f16f2b6710016898a4d7798798db"
DRAFT="9c8df0fc72aea3d07a4c59eb432be541bf4a5c44"

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args]).decode().strip()

def tracked(root):
    items=subprocess.check_output(["git","-C",str(root),"ls-files","-z"]).split(b"\0")
    result=set()
    for item in items:
        if not item:continue
        rel=Path(item.decode())
        if rel.is_absolute() or ".." in rel.parts or (root/rel).is_symlink():
            raise RuntimeError("UNSAFE_TRACKED_PATH")
        result.add(rel.as_posix())
    return result

def state(root,path,items):
    if path not in items:return None
    p=root/path
    mode=stat.S_IMODE(p.stat().st_mode)
    return (hashlib.sha256(p.read_bytes()).hexdigest(),mode)

def main():
    parser=argparse.ArgumentParser()
    for key in ("base","main","draft","output"):parser.add_argument(key,type=Path)
    a=parser.parse_args()
    if (git(a.base,"rev-parse","HEAD"),git(a.main,"rev-parse","HEAD"),
        git(a.draft,"rev-parse","HEAD"))!=(BASE,MAIN,DRAFT):
        raise RuntimeError("PINNED_SOURCE_HEAD_CHANGED")
    paths={key:tracked(getattr(a,key)) for key in ("base","main","draft")}
    names=set.union(*paths.values())
    main_changed={p for p in names if state(a.base,p,paths["base"])!=state(a.main,p,paths["main"])}
    draft_changed={p for p in names if state(a.base,p,paths["base"])!=state(a.draft,p,paths["draft"])}
    overlap=main_changed&draft_changed
    incompatible={p for p in overlap if state(a.main,p,paths["main"])!=state(a.draft,p,paths["draft"])}
    if incompatible:
        raise RuntimeError("SAME_PATH_DIVERGENT:"+",".join(sorted(incompatible)))
    # Known current heads: six main-only file changes, 36 draft paths.
    if len(main_changed)!=6 or len(draft_changed)!=36 or overlap:
        raise RuntimeError("UNREVIEWED_DIFF_SET:"+str((len(main_changed),len(draft_changed),sorted(overlap))))
    if a.output.exists():
        raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    shutil.copytree(a.main,a.output,ignore=shutil.ignore_patterns(".git"))
    for rel in sorted(draft_changed):
        target=a.output/rel
        source=a.draft/rel
        if rel not in paths["draft"]:
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
    for rel in names:
        expected=a.draft if rel in draft_changed else a.main
        source_paths=paths["draft"] if rel in draft_changed else paths["main"]
        actual=state(a.output,rel,tracked(a.output)) if False else None
        want=state(expected,rel,source_paths)
        actual_path=a.output/rel
        if want is None:
            if actual_path.exists():raise RuntimeError("UNEXPECTED_OUTPUT:"+rel)
        else:
            if not actual_path.is_file() or (
                hashlib.sha256(actual_path.read_bytes()).hexdigest(),
                stat.S_IMODE(actual_path.stat().st_mode))!=want:
                raise RuntimeError("OUTPUT_BYTE_MISMATCH:"+rel)
    if not {"ready-integration-v1.js","scripts/validate-learning-runtime-bridge.mjs",
            ".github/workflows/taky-codex-executor.yml"}.issubset(main_changed):
        raise RuntimeError("MAIN_ONLY_CONSUMERS_NOT_IDENTIFIED")
    if not {"ready-central-learning-roundtrip-v01.js","ready-runtime-v07.js",
            "ready-snap-run-scope-v01.js","tests/snap-return-isolation.spec.js"}.issubset(draft_changed):
        raise RuntimeError("DRAFT_ROUNDTRIP_FILES_MISSING")
    print(json.dumps({"schema":"TAKY_READY_ISOLATED_COMPOSITION_AUDIT",
        "main_head":MAIN,"merge_base":BASE,"draft_head":DRAFT,
        "main_only_paths_retained":len(main_changed),
        "draft_paths_applied":len(draft_changed),
        "overlapping_changed_paths":len(overlap),
        "verified_composed_source_paths":len(names),
        "main_world_state_consumer_preserved":True,
        "main_branch_modified":False,"merged_pull_request":False},sort_keys=True))
if __name__=="__main__":main()
