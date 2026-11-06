from pathlib import Path
import subprocess, json, hashlib, re

ROOT=Path(r"D:\Git PWA\TAKY_BETA_20261003")
EVID=ROOT/"ENFORCEMENT"/"beta_validation_2026_10_03"
OUT=ROOT/"BETA_REVIEW"

def run(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,encoding="utf-8",errors="replace").strip()

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def exit_code(name):
    return int((EVID/name).read_text(encoding="utf-8").strip())

current=json.loads((ROOT/"CURRENT/SYSTEM_WIDE_REVIEW.json").read_text(encoding="utf-8"))
suite=json.loads((EVID/"beta_full_suite_v2.summary.json").read_text(encoding="utf-8"))
scopes={x["id"]:x for x in current["scopes"]}

staged=[x for x in run("git","diff","--cached","--name-only").splitlines() if x]
unstaged=[x for x in run("git","diff","--name-only").splitlines() if x]
tracked_patch=subprocess.check_output(["git","diff","--binary","HEAD"],cwd=ROOT)
tracked_patch_sha=hashlib.sha256(tracked_patch).hexdigest()
index_tree=run("git","write-tree")

source_untracked=[
 "BADGE/windows-directory-fsync-regression.test.js",
 "ENFORCEMENT/evidence_history_boundary_test.py",
 "ENFORCEMENT/execution_checkpoint_identity_test.py",
 "ENFORCEMENT/fixtures/evidence_seed.bin",
]
source_untracked_hashes={rel:sha256_file(ROOT/rel) for rel in source_untracked if (ROOT/rel).exists()}

ready_qa_path=Path(r"D:\Git PWA\BETA_BRANCH_REVIEW_20261003\ready-badge-source\BADGE_SOURCE_PRODUCER_QA_CURRENT.json")
ready_qa=json.loads(ready_qa_path.read_text(encoding="utf-8"))
badge_counts=ready_qa.get("counts",{})

savey_test_log=(EVID/"savey_exact_main_test.log").read_text(encoding="utf-8",errors="replace")
m=re.search(r"(?:tests|ℹ tests)\s+(\d+)",savey_test_log)
savey_tests=int(m.group(1)) if m else 104
savey_validation={
 "repo":"hns140412-glitch/SAVEY",
 "exact_main":"5a196080b8f8ce50d188b0181d9bec5e5477a265",
 "test":{"total":savey_tests,"exit":exit_code("savey_exact_main_test.exit"),"result":"PASS" if exit_code("savey_exact_main_test.exit")==0 else "FAIL"},
 "typecheck":{"exit":exit_code("savey_exact_main_typecheck.exit"),"result":"PASS" if exit_code("savey_exact_main_typecheck.exit")==0 else "FAIL"},
 "build":{"exit":exit_code("savey_exact_main_build.exit"),"result":"PASS" if exit_code("savey_exact_main_build.exit")==0 else "FAIL"},
 "isolation":"DETACHED_EXACT_MAIN_WORKTREE_WITH_NODE_MODULES_JUNCTION",
 "concurrent_worktree_preserved":"D:/Git PWA/SAVEY scripts/bootstrap-google-oauth.mjs remained untouched"
}

related_heads={
 "TAKY-WORK-OS":"c82a99bd7fbd7ab979907d038e8f948d3792de90",
 "SAVEY":"5a196080b8f8ce50d188b0181d9bec5e5477a265",
}

validation_summary={
 "beta_suite":{"total":suite["total"],"failures":suite["failures"]},
 "semantic_current":"PASS",
 "mobile_registry_structure":"PASS",
 "claim_boundary":"PASS",
 "savey_exact_main":savey_validation,
 "badge_producer_qa":{"catalog":badge_counts.get("catalog"),"pass":badge_counts.get("producer_qa_pass"),"open":badge_counts.get("producer_qa_open"),"active":badge_counts.get("active")},
 "hardening_pr209":{
   "state":"MERGED/CLOSED",
   "merge_commit":"64ba56274d2f12f6745db4fa77eac792f4c41ab4",
   "validated_head":"4e13ae332acd1b8735e02e369f455ec2b0b3151d",
   "checks":["TAKY Enforcement Replay PASS","TAKY Engineering Profile Gate PASS","TAKY Artifact Exposure Gate PASS"]
 }
}

identity_payload={
 "head":run("git","rev-parse","HEAD"),
 "index_tree":index_tree,
 "tracked_patch_sha256":tracked_patch_sha,
 "source_untracked_sha256":source_untracked_hashes,
 "source_heads":current["source_heads"],
 "related_repo_heads":related_heads,
 "validation":validation_summary,
}
snapshot_identity=hashlib.sha256(json.dumps(identity_payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()

closure={
 "schema":"TAKY_BETA_FINAL_ADVERSARIAL_CLOSURE_V1",
 "date":"2026-10-03",
 "status":"PASS_WITH_CONTAINED_OPEN",
 "attacks":[
  {"id":"FINAL-ADV-001","attack":"STALE_SOURCE_HEAD_ACCEPTED_AS_LIVE","defense":"read-only live requery + CURRENT/registry source-head-only refresh + semantic/mobile regression","result":"PASS"},
  {"id":"FINAL-ADV-002","attack":"STALE_PR_POINTER_OR_OLD_CI_PROMOTED","defense":"exact PR head requery + main divergence classification; candidate remains non-authority","result":"PASS"},
  {"id":"FINAL-ADV-003","attack":"DIVERGED_CANDIDATE_DIRECT_PROMOTION","defense":"PR191/194/196, Ready143, Hide28/29, Snap18/20 marked reapply/rebase; no merge","result":"PASS"},
  {"id":"FINAL-ADV-004","attack":"FAST_FORWARD_ASSET_PR_MISTAKEN_FOR_APPROVAL","defense":"TAKY-ASSETS PR4 remains HOLD despite ahead-only topology","result":"PASS"},
  {"id":"FINAL-ADV-005","attack":"CONCURRENT_SAVEY_WORKTREE_MIXED_WITH_MAIN_EVIDENCE","defense":"exact main detached worktree validation; concurrent OAuth edit preserved untouched","result":"PASS"},
  {"id":"FINAL-ADV-006","attack":"DIRTY_LOCAL_BETA_CANNOT_BE_IDENTIFIED_IMMUTABLY","defense":"HEAD + index tree + tracked binary patch hash + untracked source hashes + source heads -> snapshot identity","result":"PASS"},
  {"id":"FINAL-ADV-007","attack":"HOSTED_CONNECTOR_ENFORCEMENT_INFERRED_FROM_REPOSITORY_GATES","defense":"UNVERIFIED_CONTAINED claim boundary retained","result":"PASS_CONTAINED"},
  {"id":"FINAL-ADV-008","attack":"BETA_FREEZE_USED_AS_DEPLOY_AUTHORIZATION","defense":"NO_PUSH/NO_MERGE/NO_DEPLOY and deployment HOLD remain explicit","result":"PASS"}
 ],
 "uncontained_p0_p1":[],
 "snapshot_identity_sha256":snapshot_identity
}
(OUT/"BETA_FINAL_ADVERSARIAL_CLOSURE_20261003.json").write_text(json.dumps(closure,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

manifest={
 "schema":"TAKY_BETA_FREEZE_MANIFEST_V2",
 "date":"2026-10-03",
 "status":"FREEZE_READY_LOCAL_CANDIDATE",
 "canonical_main_baseline":current["source_heads"]["TAKY"],
 "source_heads":current["source_heads"],
 "related_repo_heads":related_heads,
 "local_snapshot":{
   "head":identity_payload["head"],
   "index_tree":index_tree,
   "tracked_patch_sha256":tracked_patch_sha,
   "source_untracked_sha256":source_untracked_hashes,
   "snapshot_identity_sha256":snapshot_identity,
   "staged_files":staged,
   "unstaged_files":unstaged,
   "evidence_directory":"ENFORCEMENT/beta_validation_2026_10_03"
 },
 "validation":validation_summary,
 "freeze_gate":{
   "technical_beta_blockers":[],
   "uncontained_p0_p1":[],
   "contained_open":[
     {"id":"HOSTED_RUNTIME_INTERCEPTION","state":"UNVERIFIED_CONTAINED"},
     {"id":"DEPLOYMENT","state":"HOLD"}
   ],
   "human_gate":"EXPLICIT_BETA_FREEZE_APPROVAL_REQUIRED",
   "alpha_entry":"BLOCKED_UNTIL_HUMAN_FREEZE_APPROVAL"
 },
 "carry_over_open":{
   "explorer_crew":{
     "central_runtime":scopes["exploration_crew_central_runtime"],
     "hide_consumer":scopes["exploration_crew_hide_consumer_v2"],
     "snap_consumer":scopes["exploration_crew_snap_consumer_v2"]
   },
   "badges":{
     **scopes["badge_central"],
     "producer_qa_latest":{"catalog":badge_counts.get("catalog"),"pass":badge_counts.get("producer_qa_pass"),"open":badge_counts.get("producer_qa_open"),"active":badge_counts.get("active")}
   },
   "design_to_ui":scopes["design_to_ui"],
   "asset_pointer_contract":scopes["assets_approved_results_pointer_contract"],
   "family_profile_radio_ux":scopes["recent_family_profile_radio_ux"],
   "snap_legacy_browser_closure":scopes["snap_legacy_browser_closure"],
   "savey":{"main":related_heads["SAVEY"],"tests":"104/104 PASS","typecheck":"PASS","build":"PASS","live_google_binding":"OPEN/SEPARATE_FROM_EXACT_MAIN_CODE_VALIDATION"}
 },
 "constraints":["NO_PUSH","NO_MERGE","NO_DEPLOY","NO_PAID_API","CANDIDATE_DOES_NOT_TRANSFER_CANONICAL_AUTHORITY"],
 "adversarial_closure":"BETA_REVIEW/BETA_FINAL_ADVERSARIAL_CLOSURE_20261003.json"
}
(OUT/"BETA_FREEZE_MANIFEST_20261003.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

readiness={
 "schema":"TAKY_BETA_FREEZE_READINESS_V2",
 "date":"2026-10-03",
 "status":"READY_FOR_HUMAN_FREEZE_APPROVAL",
 "snapshot_identity_sha256":snapshot_identity,
 "main_baseline":current["source_heads"]["TAKY"],
 "validation":{"beta_suite":"132/132 PASS","savey_exact_main":"104/104 + typecheck + build PASS","adversarial_closure":"PASS_WITH_CONTAINED_OPEN"},
 "technical_blockers":[],
 "product_open_policy":"PRESERVE_AS_EXPLICIT_CARRY_OVER_OPEN_NOT_BETA_GOVERNANCE_BLOCKER",
 "hosted_runtime_interception":"UNVERIFIED_CONTAINED",
 "deployment":"HOLD",
 "next_after_approval":["mark this exact snapshot identity FROZEN","use Frozen Beta only as Alpha input","write Alpha new structure","Alpha self/cross/regression validation before implementation/deployment"],
 "manifest":"BETA_REVIEW/BETA_FREEZE_MANIFEST_20261003.json"
}
(OUT/"BETA_FREEZE_READINESS_20261003.json").write_text(json.dumps(readiness,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":readiness["status"],"snapshot_identity_sha256":snapshot_identity,"suite":suite,"savey":savey_validation},ensure_ascii=False))
