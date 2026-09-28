#!/usr/bin/env python3
"""Byte-audited disposable composition of two independent main-based TAKY Drafts.

This does NOT merge Git history or copy either Draft's workflow over another.
Exact conflict is integration workflow YAML; the audit harness separately runs
the union of both test suites. Unknown new overlaps abort before output.
"""
import hashlib
import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

MAIN="8e78af8b77d1f3e132f05c99cd6b69a7f258a23e"
AUTH="31c0346222b3454ba6ac098ae127a8facd23ef4a"
INDEX="d397e85431b4ed864b339d0bf9d8dc123dcdfd66"
ALLOWED_OVERLAP={".github/workflows/mining-indexing-learning-integration.yml"}

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],text=True).strip()

def tracked(root):
    raw=subprocess.check_output(["git","-C",str(root),"ls-files","-z"])
    result=set()
    for entry in raw.split(b"\0"):
        if not entry:continue
        p=Path(entry.decode())
        if p.is_absolute() or ".." in p.parts or (root/p).is_symlink():
            raise RuntimeError("UNSAFE_SOURCE_PATH")
        result.add(p.as_posix())
    return result

def fingerprint(root,rel,paths):
    if rel not in paths:return None
    p=root/rel
    return (hashlib.sha256(p.read_bytes()).hexdigest(),stat.S_IMODE(p.stat().st_mode))

def main():
    if len(sys.argv)!=5:raise RuntimeError("EXPECTED_MAIN_AUTH_INDEX_OUTPUT")
    main,auth,index,out=map(Path,sys.argv[1:])
    if (git(main,"rev-parse","HEAD"),git(auth,"rev-parse","HEAD"),
        git(index,"rev-parse","HEAD"))!=(MAIN,AUTH,INDEX):
        raise RuntimeError("EXACT_SOURCE_HEAD_CHANGED")
    folders={"main":main,"auth":auth,"index":index}
    paths={name:tracked(folder) for name,folder in folders.items()}
    names=set.union(*paths.values())
    changed={}
    for name in ("auth","index"):
        changed[name]={p for p in names if
            fingerprint(folders[name],p,paths[name])!=fingerprint(main,p,paths["main"])}
    overlap=changed["auth"]&changed["index"]
    if overlap!=ALLOWED_OVERLAP:
        raise RuntimeError("UNREVIEWED_CROSS_DRAFT_OVERLAP:"+str(sorted(overlap)))
    if not {"ENFORCEMENT/learning_evidence_gap_broker.py",
            "ENFORCEMENT/learning_index_authority_review_test.py"}.issubset(changed["auth"]):
        raise RuntimeError("AUTHORITY_DRAFT_FILES_MISSING")
    if not {"ENFORCEMENT/reference_intake_executor.py",
            "ENFORCEMENT/reference_index_owner_receipt.py",
            "ENFORCEMENT/reference_index_owner_receipt_test.py",
            "ENFORCEMENT/cross_engine_growth_e2e_test.py"}.issubset(changed["index"]):
        raise RuntimeError("INDEXING_RECEIPT_DRAFT_FILES_MISSING")
    if out.exists():raise RuntimeError("COMBINED_OUTPUT_ALREADY_EXISTS")
    shutil.copytree(main,out,ignore=shutil.ignore_patterns(".git"))
    for name in ("auth","index"):
        for rel in sorted(changed[name]-overlap):
            target=out/rel
            if rel not in paths[name]:
                target.unlink(missing_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(folders[name]/rel,target)
    for rel in sorted(names):
        winner=next((name for name in ("index","auth") if rel in changed[name]-overlap),"main")
        expected=fingerprint(folders[winner],rel,paths[winner])
        actual_path=out/rel
        if expected is None:
            if actual_path.exists():raise RuntimeError("UNEXPECTED_OUTPUT:"+rel)
        elif not actual_path.is_file() or (
            hashlib.sha256(actual_path.read_bytes()).hexdigest(),
            stat.S_IMODE(actual_path.stat().st_mode))!=expected:
            raise RuntimeError("OUTPUT_DIFFERS:"+rel)
    print(json.dumps({"schema":"TAKY_ISOLATED_INDEX_AUTHORITY_AND_INTAKE_COMPOSE_AUDIT",
        "main":MAIN,"authority_draft":AUTH,"owner_receipt_draft":INDEX,
        "source_paths_compared":len(names),
        "authority_paths":len(changed["auth"]),
        "owner_receipt_paths":len(changed["index"]),
        "excluded_workflow_conflict":sorted(overlap),
        "workflow_test_union":"RUN_IN_THIS_AUDIT_JOB_NOT_PROMOTED",
        "main_changed":False,"drafts_merged":False},sort_keys=True))
if __name__=="__main__":main()
