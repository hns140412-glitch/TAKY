#!/usr/bin/env python3
"""Restore TAKY's shared Claude/Codex Skill paths on a fresh Windows checkout.

TAKY is found as sibling <parent>/TAKY or as the parent of TAKY/.local/TAKY-2.0-ORCH.
The source skill content is owned by TAKY; this adapter never copies or edits it.
Default command is read-only 'check'. 'restore' only adds MISSING links.
Physical directories identical to the canonical source count as VERIFIED_CONTENT;
this is not proof of runtime skill invocation.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, subprocess, sys
from datetime import datetime, timezone

HERE=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=pathlib.Path(__file__).with_name("SKILL_LINKS_MANIFEST.json")
SKILL_RE=re.compile(r"^[a-z][a-z0-9-]*$")
CONSUMERS=(".agents/skills",".claude/skills")
def digest(p: pathlib.Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
def get_manifest(path: pathlib.Path=MANIFEST):
    m=json.loads(path.read_text(encoding="utf-8"))
    if m.get("schema")!="TAKY2_SKILL_LINK_MANIFEST_V1" or m.get("source_repo")!="TAKY":
        raise RuntimeError("MANIFEST_SCHEMA_OR_SOURCE_INVALID")
    names=m.get("skills")
    if not isinstance(names,dict) or len(names)!=11:
        raise RuntimeError("MANIFEST_SKILL_COUNT_INVALID")
    for name,sha in names.items():
        if not SKILL_RE.fullmatch(name) or not re.fullmatch(r"[a-f0-9]{64}",sha):
            raise RuntimeError("MANIFEST_SKILL_ENTRY_INVALID")
    return m
def is_link(p:pathlib.Path)->bool:
    return p.is_symlink() or (hasattr(p,"is_junction") and p.is_junction())
def canonical_source(repo:pathlib.Path):
    """Return the trusted TAKY Git root for the two known layouts only:
    <parent>/TAKY (sibling) or TAKY/.local/<repo> (nested worktree)."""
    parent=repo.parent
    candidates=[parent/"TAKY"]
    if parent.name==".local":
        candidates.append(parent.parent)
    for cand in candidates:
        try:
            base=cand.resolve(strict=True)
        except OSError:
            continue
        if base.name=="TAKY" and (base/".git").exists() and (base/".claude"/"skills").is_dir() \
                and not is_link(base/".claude"/"skills"):
            return base
    raise RuntimeError("TAKY_GIT_SOURCE_NOT_FOUND")
def tree_digest(root:pathlib.Path):
    """Map of relative path -> sha256 (files) or None (dirs). None result if any link descendant."""
    out={}
    for cur,dirs,files in os.walk(root,followlinks=False):
        curp=pathlib.Path(cur)
        for d in dirs:
            if is_link(curp/d):
                return None
            out[(curp/d).relative_to(root).as_posix()]=None
        for f in files:
            fp=curp/f
            if is_link(fp) or not fp.is_file():
                return None
            out[fp.relative_to(root).as_posix()]=digest(fp)
    return out
def collect(repo:pathlib.Path, manifest_path:pathlib.Path=MANIFEST):
    m=get_manifest(manifest_path)
    root=canonical_source(repo)
    output=[]
    for name,expect in sorted(m["skills"].items()):
        src=root/".claude"/"skills"/name
        # Don't read through an unexpected linked canonical source.
        if not src.is_dir() or is_link(src):
            raise RuntimeError("CANONICAL_SKILL_SOURCE_MISSING_OR_LINKED:"+name)
        skill=src/"SKILL.md"
        if not skill.is_file() or digest(skill)!=expect:
            raise RuntimeError("CANONICAL_SKILL_SOURCE_HASH_DRIFT:"+name)
        src_tree=tree_digest(src)
        if src_tree is None:
            raise RuntimeError("CANONICAL_SKILL_SOURCE_MISSING_OR_LINKED:"+name)
        for consumer in CONSUMERS:
            dst=repo/consumer/name
            if is_link(dst):
                state="LINK_VALID" if dst.resolve()==src.resolve() else "LINK_WRONG_TARGET"
            elif dst.is_dir():
                # Exact content match only; anything else stays a conflict (never overwritten).
                state="VERIFIED_CONTENT" if tree_digest(dst)==src_tree else "DESTINATION_OCCUPIED"
            elif dst.exists():
                state="DESTINATION_OCCUPIED"
            else:
                state="MISSING"
            output.append((name,str(consumer),src,dst,state))
    return output
def link(src:pathlib.Path, dst:pathlib.Path):
    if sys.platform=="win32":
        # Windows junctions don't need developer-mode symlink privileges.
        result=subprocess.run(["cmd","/d","/c","mklink","/J",str(dst),str(src)],
             text=True,capture_output=True,timeout=8)
        if result.returncode!=0:
            raise RuntimeError("JUNCTION_CREATION_FAILED")
    else:
        os.symlink(src,dst,target_is_directory=True)
def restore(repo:pathlib.Path,manifest_path:pathlib.Path=MANIFEST):
    rows=collect(repo,manifest_path)
    if any(state in ("LINK_WRONG_TARGET","DESTINATION_OCCUPIED") for *_,state in rows):
        raise RuntimeError("DESTINATION_CONFLICT_NO_MUTATION")
    created=[]
    try:
        for name,consumer,src,dst,state in rows:
            if state!="MISSING":
                continue
            parent=dst.parent
            parent.mkdir(parents=True,exist_ok=True)
            if dst.exists() or dst.is_symlink():
                raise RuntimeError("DESTINATION_CHANGED_DURING_RESTORE")
            link(src,dst)
            if dst.resolve()!=src.resolve():
                raise RuntimeError("RESTORED_LINK_TARGET_MISMATCH")
            created.append(str(dst))
    except Exception:
        # Do not remove even a newly made junction automatically; preserve evidence.
        raise
    return created
def manifest_data(repo:pathlib.Path):
    base=canonical_source(repo)
    names=("archi-grow","authority-check","browser-verify","cross-model-review",
           "handoff","intent-router","learning-grow","mining-index-learning",
           "mobile-webapp-build","outcome-quality","runtime-e2e")
    hashes={}
    for n in names:
        path=base/".claude"/"skills"/n/"SKILL.md"
        if not path.is_file():raise RuntimeError("MISSING_SOURCE:"+n)
        hashes[n]=digest(path)
    return {"schema":"TAKY2_SKILL_LINK_MANIFEST_V1",
        "source_repo":"TAKY","source_rel_to_target":"../TAKY/.claude/skills",
        "target_repo":"TAKY-2.0-ORCH","consumer_dirs":list(CONSUMERS),
        "skills":hashes,
        "source_authority":"TAKY Git-tracked source SKILL.md; hashes pinned",
        "not_proof_of_runtime_skill_activation":True}
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("check","restore","manifest-preview"))
    p.add_argument("--repo",type=pathlib.Path,default=HERE)
    p.add_argument("--manifest",type=pathlib.Path,default=MANIFEST)
    args=p.parse_args(argv)
    repo=args.repo.resolve(strict=True)
    if repo.name!="TAKY-2.0-ORCH" or not (repo/".git").exists():
        raise RuntimeError("TARGET_GIT_REPO_IDENTITY_INVALID")
    if args.action=="manifest-preview":
        data=manifest_data(repo)
        print(json.dumps(data,ensure_ascii=False,indent=2))
        return 0
    rows=collect(repo,args.manifest)
    bad=[(n,c,s) for n,c,src,dst,s in rows if s in ("DESTINATION_OCCUPIED","LINK_WRONG_TARGET")]
    if bad:raise RuntimeError("UNSAFE_LINK_CONFLICT:"+json.dumps(bad))
    restored=restore(repo,args.manifest) if args.action=="restore" else []
    status=collect(repo,args.manifest)
    missing=[(n,c) for n,c,src,dst,s in status if s not in ("LINK_VALID","VERIFIED_CONTENT")]
    links=sum(1 for *_,s in status if s=="LINK_VALID")
    verified=sum(1 for *_,s in status if s=="VERIFIED_CONTENT")
    output={"schema":"TAKY2_SHARED_SKILLS_LINK_QA_V1",
         "mode":args.action,"source_repo":str(canonical_source(repo)),
         "target_repo":str(repo),"skill_count":len(get_manifest(args.manifest)["skills"]),
         "expected_links":len(status),"valid_links":links,
         "verified_content_dirs":verified,"valid_consumers":links+verified,
         "missing_links":missing,"new_links_created":len(restored),
         "model_invoked":False,"canonical_skills_modified":False,
         "status":"PASS" if not missing else "NEEDS_RESTORE"}
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0 if not missing else 2
if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,RuntimeError,ValueError) as ex:
        print(json.dumps({"status":"HOLD","reason":str(ex),"provider_invoked":False}),file=sys.stderr)
        sys.exit(3)
