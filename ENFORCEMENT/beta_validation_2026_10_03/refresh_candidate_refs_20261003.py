from pathlib import Path
import json

ROOT = Path(r"D:\Git PWA\TAKY_BETA_20261003")
p = ROOT / "CURRENT" / "SYSTEM_WIDE_REVIEW.json"
d = json.loads(p.read_text(encoding="utf-8"))
scopes = {x["id"]: x for x in d["scopes"]}

def mark(scope_id, **fields):
    scopes[scope_id].update(fields)

mark("exploration_crew_central_runtime",
     pr_state="DRAFT/OPEN",
     head_ref="d2eecf35ebb1f46de7b18589442b07d3e11919c6",
     head_verification="LIVE_VERIFIED_2026-10-03",
     promotion_state="REAPPLY_OR_REBASE_ON_LATEST_MAIN_REQUIRED",
     main_compare={"ahead":154,"behind":96,"status":"diverged"})

mark("exploration_crew_hide_consumer_v2",
     head_ref="c876a8167be28a2f30a69fd0a0f38f74987abb3c",
     head_verification="LIVE_VERIFIED_2026-10-03",
     promotion_state="REAPPLY_ON_LATEST_MAIN_REQUIRED",
     main_compare={"ahead":1,"behind":2,"status":"diverged"})

mark("exploration_crew_snap_consumer_v2",
     head_ref="bceb6cc9b336447002a4c189fa1560efc3c4ae5e",
     head_verification="LIVE_VERIFIED_2026-10-03",
     promotion_state="REAPPLY_ON_LATEST_MAIN_REQUIRED",
     main_compare={"ahead":1,"behind":2,"status":"diverged"})

badge = scopes["badge_central"]
badge.update({
    "pr_state":"DRAFT/OPEN",
    "head_ref":"52498dbc09a8db1f50cd7d5d3fe437c5e0c34a69",
    "head_verification":"LIVE_VERIFIED_2026-10-03",
    "promotion_state":"REAPPLY_OR_REBASE_ON_LATEST_MAIN_REQUIRED",
    "main_compare":{"ahead":186,"behind":84,"status":"diverged"},
    "candidate_refs":{
        "TAKY-MOBILE":{
            "pr":2,
            "head":"02bb7fae93dcc5c15b2e7384875075a83e7451c1",
            "state":"MERGED/CLOSED",
            "merged":True,
            "main_head":"6c90045d1bc1f957325b7daef0c6079b29338f1e",
            "note":"Central badge transport PR merged; later main commits extend badge/auth transport."
        },
        "Ready-Set":{
            "pr":143,
            "head":"5c1a1fba5c9fe3945957a2c6ab6ac0eb57b86b93",
            "state":"DRAFT/OPEN",
            "promotion_state":"REAPPLY_ON_LATEST_MAIN_REQUIRED",
            "main_compare":{"ahead":142,"behind":1,"status":"diverged"}
        },
        "Hide-Seek":{
            "pr":29,
            "head":"0d8af51e8b47f561659135a18ed5c4a0e1304419",
            "state":"DRAFT/OPEN",
            "promotion_state":"REAPPLY_ON_LATEST_MAIN_REQUIRED",
            "main_compare":{"ahead":32,"behind":1,"status":"diverged"}
        },
        "Snap-Pop":{
            "pr":20,
            "head":"fac7cc264a9d003c4576612ebdd53f55e4bf90e9",
            "state":"DRAFT/OPEN",
            "promotion_state":"REAPPLY_ON_LATEST_MAIN_REQUIRED",
            "main_compare":{"ahead":1237,"behind":18,"status":"diverged"},
            "note":"Very large divergence; do not promote directly."
        }
    }
})

mark("design_to_ui",
     pr_state="DRAFT/OPEN",
     head_ref="9ab5fc579ada0547d5bb7cc066a157c4912bc0f1",
     head_verification="LIVE_VERIFIED_2026-10-03",
     promotion_state="REAPPLY_OR_REBASE_ON_LATEST_MAIN_REQUIRED",
     main_compare={"ahead":83,"behind":94,"status":"diverged"})

mark("assets_approved_results_pointer_contract",
     pr_state="DRAFT/OPEN",
     head_ref="319968689148ad898932ecd97b4f509bb30fd977",
     head_verification="LIVE_VERIFIED_2026-10-03",
     promotion_state="FAST_FORWARD_CAPABLE_BUT_HOLD_NO_MERGE",
     main_compare={"ahead":21,"behind":0,"status":"ahead"})

p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

test = ROOT / "ENFORCEMENT" / "semantic_current_resolver_test.py"
txt = test.read_text(encoding="utf-8")
txt = txt.replace("de9ca733168bdace6b114b147ffc95ec7c09f064",
                  "52498dbc09a8db1f50cd7d5d3fe437c5e0c34a69")
txt = txt.replace("b42f7e2d0fdf220e552817c41629c5384034888b",
                  "02bb7fae93dcc5c15b2e7384875075a83e7451c1")
test.write_text(txt, encoding="utf-8")
print("PASS: refreshed candidate PR pointers and promotion boundaries")
