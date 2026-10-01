# TAKY Badge Runtime Sync QA — 2026-10-02

Status: BADGE_RUNTIME_SYNC=PASS / FULL_APP_DEPLOYMENT=HOLD

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

## Runtime verification
- GitHub branch contains 10/10 shard files with expected Git blob SHA and byte sizes.
- Catalog data: 60/60 asset slots marked SYNCED_SHARDS.
- JS syntax PASS: shard loader, catalog runtime, catalog controller, self-test, app, service worker.
- Badge-specific browser runtime self-test: PASS.
  - pack loaded
  - 60 runtime blob URLs resolved
  - 60 per-entry SHA metadata matches catalog runtime SHA
  - 60 unique badge IDs / visual IDs / asset slots
  - nature taxonomy/filter/sort contract present
- Isolated production controller/style render QA: PASS, 60 tiles rendered from the synced shards.

## Regression note
A full-app headless smoke run remains blocked at app initialization/migration timing in a fresh headless profile. The same failure is reproducible on the unmodified Snap-Pop base branch (`taky/snap-pop-implementation-2026-09-20`), so it is not classified as a badge regression. Full app merge/deploy remains HOLD until the inherited initialization issue is handled by the broader Snap runtime pipeline.

## Replacement invariant
Later source-art revisions keep badge_id / visual_id / asset_slot_id fixed. Replace canonical PNG -> update source SHA/revision -> regenerate WebP -> rebuild only the owning shard -> update shard/entry SHA metadata.
