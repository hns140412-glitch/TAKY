> **STATUS CORRECTION — SUPERSEDED FOR PRODUCTION CHOICE, 2026-09-26.** Preserve this document as historical CAS experiment only. Netlify's August 31, 2026 official guide says user-level transactional data and read-modify-write invariants belong in a transactional DB, not Blobs even with conditional retries. The CAS module now requires `experimentalNonProduction:true`. Latest implementation authority for a production candidate is `BADGE/BADGE_TRANSACTIONAL_DB_SOURCE_CONTRACT_2026-09-26.md`. No actual database or production deployment has been activated.\n\n# MULTI-INSTANCE SIGNED AWARD LEDGER — CONDITIONAL CAS PROVIDER — 2026-09-26

## Open addressed
The original `BADGE/badge-award-ledger-store.js` uses safe local Node exclusive filesystem locks and immutable signed chained rows but is **not** a multi-instance Netlify persistence adapter. Ready's current `ready-sync-core.js` uses ordinary remote `get/set`; it is a general task-event store, not an Achievement Award Ledger. An ordinary read→set can lose simultaneous award writes.

Netlify Blobs documentation (verified September 26, 2026):
https://docs.netlify.com/build/data-and-storage/netlify-blobs/
supports `getWithMetadata(key,{consistency:'strong',type:'text'})` and atomic conditional `set(key,value,{onlyIfNew:true})` or `set(key,value,{onlyIfMatch:etag})`. A failed condition returns `modified:false`. It also warns that *unconditional* writes to one key use last-write-wins. Production usage, plan quota, region and secret provisioning remain unapproved.

## Implemented pure server-side contract
`BADGE/badge-award-ledger-cas-store.js` adds `createCasAwardLedger({store,family_id,signingKey,verifyDecision,isBadgeActive,now,maxRetries})`. The injected store has exactly the above *atomic*, strongly-consistent operations; Node tests simulate these semantics without contacting Netlify.

- Verifies an actual owner-supplied Achievement Decision and per-child approved active badge authorization **before each write attempt**; no trust in browser `approved:true`.
- Opaque stable per-family/child/badge object key independent of the signing key. A mistaken signing-key rotation must fail verification of existing records rather than opening an invisible second ledger.
- Reads and fully verifies scoped HMAC-SHA256 chain, sequence, deterministic award IDs, duplicate decisions, timestamps, and checkpoint. Retains first award = unlock/0 stars, only successive distinct authorized REAWARD receipt increments stars via the unchanged projection.
- New write uses `onlyIfNew` for a missing object, otherwise `onlyIfMatch` with its exact current ETag. If concurrent overwrite was rejected, it reloads **and revalidates the entire ledger** before a bounded retry; never silently overwrites a rival receipt.
- Returns the same `TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1` read contract already consumed by `deriveFromLedger`, `getBadgeHistory`, and `getMonth`. Existing filesystem provider remains untouched and active for its own tests. No automatic migration or combining histories.
- A successful CAS receipt includes exact award_id, sequence, actual signed awarded_at, checkpoint and returned ETag. A retry collision with the same decision is explicitly `DUPLICATE_APPROVED_DECISION`; a stale write after retry exhaustion reports `CAS_CONFLICT_RETRY_REQUIRED`, not fake success.

## Boundaries / must not overclaim
**This is a tested *provider core*, not a deployed authoritative backend.** It has no Netlify SDK import, no live site credentials, no configured production store, no authenticated end-user write endpoint, no actual Achievement Decision verifier or approved image catalog. The source requires all of these to be supplied by a trusted runtime. Existing 60 badges remain working draft/inactive; the 20 history discoveries remain unawarded proposals.

A HMAC chain detects tampering and a wrong key, but a complete rollback to a previously valid signed historical blob needs a separately anchored checkpoint or tamper-evident audit/watermark; this is OPEN. The same applies to authorized deletion of a whole blob. No anti-rollback protection can be claimed solely from a signed local chain. A production rollout must define consistent site-wide namespace and region, secrets rotation/recovery, backup, authenticated child/family scope, production isolation from deploy previews, privacy and cost/usage gate. Do not deploy an experimental backend by merging Ready or invoking Netlify.

## Tests
`BADGE/badge-award-ledger-cas-store.test.js`: missing trust capabilities, approved/draft decisions, cross-child and cross-family gating, verified first award and real KST calendar projection, two separate concurrent REAWARD writers reading the same ETag, CAS conflict + retry preserving BOTH receipts, simultaneous duplicate decision producing ONE receipt, stale snapshot refusal, signed tampering refusal, wrong-key failure, transplanted foreign-family snapshot refusal, write outage, invalid and regressing trusted clock. The fake store rejects unconditional set.

Next exact OPEN: choose approved durable store/namespace/secret authority and anti-rollback anchoring; map owner-supplied actual Achievement Decision and approved badge provider; bind authenticated Reader to Ready/Snap without exposing this write API to client. The read UI PRs stay DRAFT and their main→Netlify release gate remains separate.
