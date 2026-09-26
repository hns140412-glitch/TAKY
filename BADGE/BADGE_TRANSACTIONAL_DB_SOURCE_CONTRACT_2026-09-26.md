# BADGE TRANSACTIONAL AWARD LEDGER — DB PROVIDER CONTRACT — 2026-09-26

## Why this is a correction, not a parallel second authority
Fresh review of Netlify's August 31, 2026 official Knowledge Base guide:
https://www.netlify.com/knowledge-base/how-to-store-files-and-objects-with-netlify-blobs/
states that per-user transactional data, balances and read-modify-write invariants belong in a transactional database such as Netlify DB; Blobs conditional ETag writes are not a substitute for database transactions. The primitive API does support `onlyIfNew` / `onlyIfMatch`, per https://docs.netlify.com/build/data-and-storage/netlify-blobs/ , but that alone does not establish the full application transaction, crash-recovery, external anti-rollback and privilege model.

There is also a public Netlify SDK issue (status requires release-specific verification before production) describing conditional writes returning `modified:true,etag:''` on some non-412 failures:
https://github.com/netlify/primitives/issues/741

The previous `badge-award-ledger-cas-store.js` and its passed isolated CAS simulation are **preserved as experimental compatibility/research evidence, NOT the selected production provider**. Its constructor now requires `experimentalNonProduction:true` and refuses Netlify `CONTEXT=production`. This is only an intent guard, not a security boundary. Nothing in prior CI proved real Netlify Blobs is safe for financial/gem or multi-table achievement transactions.

## Actual new code
`BADGE/badge-award-ledger-postgres.sql`: explicit PostgreSQL migration draft for two family+child+badge-scoped tables:
- `taky_badge_award_head`: PK scope, current signed checkpoint and count.
- `taky_badge_award_event`: immutable sequenced events, scoped unique decision_id, award_id and ledger_sequence, foreign key `ON DELETE RESTRICT`.
- Signed `record_json` stays **TEXT**, not JSONB, because JSONB normalizes/reorders canonical JSON and would invalidate the original per-record HMAC input. The server verifies the JSON and signature on replay.

`BADGE/badge-award-ledger-transactional.js`: server-only `createTransactionalAwardLedger({pool,family_id,signingKey,verifyDecision,isBadgeActive,now})` and the existing `TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1` source interface.

- Injected `pool.connect()` supports parameterized PostgreSQL queries, explicit BEGIN/COMMIT/ROLLBACK.
- On first write, idempotent `INSERT ... ON CONFLICT DO NOTHING` makes the aggregate head. `SELECT ... FOR UPDATE` serializes writers for exactly that family+child+badge.
- Within **one transaction**, verify full existing signed chain and head checkpoint, reject duplicate Decision, check required INITIAL_AWARD or REAWARD in sequence, recheck trusted active catalog/child authorization, stamp actual `awarded_at`, INSERT immutable signed event, UPDATE head count/checkpoint with the previous-count/checkpoint guard, COMMIT. On failure or denial ROLLBACK everything (including a newly inserted head).
- Reads use `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY` for a consistent head+event snapshot. Signed ledger row verification and bridge to first/reaward/promotion/history/KST calendar use the exact same source contract as the tested Node ledger; no duplicate owner of achievements.
- No accepted app/LLM activity, family praise gift, approved catalogue draft or browser-supplied `approved` flag can mint a record. All verification capabilities must come from a trusted server.

## What tests prove, and what remains unproven
`BADGE/badge-award-ledger-transactional.test.js` uses an explicit in-memory fake that implements BEGIN, row-level lock, SQL shape, snapshot, rollback, commit and uniqueness. It verifies distinct concurrent REAWARDs both survive, same Decision is rejected once, a failure after event INSERT but before head UPDATE removes the entire attempted transaction, tamper or signing-key mismatch fails, a previously read checkpoint goes stale, KST calendar derives the correct records, family scope isolation and no draft auto-activation. CI checks module syntax and the SQL migration's essential constraints.

**This is not a live PostgreSQL integration test** and does not create a DB, server key, site env, authorized Decision source or operational user API. Before approval: actual isolated Postgres migration/role permissions; real `pg` pool and server-only credentials; actual provider-verified member session and active approved catalogue; production-only read/write routing; migration from legacy sources with no loss; DB backup and external/independent high-watermark audit against complete historical rollback; schema/transaction integration tests in a real isolated DB; quota and free-tier check. No Netlify calls, production deploy, 60 draft activation, 20 auto-awards or Gem Wallet changes authorized.

## Cross-app status inherited
Ready-Set combined DRAFT #112 exact head `6d29015bf84893877ff47dcc6d9b8d5376ddea09`: all CI SUCCESS, 53 Chromium Playwright tests. Its day/week badge rail has **no live trusted reader**. Snap-Pop DRAFT #9 exact head `7652c3fb0ec99796768f3993b05cf7c0946dcd9e`: 7 browser tests, read-only record UI and no caching of personal /api responses, also no live trusted reader. Neither PR is merged/deployed due to main→Netlify gate. Do not re-open their CLOSED isolated UI regressions without new evidence.
