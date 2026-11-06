from pathlib import Path
import json, hashlib, datetime

ROOT = Path(r"D:\Git PWA\TAKY_ALPHA_20261003")
ALPHA = ROOT / "ALPHA"
REVIEW = ROOT / "ALPHA_REVIEW"
TODAY = "2026-10-04"

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def save(rel, obj):
    (ROOT / rel).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def sha256(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

current = load("ALPHA/TAKY_ALPHA_CURRENT_V0_1.json")
if current.get("status") != "SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL_NONCANONICAL":
    raise SystemExit("PRECONDITION_CURRENT_STATUS")

required_pass = [
    "ALPHA_REVIEW/ALPHA_READONLY_VALIDATION_20261004.json",
    "ALPHA_REVIEW/ALPHA_COVERAGE_DEPTH_VALIDATION_20261004.json",
    "ALPHA_REVIEW/ALPHA_PIPELINE_VALIDATION_20261004.json",
    "ALPHA_REVIEW/ALPHA_LANE_BOUNDARY_VALIDATION_20261004.json",
    "ALPHA_REVIEW/ALPHA_ADVERSARIAL_VALIDATION_20261004.json",
]
for rel in required_pass:
    if load(rel).get("status") != "PASS":
        raise SystemExit("PRECONDITION_VALIDATION_FAIL:" + rel)

suite = load("ENFORCEMENT/alpha_validation_2026_10_03/beta_full_suite_v2.summary.json")
if suite.get("total") != 132 or suite.get("failures") != 0:
    raise SystemExit("PRECONDITION_BETA_REGRESSION")

a8 = (ROOT / "ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt").read_text(encoding="utf-8")
if "A8_PASS_SYSTEM_ALPHA_STRUCTURALLY_READY_FOR_A9" not in a8:
    raise SystemExit("PRECONDITION_A8")

main_refresh = load("ALPHA_REVIEW/ALPHA_MAIN_REFRESH_EVIDENCE_20261004.json")
if not (
    main_refresh.get("compare_status") == "identical"
    and main_refresh.get("ahead_by") == 0
    and main_refresh.get("behind_by") == 0
    and main_refresh.get("baseline") == "e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2"
):
    raise SystemExit("PRECONDITION_MAIN_DIVERGED")

evidence_hashes = {rel: sha256(rel) for rel in required_pass}
evidence_hashes["ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt"] = sha256("ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt")
evidence_hashes["ALPHA_REVIEW/ALPHA_MAIN_REFRESH_EVIDENCE_20261004.json"] = sha256("ALPHA_REVIEW/ALPHA_MAIN_REFRESH_EVIDENCE_20261004.json")
evidence_hashes["ENFORCEMENT/alpha_validation_2026_10_03/beta_full_suite_v2.summary.json"] = sha256("ENFORCEMENT/alpha_validation_2026_10_03/beta_full_suite_v2.summary.json")

receipt = {
    "schema": "TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_V1",
    "date": TODAY,
    "promoted_at_local": datetime.datetime.now().astimezone().isoformat(),
    "status": "LOCAL_CANONICAL_ORCHESTRATION_PROMOTED",
    "human_approval": {
        "approved": True,
        "approval_scope": "LOCAL_CANONICAL_ALPHA_ORCHESTRATION_ONLY",
        "source": "CURRENT_CHAT_EXPLICIT_GO_A10",
        "does_not_authorize": ["PUSH", "MERGE", "DEPLOY", "NETLIFY", "PAID_API"]
    },
    "main_refresh": main_refresh,
    "frozen_beta_snapshot_identity_sha256": current.get("frozen_beta_snapshot_identity_sha256"),
    "evidence_sha256": evidence_hashes,
    "scope": {
        "canonicalized": [
            "Alpha orchestration graph",
            "app/engine structural coverage model",
            "pipeline structural coverage model",
            "runtime contract structural model",
            "claim-dimension boundaries",
            "OPEN/HOLD classification and routing"
        ],
        "not_canonicalized_or_not_closed": [
            "Planner dedicated owner document",
            "Badge canonical owner",
            "SAVEY canonical owner",
            "product runtime gaps",
            "device verification",
            "deployment",
            "production verification",
            "post-freeze local candidate registry rules"
        ],
        "semantic_owner_transfer": False,
        "existing_domain_semantic_owners_preserved": True
    },
    "claim_boundary": "LOCAL_CANONICAL_ORCHESTRATION_NE_GITHUB_MAIN_MUTATION_NE_PRODUCT_RUNTIME_COMPLETE_NE_DEPLOYED",
    "release_boundary": {
        "push": "HOLD",
        "merge": "HOLD",
        "deploy": "HOLD",
        "netlify": "HOLD",
        "paid_api": "HOLD"
    }
}
save("ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json", receipt)

master_path = ALPHA / "TAKY_ALPHA_MASTER_V0_1.md"
master = master_path.read_text(encoding="utf-8")
master = master.replace(
    "> Status: **DRAFT / NON-CANONICAL**",
    "> Status: **LOCAL CANONICAL ORCHESTRATION / GITHUB MAIN UNCHANGED**"
)
master = master.replace(
    "> Rule: Alpha is a new orchestration structure. It does **not** replace existing canonical owners until validation and explicit human promotion.",
    "> Rule: Alpha is the locally promoted canonical orchestration structure. It **does not replace or absorb existing domain semantic owners**; owner authority remains registry-resolved."
)
master = master.replace(
    "> Version note: **V0.1 is an Alpha draft label, not a TAKY canonical Revision.** Canonical revision governance remains owned by 'MASTER/REVISION_GOVERNANCE.md'.",
    "> Version note: **V0.1 is the promoted local Alpha orchestration baseline, not a GitHub-main TAKY revision.** Revision governance remains owned by 'MASTER/REVISION_GOVERNANCE.md'."
)
master = master.replace(
    "## 20. Current Alpha State\n'DRAFT / NON-CANONICAL / LOCAL ONLY'.\nNo push, merge, deployment or paid API action is authorized by creation of this Alpha draft.",
    "## 20. Current Alpha State\n'LOCAL CANONICAL ORCHESTRATION / GITHUB MAIN UNCHANGED'.\nA10 human promotion is approved for the local orchestration baseline only. No push, merge, deployment, Netlify or paid API action is authorized."
)
master = master.replace(
    "- A10 human canonical-promotion gate remains PENDING.",
    "- A10 human local-canonical promotion gate: PASS."
)
master = master.replace(
    "SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL != CANONICAL_ALPHA_PROMOTED != PRODUCT_RUNTIME_COMPLETE != DEPLOYED.",
    "SYSTEM_ALPHA_LOCAL_CANONICAL_ORCHESTRATION != GITHUB_MAIN_PROMOTED != PRODUCT_RUNTIME_COMPLETE != DEPLOYED."
)
section = """## 25. A10 Local Canonical Promotion — 2026-10-04
Human approval was explicitly given for local canonical promotion after A0–A9 PASS.
GitHub main was refreshed before promotion and was identical to the Frozen Beta baseline (e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2), so no rebase/reapplication was required for this local A10 decision.

This promotion canonicalizes the Alpha orchestration and structural coverage layer only. It does not transfer semantic ownership from existing domain owners and does not silently resolve Planner/Badge/SAVEY owner gaps or product/runtime OPEN items.

Promotion receipt: ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json.

Release boundary remains: PUSH / MERGE / DEPLOY / NETLIFY / PAID_API = HOLD.
"""
if "## 25. A10 Local Canonical Promotion" not in master:
    master = master.rstrip() + "\n\n" + section + "\n"
master_path.write_text(master, encoding="utf-8")

authority = load("ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json")
authority["status"] = "LOCAL_CANONICAL_ORCHESTRATION"
authority["date"] = TODAY
authority["promotion"] = {
    "state": "A10_PASS_LOCAL_CANONICAL",
    "receipt": "ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json",
    "semantic_owner_transfer": False,
    "github_main_mutated": False,
    "main_refresh_evidence": "ALPHA_REVIEW/ALPHA_MAIN_REFRESH_EVIDENCE_20261004.json"
}
rules = authority.setdefault("authority_rules", [])
for old in [
    "ALPHA_DRAFT_DOES_NOT_OVERRIDE_CANONICAL_OWNERS",
    "HUMAN_APPROVAL_REQUIRED_FOR_CANONICAL_PROMOTION_AND_DEPLOYMENT",
]:
    if old in rules:
        rules.remove(old)
for new in [
    "LOCAL_CANONICAL_ALPHA_ORCHESTRATION_DOES_NOT_OVERRIDE_DOMAIN_SEMANTIC_OWNERS",
    "A10_LOCAL_PROMOTION_APPROVED__MERGE_AND_DEPLOYMENT_REMAIN_SEPARATE_HUMAN_GATES",
]:
    if new not in rules:
        rules.append(new)
save("ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json", authority)

validation = load("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json")
validation["status"] = "LOCAL_CANONICAL_PROMOTION_PASS"
validation["date"] = TODAY
validation.setdefault("latest_structural_evidence", {})["A10"] = "ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json"
validation["promotion_boundary"] = {
    "local_canonical_orchestration": "PASS",
    "github_main_promotion": "NOT_PERFORMED",
    "semantic_owner_transfer": False,
    "push": "HOLD",
    "merge": "HOLD",
    "deploy": "HOLD",
    "netlify": "HOLD",
    "paid_api": "HOLD"
}
save("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json", validation)

open_plan = load("ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json")
open_plan["date"] = TODAY
open_plan["status"] = "LOCAL_CANONICAL_ORCHESTRATION_WITH_EXPLICIT_OPEN"
for item in open_plan.get("items", []):
    if item.get("id") == "A10_HUMAN_PROMOTION":
        item.update({
            "state": "CLOSED_PASS_LOCAL_CANONICAL",
            "blocks_structural_alpha": False,
            "blocks_canonical_promotion": False,
            "evidence": "ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json"
        })
save("ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json", open_plan)

carry = load("ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json")
carry["date"] = TODAY
for item in carry.get("classes", []):
    if item.get("id") == "ALPHA_HUMAN_PROMOTION":
        item["state"] = "CLOSED_A10_LOCAL_CANONICAL_PASS"
        item["evidence"] = "ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json"
save("ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json", carry)

trace = load("ALPHA/TAKY_ALPHA_SOURCE_TRACE_V0_1.json")
trace["date"] = TODAY
if not any(x.get("alpha_concept") == "A10 local canonical orchestration promotion" for x in trace.get("items", [])):
    trace.setdefault("items", []).append({
        "alpha_concept": "A10 local canonical orchestration promotion",
        "classification": "HUMAN_APPROVED_LOCAL_PROMOTION",
        "sources": [
            "ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json",
            "ALPHA_REVIEW/ALPHA_MAIN_REFRESH_EVIDENCE_20261004.json"
        ],
        "authority_transfer": False,
        "semantic_owner_transfer": False
    })
trace["rule"] = "Alpha orchestration is locally canonical after A10; domain semantic ownership remains with declared owners and GitHub main is unchanged."
save("ALPHA/TAKY_ALPHA_SOURCE_TRACE_V0_1.json", trace)

current.update({
    "status": "SYSTEM_ALPHA_LOCAL_CANONICAL_ORCHESTRATION",
    "a10": "PASS_LOCAL_CANONICAL_HUMAN_APPROVED",
    "promotion_receipt": "ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json",
    "github_main_refresh": "IDENTICAL_TO_FROZEN_BASELINE_E7CA5C7",
    "semantic_owner_transfer": False,
    "github_main_mutated": False,
    "claim_boundary": "LOCAL_CANONICAL_ORCHESTRATION_NE_GITHUB_MAIN_PROMOTED_NE_PRODUCT_RUNTIME_COMPLETE_NE_DEPLOYED",
    "next": "CONTINUE_EXPLICIT_PRODUCT_RUNTIME_OPEN_WITHOUT_REOPENING_A0_A10"
})
save("ALPHA/TAKY_ALPHA_CURRENT_V0_1.json", current)
save("ALPHA_REVIEW/ALPHA_SYSTEM_WIDE_STATUS_20261004_FINAL.json", current)

print("A10_LOCAL_CANONICAL_PROMOTION_APPLIED")
