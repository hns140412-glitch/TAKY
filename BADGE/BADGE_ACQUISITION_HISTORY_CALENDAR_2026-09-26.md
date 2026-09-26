# CHILD BADGE ACQUISITION HISTORY & CALENDAR — 2026-09-26

## Direct user intent
Each badge remembers **every actual acquisition**, with a child-specific detail timeline and a monthly calendar. The record must not disappear when the badge advances in tier or its current within-tier stars reset. The calendar shows the child's journey, not a leaderboard or a new path for granting awards.

## Verified data path
Trusted Achievement Decision → family/child/badge-scoped signed Award Ledger → verified per-award replay → detail timeline + Asia/Seoul month grid. The original immutable receipt/ID and HMAC checkpoint remain the authority. UI state is only a derived projection; no calendar tap, app telemetry, error correction event, family praise gift or AI discovery proposal can directly issue an Award Ledger receipt.

The Node Award Ledger now records a trusted, UTC `awarded_at` at the **successful append**, separate from the pre-existing `approved_at` on the Achievement Decision. The timestamp is part of the row's signed data and included in the normalized verified receipt. An invalid trusted clock blocks the award before disk write. Existing legacy signed rows without `awarded_at` remain readable and appear in `undated_history` (actual award time was not recorded). Their decision approval date is retained as provenance but is **never silently used** as acquisition date.

`BADGE/badge-ledger-projection-bridge.js` now replays the exact same verified Award Ledger through existing `badge-reaward-progress.js`, emitting one event per distinct verified award. The sixth receipt may produce `TIER_PROMOTION`, which is still one REAWARD record, not a second grant. A first acquisition starts at 0 stars. An accepted reaward increments one star, and the existing provisional five-star tier-up policy is preserved; the date projection cannot alter it.

`BADGE/badge-award-calendar.js` groups ONLY signed `awarded_at` timestamps by **Asia/Seoul**, safely handling UTC midnight boundaries. Monthly day cells include a sorted event list and a summary (first acquisition, re-acquisition, promotion); undated legacy events are a separate collection-wide section, not assigned to a guessed day. The month is YYYY-MM. A missing or inconsistent family/child scope, duplicate receipt ID, malformed timestamp or unverified status fails closed.

`BADGE/badge-family-read-access.js` extends the already-tested authenticated server reader with `getBadgeHistory(request,{child_id,badge_id,tier_order})` and `getMonth(request,{child_id,month,tier_order})`. It checks the verified family session and authoritative current Child membership **before** looking up the approved active badge list, even if that list is empty. Child can read only own history, existing Parent access follows verified same-family scope; other family roles do not silently inherit history-read permission. `getMonth` accepts badge IDs only from injected trusted `listActiveBadgeIds` with active and approved entries, not from a client-controlled 60/20 draft list.

## Intended UI (not wired to a real app yet)
Child Badge Collection has one-screen switching:
- **도감**: earned vs approved-but-unearned silhouette; badge-card corner can show verified acquisition count and current stars/tier.
- **배지 상세 > 획득 기록**: chronological first acquisition → independent re-acquisitions → tier promotion, with dates, count, tier transition, and the existing witty flavor copy (only if independently approved). Never delete history when current display progress resets.
- **탐험 캘린더**: month grid; dots for verified earned entries, a compact date sheet when a day is tapped, and direct navigation to that badge's detail/history.
- **날짜 미확인**: legacy verified awards without actual append time shown separately with no fabricated calendar day.
- Approved visual art and actual asset binding are separately required for real art; calendar can truthfully show text/status with a neutral placeholder if art is still unapproved.

Family Praise Badge gifts and gem gifts live in a **separate event lane / gift journal**. The new read-only `BADGE/badge-family-gift-calendar.js` accepts only an injected trusted V2 signed gift journal, scopes to the recipient child, and builds separately labeled `FAMILY_PRAISE_BADGE_GIFT` and `FAMILY_GEM_GIFT` events. `composeChildCalendar` can put both lanes in the same month grid while preserving independent counts and provenance. A gift NEVER counts as an Achievement reaward, and the journaled gem total is not an assertion that the live Gem Wallet has been credited. The real service must independently authorize every gift-history read before invoking this projection; no live endpoint is added. Giver identity/message is subject to approved family-reader privacy and visibility policy. Parent has no personal unearned badge atlas.

## Calendar interaction proposal
- A small event indicator on a date: expedition badge for a verified achievement; a separate gift-ribbon for family praise; a gem-shaped mark for journaled gem gifts. Markers are visual categories, not reward amounts.
- Tapping a date opens a day sheet with chronological entries. Tapping an achievement entry opens that badge's full event history. Gift entries open their separate approved gift-history detail, never the achievement reaward ledger.
- Keep month-grid switching on one screen, no lengthy scrolling. Support reduced motion, labels instead of color-only meaning, and an explicit undated archive section for legacy awards.

## Regression gates
- New actual signed award timestamp differs from Decision approval timestamp.
- UTC Sep 26 15:00 => Korea Sep 27 calendar, and promotion displays once, without duplicate award.
- Legacy signed row with no awarded_at remains readable and undated; forged/malformed dates fail.
- Parent/Child family isolation, forged bootstrap and cross-family reads fail.
- Trusted empty active catalogue still checks authentication; unapproved or duplicated active catalogue entries fail.
- Same source history drives detail + calendar; historical 60 draft and new 20 discovery proposals never appear as awarded records just because they have narrative titles.

## Still OPEN / no production claim
The live app UI, verified multi-device Award Ledger backend, actual authenticated Achievement Decision source, final approved visual art, trusted production active badge catalogue, actual family gift history-read authorization endpoint and deployment remain OPEN. The existing tests use explicit fake authorities and temporary Node storage. This scope changes no deployed PWA or user's real award history, does not auto-activate the 60 preset content slots, and does not merge pending Ready PR #110.
