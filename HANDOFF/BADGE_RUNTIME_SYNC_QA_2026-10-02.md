# TAKY Badge Runtime Sync QA — 2026-10-02

Status: BADGE_RUNTIME_SYNC=PASS / BADGE_CODEX_UI=PASS / FULL_APP_BROWSER_RUNTIME=PASS / PWA_PREDEPLOY_STATIC=PASS / DEPLOYMENT=HOLD

## Binary delivery
- Canonical art remains Library PNG 001..060.
- Runtime derivative: 512x512 WebP Q82.
- Physical delivery: 10 binary shards, 6 badges per shard.
- Snap-Pop target: `assets/badges/current/shards/taky-badge-art-shard-01..10.bin`.
- Shard manifest: `data/badge-art-shard-manifest.json`.
- Resolver: `badge-art-pack-runtime.js`.
- Total extracted WebP payload: 3,879,972 bytes.
- Total shard container bytes: 3,891,414 bytes.
- Each shard SHA-256 and each extracted WebP SHA-256 are verified before rendering.
- Missing/corrupt shard fails closed; no replacement art is generated.

## Badge codex verification
- 60/60 tiles resolve through stable badge_id / visual_id / asset_slot_id.
- 60/60 runtime images load from blob URLs after scroll; no failed image.
- Mobile QA viewport: 390 x 844 CSS px, DPR 2.
- Horizontal overflow: NONE.
- Nature filter controls: ALL + 8 semantic groups.
- Nature grouped view: 8/8 groups rendered.
- Detail sheet: art / number / category / primary_nature / title / story / ownership state render correctly.
- POCKET / FIELD / EXPEDITION / SECRET remains separate from semantic nature classification.

## Full browser runtime verification
- Fresh headless Chrome profile: PASS.
- app init: PASS.
- IndexedDB: OPEN.
- Full browser runtime self-test: PASS.
- PWA reload recovery probe: PASS.
- PWA offline shell cache: PASS.
- Service worker cache: `snap-pop-2026-10-02-badge-shards-v1`.
- Badge-specific first-award policy verified: first award = GREEN + 0 reacquire stars.
- Reacquire star range verified: 0..5; 5 reawards promote tier and reset to 0.
- Static validators PASS:
  - badge visual compositor
  - DOM binding integrity
  - PWA predeploy precache
  - Snap predeploy readiness contract

## Correction to earlier regression note
The earlier OPEN_DB / MIGRATE timing diagnosis is superseded. A fresh-profile rerun showed init PASS / DB OPEN.
The actual latest branch failure was a stale self-test that still expected the old 1..5 star model. The runtime had already moved to the approved 0..5 reacquire-star contract. The stale browser and visual-compositor validators were corrected, after which the full runtime smoke and PWA recovery tests passed.

## Replacement invariant
Later source-art revisions keep badge_id / visual_id / asset_slot_id fixed.
Replace canonical PNG -> update source SHA/revision -> regenerate WebP -> rebuild only the owning shard -> update shard/entry SHA metadata.

## Remaining OPEN
- Final visual polish / real-device QA can continue without changing badge identity or award logic.
- Main merge / Netlify deployment remain HOLD by current project deployment policy.
