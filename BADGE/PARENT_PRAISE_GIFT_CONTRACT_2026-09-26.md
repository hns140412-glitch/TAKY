> HISTORICAL V1 — SUPERSEDED for new family gifting by `BADGE/FAMILY_PRAISE_GIFT_V2_CONTRACT_2026-09-26.md`. The family is not Parent-only. Preserve V1 lineage; do not inherit its Parent-only assumption into new implementation.\n\n# FAMILY PARENT PRAISE GIFTS — 2026-09-26

## Direct user authority

- Parents praise children by gifting either a **family praise badge** or **gems**.
- A parent is a gift-giver, NOT a child badge collector. The parent surface must NEVER show a personal locked/unearned badge silhouette/atlas.
- **A parent may gift 1, 2, 3, 4, or 5 gems per gift transaction; maximum is FIVE.** Zero, negative, fractional, stringified numbers and values above five are invalid. The user did NOT specify a daily, weekly, monthly or lifetime quota. Do not invent one.
- Awarded gems and praise badges must be scoped to the chosen, provider-verified Child within the same family; not granted to a Parent or another family's child.
- These are user-authored praise gifts, not AI inference of academic mastery, effort, or achievement criteria.

## Current executable slice — scoped, NOT live app wiring

`BADGE/parent-praise-gift.js` implements a server-only, parent-authenticated gift request boundary. It requires injected trusted Ready-style session resolver, request-origin check, live Child membership lookup, giftable badge catalog and durable appendGiftRecord capability. It exposes `getGiftOptions()`, which returns only [1,2,3,4,5] and explicitly approved family-praise giftable badge options, **without parent-owned, LOCKED or unearned states**.

`sendGift()` requires an explicit parent request with idempotency key; for GEM, integer amount 1..5. For BADGE, resolves a dedicated `FAMILY_PRAISE_BADGE` with `APPROVED_ACTIVE` and `giftable=true`. Historical 60 `WORKING_DRAFT_NOT_ACTIVE` items remain ineligible. A GEM and BADGE cannot be combined into one ambiguous gift event. Browser body `family_id`/giver identity/award metadata is rejected; authority derives only from the trusted server session.

`BADGE/parent-praise-gift-journal.js` provides a separate Node-only durable, HMAC-chained family gift journal with per-family file and lock, atomic replacement, verified replay, same-key idempotency, conflict and tampering detection. It also independently enforces the 1..5 GEM amount and distinguishes `GEM_GIFT` from `PRAISE_BADGE_GIFT`. **Append success means a validated gift record was stored, not that the live child Gem wallet or Badge collection was credited.** Test fake Identity, catalog and signing key are test-only.

## Integration contract

`Parent authenticated intent → family/Child membership → dedicated gift catalog or gem amount validation → durable Gift Journal → read-only family gift projection → authorized child Gem Wallet / Family Praise Badge collection consumer`.

- Never use this gift ledger as an Achievement Award Ledger receipt, EXP, Learning Engine mastery, behavioral evidence, or a substitution for a review.
- An additional same-title parent praise gift creates a separate gift event. Whether repeat parent praise gifts should affect the child praise badge's reaward-star tier still requires an explicit domain rule; do not silently increment existing achievement stars.
- Parent Gift options are NOT a personal Parent collection. The Child collection retains LOCKED silhouettes only where active and approved base assets exist.
- Keep each child's gift inbox, gem wallet and collection scoped; no cross-child leakage.
- Real live awarding requires approved family praise badge definitions/art, authoritative account session endpoint, trusted multi-device atomic/transactional writer, a durable wallet consumer with idempotency and rollback handling, and an app surface. Standalone Node files are not a Netlify Functions shared persistence backend.
- External rollback anchoring and server-only secret management remain necessary for production. No deployment or historical badge activation is authorized in this slice.

## Minimum regression checklist

- Parent gets gift-only choices; Child / fake bootstrap cannot enter giver role.
- GEM 1 and 5 pass; 0, 6, negative, decimal, string and mixed fields fail before writing and in journal.
- Same idempotency key and content = one durable gift; changed content with same key = conflict.
- Cross-family child, parent-as-target, missing origin and forged authority fields fail.
- Restart/rehydration, signed journal integrity, different key and cross-family transplant fail-closed.
- Approved family praise badge can be journaled; historical draft cannot.
- Zero automatic balance updates, no fake Award Ledger receipts, no Netlify deployment.
