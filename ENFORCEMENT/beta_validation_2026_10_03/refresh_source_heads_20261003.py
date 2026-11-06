from pathlib import Path
import json

ROOT = Path(r"D:\Git PWA\TAKY_BETA_20261003")

heads = {
    "TAKY": "e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2",
    "Ready-Set": "0c49a2d607c7c26f3ad6ea4ca6fcee4c5b2ad915",
    "Hide-Seek": "5da6594510cc89341054aafef66d5f4ea47a0210",
    "Snap-Pop": "a77e65b383df170e1124d3b9e01ca37eef334d6c",
    "TAKY-MOBILE": "6c90045d1bc1f957325b7daef0c6079b29338f1e",
    "TAKY-ASSETS": "8d902a93dbb7cde3f38580c4f4d0653a4f1314aa",
}
app_to_repo = {
    "READY_SET": "Ready-Set",
    "HIDE_SEEK": "Hide-Seek",
    "SNAP_POP": "Snap-Pop",
    "MOBILE_CATALOG": "TAKY-MOBILE",
    "SHARED_ASSETS": "TAKY-ASSETS",
}

current_path = ROOT / "CURRENT" / "SYSTEM_WIDE_REVIEW.json"
current = json.loads(current_path.read_text(encoding="utf-8"))
current["source_heads"] = heads
current["base_ref"] = heads["TAKY"]
current["evidence_basis"] = (
    "2026-10-02 scope audit preserved as dated snapshots; GitHub default-branch source heads re-queried read-only "
    "on 2026-10-03 for TAKY/Ready-Set/Hide-Seek/Snap-Pop/TAKY-MOBILE/TAKY-ASSETS. "
    "Source-head refresh does not revalidate PR, runtime, device or deployment state."
)
current["live_head_comparison"] = "SOURCE_HEADS_LIVE_MATCH_2026-10-03__REQUERY_BEFORE_LATER_CURRENT_CLAIM__NON_HEAD_SCOPES_RETAIN_PRIOR_EVIDENCE_DATES"
current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

reg_path = ROOT / "OS" / "MOBILE_APP_DEVELOPMENT_REGISTRY.json"
reg = json.loads(reg_path.read_text(encoding="utf-8"))
reg["registry_version"] = "2026-10-03.1-source-head-refresh"
for app, repo in app_to_repo.items():
    gh = reg["apps"][app]["github"]
    gh["main_head"] = heads[repo]
    gh["head_evidence_state"] = "LIVE_REFRESHED_2026-10-03"
    gh["live_refresh_source"] = "GITHUB_READ_ONLY_HEAD_QUERY_2026-10-03"
    gh["head_change_note"] = (
        "Default-branch source head re-queried 2026-10-03 only; "
        "no PR/runtime/device/deployment promotion is implied."
    )
fresh = reg["freshness_policy"]
audit = fresh.setdefault("source_head_audit", {})
audit["at"] = "2026-10-03"
audit["source"] = (
    "GitHub read-only default-branch head verification on 2026-10-03; "
    "this refresh covers source heads only and preserves historical PR/work/deploy evidence dates."
)
audit["apps"] = {app: heads[repo] for app, repo in app_to_repo.items()}
fresh["preserved_evidence_boundary"] = (
    "open_prs, work, runtime, device and deploy details retain their original evidence dates; "
    "the 2026-10-03 refresh updates source heads only."
)
reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

test_path = ROOT / "ENFORCEMENT" / "semantic_current_resolver_test.py"
txt = test_path.read_text(encoding="utf-8")
repls = {
    "ccfb372ed10110121cec5be615c3e3e0c59f3601": heads["TAKY"],
    "daed2ebd072061b870bfd0d2f2472dd344661bad": heads["Ready-Set"],
    "f1c4bd7a61edcfab3c9bb0836db162e38ca2311f": heads["Hide-Seek"],
    "2b9c6941792269244f847b1b978125996a49b5f8": heads["Snap-Pop"],
    "9bcb7d9660834818457704db2c0a5b16c9964c95": heads["TAKY-MOBILE"],
}
for old, new in repls.items():
    txt = txt.replace(old, new)
test_path.write_text(txt, encoding="utf-8")

print("PASS: refreshed source-head evidence only")
