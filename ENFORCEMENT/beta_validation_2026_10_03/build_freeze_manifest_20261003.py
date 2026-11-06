from pathlib import Path
import subprocess, json, hashlib

ROOT = Path(r"D:\Git PWA\TAKY_BETA_20261003")
OUT = ROOT / "BETA_REVIEW"
OUT.mkdir(exist_ok=True)

def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

current=json.loads((ROOT/"CURRENT/SYSTEM_WIDE_REVIEW.json").read_text(encoding="utf-8"))
suite=json.loads((ROOT/"ENFORCEMENT/beta_validation_2026_10_03/beta_full_suite_v2.summary.json").read_text(encoding="utf-8"))

staged=[x for x in run("git","diff","--cached","--name-only").splitlines() if x]
unstaged=[x for x in run("git","diff","--name-only").splitlines() if x]
untracked=[x for x in run("git","ls-files","--others","--exclude-standard").splitlines() if x]

tracked_patch=subprocess.check_output(["git","diff","--binary","HEAD"],cwd=ROOT)
tracked_patch_sha=hashlib.sha256(tracked_patch).hexdigest()
index_tree=run("git","write-tree")

source_untracked=[
    "BADGE/windows-directory-fsync-regression.test.js",
    "ENFORCEMENT/evidence_history_boundary_test.py",
    "ENFORCEMENT/execution_checkpoint_identity_test.py",
    "ENFORCEMENT/fixtures/evidence_seed.bin",
]
source_untracked_hashes={}
for rel in source_untracked:
    p=ROOT/rel
    if p.exists():
        source_untracked_hashes[rel]=sha256_file(p)

scopes={x["id"]:x for x in current["scopes"]}

manifest={
  "schema":"TAKY_BETA_FREEZE_MANIFEST_V1",
  "date":"2026-10-03",
  "status":"FREEZE_READY_LOCAL_CANDIDATE",
  "canonical_main_baseline":current["source_heads"]["TAKY"],
  "source_heads":current["source_heads"],
  "local_snapshot":{
    "head":run("git","rev-parse","HEAD"),
    "index_tree":index_tree,
    "tracked_patch_sha256":tracked_patch_sha,
    "staged_files":staged,
    "unstaged_files":unstaged,
    "source_untracked_sha256":source_untracked_hashes,
    "evidence_directory":"ENFORCEMENT/beta_validation_2026_10_03"
  },
  "validation":{
    "beta_full_suite":suite,
    "semantic_current":"PASS",
    "mobile_registry_structure":"PASS",
    "claim_boundary":"PASS",
    "source_head_live_refresh":"PASS_BY_READ_ONLY_GITHUB_REQUERY_2026-10-03"
  },
  "freeze_gate":{
    "technical_beta_blockers":[],
    "contained_open":[
      {
        "id":"HOSTED_RUNTIME_INTERCEPTION",
        "state":"UNVERIFIED_CONTAINED",
        "boundary":"Repository enforcement must not be represented as automatic hosted connector interception."
      },
      {
        "id":"DEPLOYMENT",
        "state":"HOLD",
        "boundary":"No Netlify/deployment action is part of Beta freeze."
      }
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
    "badges":scopes["badge_central"],
    "design_to_ui":scopes["design_to_ui"],
    "asset_pointer_contract":scopes["assets_approved_results_pointer_contract"],
    "family_profile_radio_ux":scopes["recent_family_profile_radio_ux"],
    "snap_legacy_browser_closure":scopes["snap_legacy_browser_closure"]
  },
  "constraints":["NO_PUSH","NO_MERGE","NO_DEPLOY","NO_PAID_API","CANDIDATE_DOES_NOT_TRANSFER_CANONICAL_AUTHORITY"]
}
(OUT/"BETA_FREEZE_MANIFEST_20261003.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

readiness={
  "schema":"TAKY_BETA_FREEZE_READINESS_V1",
  "date":"2026-10-03",
  "status":"READY_FOR_HUMAN_FREEZE_APPROVAL",
  "basis":"Full Beta regression PASS after live source-head and candidate-pointer refresh.",
  "main_baseline":current["source_heads"]["TAKY"],
  "validation":{"total":suite["total"],"failures":suite["failures"],"result":"PASS" if suite["failures"]==0 else "FAIL"},
  "technical_blockers":[],
  "product_open_policy":"PRESERVE_AS_EXPLICIT_CARRY_OVER_OPEN_NOT_BETA_GOVERNANCE_BLOCKER",
  "hosted_runtime_interception":"UNVERIFIED_CONTAINED",
  "deployment":"HOLD",
  "next_after_approval":[
    "mark local Beta snapshot FROZEN with immutable manifest identity",
    "use Frozen Beta only as Alpha input",
    "write Alpha as a new structure rather than appending Beta",
    "run Alpha self-validation, independent cross-validation and regression before implementation/deployment"
  ],
  "manifest":"BETA_REVIEW/BETA_FREEZE_MANIFEST_20261003.json"
}
(OUT/"BETA_FREEZE_READINESS_20261003.json").write_text(json.dumps(readiness,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"manifest":str(OUT/"BETA_FREEZE_MANIFEST_20261003.json"),"readiness":str(OUT/"BETA_FREEZE_READINESS_20261003.json"),"status":readiness["status"]},ensure_ascii=False))
