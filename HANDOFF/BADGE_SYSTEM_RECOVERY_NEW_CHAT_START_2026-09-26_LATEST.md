# BADGE SYSTEM RECOVERY — NEW CHAT START — 2026-09-26 LATEST

Status: PARTIAL / HOLD-SAFE  
Scope lock: BADGE SYSTEM RECOVERY ONLY  
Do not switch to DATA INDEXING / vector work.  
USER != DEBUGGER.

## 0. HARD LOCK

Resume in this order:

INHERIT APPROVED STATE  
→ restore BADGE CURRENT  
→ verify exact app heads / PR heads  
→ inherit CLOSED  
→ execute only remaining OPEN

Do not reopen CLOSED without new regression evidence.

## 1. Historical catalog

- 60 historical badge catalog: recovered.
- State: `WORKING_DRAFT_NOT_ACTIVE`.
- Auto canonicalize: FORBIDDEN.
- Auto activate: FORBIDDEN.
- Auto award: FORBIDDEN.

## 2. CLOSED inherited

- Achievement Decision: implemented.
- Award Ledger: implemented.
- Candidate Review: implemented.
- Hide/Snap badge-source auto-inference prohibition regression: verified.

## 3. SP-BADGE-006

State: `IMPLEMENTATION_CLOSED_CANDIDATE_MAIN_NOT_MERGED`

Repository: `hns140412-glitch/Hide-Seek`  
Draft PR: #17  
Exact head: `93aa625f91e027cfd6bc212e2b74d8418d3f9b81`

Implemented:
- real child-authored self-reflection UX producer after TEST_READY;
- evidence emitted only after explicit child selections + explicit confirmation;
- evidence type = `SELF_REFLECTION_EVIDENCE`;
- `verified_outcome=null`;
- direct mastery authority forbidden;
- direct award forbidden;
- Candidate Review required;
- telemetry-driven inference for `ERROR_DISCOVERY / DEEP_THINKING / SPECIAL_BEHAVIOR` forbidden.

CI:
- Learning Runtime Bridge Validation = SUCCESS
- Validate Hide & Seek = SUCCESS

Remaining OPEN:
- merge decision for draft PR #17;
- after merge, exact-main regression only.

## 4. SP-BADGE-008

State: `IMPLEMENTATION_CLOSED_CONTENT_APPROVAL_HOLD`

Repository: `hns140412-glitch/Snap-Pop`  
Draft PR: #8  
Exact head: `94c637fc87983a490ebf1047a07f108474b5dca1`

World / Theme:
- reviewed runtime scene `assets/world/golden_world_scene.jpg` explicitly bound;
- state = `IMPLEMENTATION_CLOSED_CANDIDATE_MAIN_NOT_MERGED`;
- `assets/reference/approved_visual_source.png` remains reference/lineage only;
- reference-board direct runtime binding forbidden;
- automatic asset promotion forbidden;
- automatic RELEASE PASS forbidden.
- `assets/character/character_master_hd.jpg` and `assets/guide/maltipoo_guide_hd.jpg` are initial lineage assets, NOT reviewed individual Crew binding evidence.
- Ready Core 6 Visual IDs SHALL NOT be auto-imported into Snap; project visual authority is owner-scoped.

Crew Visual:
- implementation state = `CLOSED`.
- content state = `CONTENT_APPROVAL_HOLD`.
- Snap-owned Crew Asset Approval Gate/Registry is implemented.
- runtime binding requires `owner=snap-pop`, `APPROVED_RUNTIME_ASSET`, explicit user confirmation and review evidence.
- initial `character_master_hd.jpg` / `maltipoo_guide_hd.jpg` remain lineage-only and cannot satisfy approval.
- Ready Core 6 cross-app auto import remains forbidden.
- Do not invent or auto-promote a Crew asset.
- Actual reviewed/approved individual Crew asset remains a content dependency, not an implementation gap.

CI:
- Validate Snap & Pop = SUCCESS

Remaining OPEN:
- actual Snap-owned reviewed/approved individual Crew/Character asset approval/content;
- merge decision for draft PR #8;
- post-merge exact-main regression.

Do NOT reopen SP-BADGE-008 implementation merely because approved Crew content is not yet supplied.

## 5. Ready World State consumer

State: `IMPLEMENTATION_CLOSED_CANDIDATE_MAIN_NOT_MERGED`

Repository: `hns140412-glitch/Ready-Set`  
Draft PR: #105  
Exact head: `ccccdbf3077ab055f1c6d964ba8988ebf1656bff`

Implemented:
- Ready consumes reviewed World State / Theme Expression only;
- Ready does not own World State;
- Ready does not mutate Crew identity;
- unreviewed World/Crew visual rejected;
- reference-board direct binding forbidden;
- automatic asset promotion forbidden;
- automatic badge activation forbidden;
- automatic award forbidden.

Exact-head CI:
- Learning Runtime Bridge Validation = SUCCESS
- Ready Integration CI = SUCCESS
- Planner Free Window Gate = SUCCESS
- Ready Runtime E2E = SUCCESS

Remaining OPEN:
- merge decision for draft PR #105;
- after merge, exact-main verification.

## 6. Do not regress

Do not:
- reactivate the 60 historical catalog;
- infer `ERROR_DISCOVERY / DEEP_THINKING / SPECIAL_BEHAVIOR` from telemetry;
- turn correct/incorrect learning telemetry directly into badge awards;
- treat a reference image as a reviewed runtime asset;
- let Ready become World State owner;
- switch this recovery session into DATA INDEXING/vector work.

## 7. Next execution order

1. Keep SP-BADGE-006 implementation closed candidate.
2. Keep SP-BADGE-008 World/Theme closed candidate.
3. Keep Crew content in CONTENT_APPROVAL_HOLD; implementation stays CLOSED unless regression evidence appears.
4. Merge draft PRs only by intentional decision.
5. After any merge, verify exact main heads and rerun regressions.
6. Only then promote corresponding items from candidate to final CLOSED.
