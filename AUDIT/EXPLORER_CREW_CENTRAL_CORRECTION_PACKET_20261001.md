# Explorer Crew Central Correction Packet — 2026-10-01

Status: REVIEWED DRAFT / CENTRAL APPLY CANDIDATE / MAIN·ROOT·NETLIFY HOLD

Authority lock:
- TAKY main: 55547a7c4c859a1aae700405fdba4a302a2c20d3
- Central runtime owner: OS/EXPLORATION_CREW_CANONICAL.md
- Canonical blob: b9729070effec2b4b834d64e7d8223b20851c171
- Relationship owner: OS/GUIDE_CHARACTER_RELATIONSHIP.md
- Snap-Pop main: 3de97be0d12dd6244a942b0c137c2efe578a43b6
- Draft PR #10 exact HEAD: 2ae8c4f6cda81dd42eed3e89700f3bcf9b09f31a

Verified candidate facts:
- first encounter remains Core6 only
- relation / memory / Main runtime roster is all 24
- 07–24 may become Main after relationship gates
- Main change preserves previous relation / affinity / memory
- ID24 canonical is VIVI; legacy NOVA is lineage only
- 13–18 personality is user-authorized derived provenance, not literal board keywords
- semantic interaction and delivery are separate axes
- Runtime Policy is thin arbitration only
- Story Gate requires explicit evidence and is separate from affinity
- static → composable → motion are separate promotion gates
- canonical render-plan consumer is not a behavior or asset owner

Fresh correction-relevant regression:
- EXPLORER_CREW_APPROVED_PERSONALITY_BOARD_V2 PASS
- EXPLORER_CREW_24_COMPANION_SWITCH_V1 PASS
- EXPLORER_CREW_ROLE_BEHAVIOR_INTEGRATION_V1 PASS
- EXPLORER_CREW_SEMANTIC_COMPAT_V1 PASS
- EXPLORER_CREW_RUNTIME_POLICY_WIRED_V1 PASS
- EXPLORER_CREW_STORY_GATE_WIRED_V1 PASS
- EXPLORER_CREW_RUNTIME_LOG_WIRED_V1 PASS
- EXPLORER_CREW_ASSET_RENDER_WIRED_V1 PASS
- CANONICAL_RENDER_PLAN_DOM_CONSUMER_V1 PASS
- CREW_CORRECTION_COMMON_SHA across Snap / Hide / Ready PASS

Explicit non-targets:
- no initial 5–6 selection restoration
- no Core6-only runtime restoration
- no asset-readiness relationship gate
- no PR #10 whole-branch merge/rebase
- no Special Friend inference from Random Guest
- no composable/motion production promotion
- no image generation
- no main / ROOT / Netlify release

Asset mismatch classification:
Legacy asset-integrity hashes mutable onboarding/index.html as source_file.
Current mismatch is LEGACY_GATE_SCOPE_MISMATCH, not evidence that approved character/cutout bytes are corrupt.
Approved asset hashes must not be rewritten or regenerated to silence this mismatch.


## Runtime V2 cutover evidence — 2026-10-01

Canonical V2:
- TAKY Draft PR #193 remains Draft / unmerged / main HOLD.
- Runtime V2 ownership is now enforced as `EXPLORER_CREW_SYSTEM_V2` + `runtime = CANONICAL_ONLY`.
- App consumer ownership flags are all false for behavior / relation / memory / asset resolution / runtime ownership.
- Central `Explorer Crew Canonical Correction` CI: SUCCESS.
- Central `TAKY Enforcement Replay` CI: SUCCESS.

Three-app candidate heads:
- Snap-Pop Draft PR #17: `e928067cd8f79b954b4072bfabe13e891fb6d07e`
  - base: `taky/companion-onboarding-candidate-2026-09-27`
  - ahead 2 / behind 0 / mergeable
  - `Validate Snap & Pop`: SUCCESS
  - `Companion Onboarding Source/Asset Gate`: SUCCESS
- Hide-Seek Draft PR #27: `fbec00eb9f0dc6a91111a8bcba6c5d35197d6e4d`
  - base: `taky/hide-living-background-v5-bind-20260930`
  - ahead 3 / behind 0 / mergeable
  - `Validate Hide & Seek`: SUCCESS
  - `Validate Hide Runtime V2`: SUCCESS
  - local full browser regression: 102/102 PASS
- Ready-Set Draft PR #135: `2d6ace779b697a7b52e4179d75252f9784c94443`
  - rebased-by-reapplication onto latest main `bb0f109fb9983140622279c05d5847e863addac0`
  - ahead 2 / behind 0 / mergeable
  - Ready Integration CI: SUCCESS
  - Ready Runtime E2E: SUCCESS
  - Weekly / Daily Availability, Hide Memory Roundtrip, worker self-test: SUCCESS
  - latest-main reapplication core contracts + actual browser V2 consumer: PASS

Common-source lock:
- scope: 34 shared runtime/contract files
- algorithm: SHA-256
- normalization: UTF-8 text with CRLF/LF normalized to LF before hashing
- Snap / Hide / Ready normalized Source Lock verification: PASS
- purpose: prevent cross-app common-runtime drift without making line-ending style or host OS part of semantic identity

Cutover readiness:
- canonical owner boundary: PASS
- 24-person roster / Core6 first-encounter boundary: PASS
- relation / affinity / memory preservation: PASS
- Runtime Policy thin-owner boundary: PASS
- approved static Visual ID/SHA preservation: PASS
- common runtime content identity: PASS
- project consumer integration: PASS
- regression / CI: PASS

Release authorization:
- `CUTOVER_READINESS=PASS`
- `MAIN_MERGE_AUTHORIZATION=HOLD`
- `ROOT_ACTIVATION=HOLD`
- `NETLIFY=HOLD`
- `IMAGE_GENERATION=HOLD`
- `COMPOSABLE_PRODUCTION_PROMOTION=HOLD`
- `MOTION_RELEASE=HOLD`

Promotion note:
- Snap PR #17 targets the Snap candidate branch, not Snap main.
- Hide PR #27 targets the verified Hide V5 branch, not Hide main.
- Ready PR #135 targets Ready main directly but remains Draft/HOLD.
- Therefore green Draft evidence is not itself production cutover and must not be interpreted as permission to merge or deploy.
