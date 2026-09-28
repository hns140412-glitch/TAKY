#!/usr/bin/env python3
"""Exact-source Hide main / V2 / independent PR19 collision inventory.

FAIL CLOSED on changed pinned heads or overlap membership. NOT a merge,
approval or replay of separately owned reflection/Badge producers.
"""
import json
import subprocess
import sys
from pathlib import Path
BASE="c0831a46ac0aa9d32c6dcc6a1e07ff70a8d155eb"
MAIN="1156c559bbc3da239b30606912ab0ae0548af0a3"
V2="1ccbd372890ba079accadb86e7610cd3fdad240a"
PR19="6d304af1f0d2bf5ce8678023ef2c62604a9e5deb"
EXPECTED_MAIN_V2={"app.js","hide-bridge.js","tests/shared-runtime-contract.test.js"}
EXPECTED_MAIN_ONLY={".github/workflows/learning-runtime-bridge.yml",
                    ".github/workflows/pages.yml",
                    "scripts/validate-learning-runtime-bridge.mjs"}
EXPECTED_PR19_V2={".github/workflows/validate.yml","hide-bridge.js",
                  "index.html","sw.js","tests/shared-runtime.spec.js"}
def cmd(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],text=True).strip()
def changed(base,other):
    a=set(cmd(other,"diff","--name-only",BASE,cmd(other,"rev-parse","HEAD")).splitlines())
    return {x for x in a if x}
def changed_from_main(root):
    return set(cmd(root,"diff","--name-only",MAIN,PR19).splitlines())
def contains(root,path,markers):
    s=(root/path).read_text(encoding="utf-8")
    if not all(x in s for x in markers):
        raise RuntimeError("EXPECTED_FEATURE_MARKER_MISSING:"+str(root/path))
def main():
    if len(sys.argv)!=5:raise RuntimeError("NEED_EXACT_BASE_MAIN_V2_PR19_DIRS")
    base,main_root,v2_root,owner=map(Path,sys.argv[1:])
    actual=(cmd(base,"rev-parse","HEAD"),cmd(main_root,"rev-parse","HEAD"),
            cmd(v2_root,"rev-parse","HEAD"),cmd(owner,"rev-parse","HEAD"))
    if actual!=(BASE,MAIN,V2,PR19):
        raise RuntimeError("SOURCE_EXACT_HEAD_DRIFT:"+str(actual))
    main_changed=changed(base,main_root)
    v2_changed=changed(base,v2_root)
    owner_changed=changed_from_main(owner)
    overlap=main_changed&v2_changed
    independent=owner_changed&v2_changed
    if overlap!=EXPECTED_MAIN_V2 or main_changed-v2_changed!=EXPECTED_MAIN_ONLY:
        raise RuntimeError("MAIN_TO_V2_COLLISION_DRIFT:"+str(sorted(overlap)))
    if independent!=EXPECTED_PR19_V2:
        raise RuntimeError("PR19_TO_V2_OWNER_COLLISION_DRIFT:"+str(sorted(independent)))
    # New V2 code has main Code Red attempt candidate, but the full legacy
    # child-authored reflection producer is still separately owned: do not
    # secretly mark runtime/badge feature integrated.
    contains(main_root,"hide-bridge.js",["function emitChildAuthoredReflection",
                                         "emitLearningMemorySignal"])
    contains(v2_root,"hide-bridge.js",["function emitLearningMemorySignal"])
    if "function emitChildAuthoredReflection" in (v2_root/"hide-bridge.js").read_text():
        raise RuntimeError("V2_REFLECTION_OWNER_ALREADY_CHANGED_REVIEW_REQUIRED")
    contains(v2_root,"app.js",["function emitCodeRedRetrievalCandidate",
                                 "verification_candidate","SLOW_CORRECT"])
    contains(owner,"hide-bridge.js",["function emitChildAuthoredReflection"])
    print(json.dumps({
        "schema":"TAKY_HIDE_OWNER_COLLISION_AUDIT_ONLY",
        "heads":{"base":BASE,"main":MAIN,"v2":V2,"separate_owner_pr19":PR19},
        "main_changed":len(main_changed),"v2_changed":len(v2_changed),
        "main_to_v2_overlaps":sorted(overlap),"main_only_preserve":sorted(EXPECTED_MAIN_ONLY),
        "separate_owner_pr19_to_v2_overlaps":sorted(independent),
        "code_red_candidate_in_v2":True,
        "child_authored_reflection_producer_separately_owned":True,
        "combined_source_acceptance":"NOT_TESTED",
        "automatic_merge_permitted":False,
        "main_or_product_modified":False,
    },sort_keys=True))
if __name__=="__main__":main()
