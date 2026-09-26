# LATEST RESUME OVERRIDE — OPTIONAL EARNED BADGE TRACES IN DAY/WEEK PLANNER AND SNAP RECORDS — 2026-09-26

Direct user wants earned badges in Ready daily/weekly exploration plans to raise delight and motivation. **Retrospective celebration, NOT required quota, streak, task completion criterion, XP/gem conversion or task-to-badge correlation based only on same calendar date.** Date-level tiny text merit pin in Week and compact '이날 발견한 훈장' in Day, up to 3 names; quiet neutral empty state. Approved art required before visual image binding.

Actual tested DRAFT app PRs: Ready-Set [#111](https://github.com/hns140412-glitch/Ready-Set/pull/111), exact head `c038a37bb2728522ef8312e69ee4c84745ac4725`, ALL CI SUCCESS including Chromium E2E; Snap-Pop [#9](https://github.com/hns140412-glitch/Snap-Pop/pull/9), exact head `7652c3fb0ec99796768f3993b05cf7c0946dcd9e`, CI SUCCESS. Both UNMERGED and UNDEPLOYED due unverified main→Netlify auto-deploy coupling. Ready adds read-only child signed-month projection rails; Snap Records adds single-screen 탐험일지/배지 도감/캘린더 and signed-detail shell. No app has actual production authenticated Badge Reader yet; default is truthful unconnected, test fixtures only. Snap SW draft excludes all /api from offline caching. Parent has no personal unearned atlas. Existing historical 60 remain unapproved/unbound.

TAKY PR #153 merged main `76b9dbc77f147c44f44818b62bb66af891a9be65`; signed Award Ledger → verified child history/calendar, and separately labeled signed Family Gift read lane are executable, CI success. Previous branch-status strings in older docs do not override this exact merged main. Ready PR #110 (extended family roles) remains independently DRAFT; #111 starts from current Ready main without #110, so explicitly rebase/retest in whichever merge order is eventually authorized. No Netlify tool calls. Next OPEN: real server-approved asset/catalog + server session-bound no-store getMonth/getBadgeHistory/getCollection/getViewer, relation/permission source, then branch conflict/regression and actual release gate.

---

# CALENDAR DELTA — SEPARATE SIGNED FAMILY GIFT LANE — 2026-09-26

The same bounded history PR also adds `BADGE/badge-family-gift-calendar.js`. It reads a trusted signed V2 gift journal, filters recipient Child, groups Korean-time gifts by date, and composes **separate** achievement / family praise badge / journaled gem gift lanes. It does not issue awards, increment reaward stars, or claim a live wallet credit. The real family gift-history reader's authorization remains OPEN. See updated BADGE acquisition history/calendar spec and CI.

---

# LATEST RESUME OVERRIDE — BADGE ACQUISITION HISTORY / CALENDAR — 2026-09-26

Direct user instruction: Keep each badge's *entire acquisition history* and show it in child-specific detail timelines and a monthly calendar. The one source of truth is the signed Award Ledger, not app telemetry, story prompts or family gift records. New append has distinct UTC signed `awarded_at` and `approved_at`; legacy signed records without actual award timestamp remain in "날짜 미확인", not assigned to a guessed day. New `BADGE/badge-award-calendar.js` builds Asia/Seoul month cells; existing family reader gets `getBadgeHistory` and `getMonth` with auth and approved active catalog gates; one tier promotion is ONE underlying REAWARD event.

See `BADGE/BADGE_ACQUISITION_HISTORY_CALENDAR_2026-09-26.md` and latest CURRENT; verify exact-head CI before declaring main closure. Child self / existing verified Parent scope only; other relatives do not inherit private history access from family membership or praise-gift permission. Gift journal is distinct and can be an explicitly labeled separate future calendar lane, never an Achievement grant.

No real app surfaces, real approved 60/20 catalogue/asset, Gem Wallet, Netlify deployment or pending Ready PR #110 merge in this slice.

---

# LATEST RESUME OVERRIDE — ORIGINAL WITTY BADGE NAMING INSPIRED BY WoW — 2026-09-26

Direct user wants witty, clever WoW-achievement-style names in TAKY. Use writing craft, not direct borrowed WoW names. New `BADGE/badge-wow-inspired-copyworking.json` keeps 60 historical canonical names/IDs and 20 history-template IDs, and proposes 80 original display-name alternatives, earned-only reveal toasts and warm flavor texts. Humorous devices include situational twist, talking objects, Korean pun, self-aware and mystery reveal. `BADGE/badge-wow-inspired-copy-validator.js` guards source identity/uniqueness/status.

This is *editorial candidate content*, not source-name override or production asset approval, not actual 60+20 catalog activation or any Award Ledger issuance. Discovery candidates never show earned-only toast. Read `BADGE/BADGE_WITTY_NAMING_WOW_REFERENCE_2026-09-26.md` and current state before follow-up. WoW reference examples cited therein, no copyright title copied. Preserve separate same-badge verified reaward stars/tiers, parent no locked atlas, family permission and per-gift gem 1..5. No Netlify deployment.

---

# LATEST RESUME OVERRIDE — 60 PRESET + ~20 HISTORY BADGE STORIES — 2026-09-26

User wants 60 pre-set exploration badges (preserve original 60 historical IDs and witty names) with varied merit-scene hierarchy and about 20 extra child-personal discoveries according to actual learning history. Working rank axis POCKET(20)/FIELD(20)/EXPEDITION(14)/SECRET(6), tone independently WITTY/WARM/BRAVE/CURIOUS. This is narrative / visual distinctiveness, NOT the existing approved reaward star-tier axis.

Read `BADGE/badge-60-story-20-history-working.json`, `BADGE/BADGE_60_PLUS_HISTORY_20_STORY_SYSTEM_2026-09-26.md`, validator/proposal tests and CURRENT. All 60 source labels/IDs preserved; they are pre-set story slots NOT automatically runtime active or image approved. The 20 learning-history templates only produce child-scoped `REVIEW_REQUIRED_NOT_AWARD` candidates from distinct evidence verified by injected trusted capability; real Learning Engine evidence adapter and Decision/Award Ledger wiring still OPEN. No screenshot/telemetry-to-award shortcuts.

Scene entrance: small moment clue -> pastel imaginary exploration merit patch -> separate child-specific avatar -> owned/stars from signed ledger -> gradient-fade border. Parent remains without personal unearned atlas; family praise gift separate and gem 1..5 per gift. No 60 activation, no A/B asset approval, no Netlify deployment. Verify exact-head CI prior to main promotion.

---

# LATEST RESUME OVERRIDE — READY FAMILY RELATION / GIFT PERMISSION PR — 2026-09-26

TAKY family gift V2 in TAKY main remains authority. Ready-Set PR #110 at exact head `274ad4d6a14a202b69c9f808e74286140c2ed92a` (base Ready main `1d672d862cc8329a5f19ca91c9ed6a338752f5ae`) implements separately provisioned FAMILY_ADULT and verified relationships (grandparent, guardian, other adult family) without Parent Planner or Child learner authority. Sibling remains CHILD relation with distinct gift permission. Trusted Identity app metadata `family_permissions` gates `FAMILY_PRAISE_GIFT`, no relation grants automatically. Read-only GET /api/family/gift-permission does not authorize sending a gift. FAMILY_ADULT is denied old Ready Planner sync both client and server.

Ready PR #110 ALL exact-head checks PASS including Integration CI and Chromium Runtime E2E; it is still DRAFT / UNMERGED to avoid unverified Netlify auto-deploy linkage. Do NOT claim Ready main or real PWA integration is complete. No Netlify tool was called or manual deploy performed. Existing 60 historical badge drafts inactive; child real wallet/approved gift assets/actual transfer endpoint still OPEN. Latest gem gift rule 1..5 per individual transaction, parent has no personal unearned atlas. See CURRENT and Ready PR #110.

OPEN: identify safe deployment/merge gate; actual server-side family invitation and explicit grant management, trusted child target lookup and production gift write/wallet/collection adapter. Do not mutate auth roles via client self-service or treat a family relation as an authorization.

---

# LATEST RESUME OVERRIDE — FAMILY RELATION ≠ PARENT ROLE — 2026-09-26

Direct user correction: Family includes Parent, Grandparent, Guardian, Sibling and other relatives/members. The previous Parent-only Gift interpretation (PR #148) is superseded for new implementation, but V1 files/history are preserved. Family relationship never automatically grants praise gift permission; grant `FAMILY_PRAISE_GIFT` independently through a verified server-side family provider. A verified Child/Sibling can be a giver if separately permitted; self-gift, parent-recipient and cross-family gifting remain blocked.

V2: `BADGE/family-praise-gift.js` + `BADGE/family-praise-gift-journal.js` use `giver_member_id` and a distinct signing/idempotency domain; tests mock authorized Parent/Grandparent/Guardian/Sibling and an unapproved relative. This is NOT proof of live Ready relation support. Ready main Identity core still models binary PARENT/CHILD; real multi-relation family authority and gift-permission resolver remain OPEN.

GEM gift is 1..5 per single gift (not per day/week/month). Parent still has no personal unearned/locked Badge atlas. Gift Journal ≠ Achievement Award Ledger ≠ credited Gem Wallet. No historical 60 activation, no production asset selection, no deployment. Check PR exact-head/main CI before declaring implemented CLOSED.

Read `BADGE/FAMILY_PRAISE_GIFT_V2_CONTRACT_2026-09-26.md`, then current state, and continue ONLY remaining OPEN.

---

# LATEST RESUME OVERRIDE — PARENT PRAISE GIFTS / GEM CAP — 2026-09-26

Direct user correction: Parents can praise a Child with a badge or gems, but Parent has NO personal unearned/locked badge collection. Parent is a giver, not a collector. A GEM gift is integer **1..5 per individual transaction**; do not impose a daily/monthly/lifetime limit without user instruction.

PR #148 implements server-gated Parent Gift options + submission and a separate, signed durable Family Gift Journal with idempotency/tamper/family tests. This journal does NOT automatically credit actual child Gem Wallet or issue Achievement Award Ledger events. Only dedicated approved `FAMILY_PRAISE_BADGE` choices are giftable; historical 60 working drafts remain inactive. Re-gifting a praise badge is a separate event; whether its re-acquisition should affect stars is OPEN, never silently inferred.

Read `BADGE/PARENT_PRAISE_GIFT_CONTRACT_2026-09-26.md` and CURRENT for exact scoped implementation. Verify PR exact head and CI before claiming main closure. Real Ready endpoint, trusted production persistence, approved gift catalogue and child wallet/collection UI remain OPEN. No Netlify deployment.

---

# LATEST RESUME OVERRIDE — FAMILY BADGE ACCESS (PR #147, 2026-09-26)

- Ready main has server-verified Netlify Identity family/member role mapping and linked Child accounts. It is an AUTH foundation, NOT an Achievement Decision grant or Badge Award Ledger.
- New TAKY `BADGE/badge-family-read-access.js` gates reads through trusted server session + provider-verified same-family child and explicitly family-bound source; Parent can read own family's verified Child, Child self only. No fake client bootstrap.
- Badge Award Ledger HMAC/file key/award receipt now includes immutable family_id. Cross-family file transplant and rewritten family fields are rejected. Bridge checks signed snapshot and receipt family.
- Exact PR CI must be checked before claiming main CLOSED. No actual Ready API function or live multi-device store has been wired; no Netlify deploy.
- Next OPEN: real server identity lookup and Decision verifier, shared atomic persistent backend/key management, actual approved badge art, runtime surfaces and promotion/top-tier details.

---

# LATEST RESUME OVERRIDE — DURABLE LEDGER CORE SLICE (PR #146, 2026-09-26)

Implemented/tested in PR #146 (verify exact main before declaring main closure): `BADGE/badge-award-ledger-store.js` and `BADGE/badge-ledger-visual-binding.js` with real Node file persistence + signed scoped history and persisted replay tests. They are not production-wired: trusted Decision/auth/active-catalog adapters, server key and app consumer remain OPEN. Do not use browser-side secrets or claim a live award from test mocks.

First verified acquisition unlocks badge/0 stars; five approved unique reawards promote tier. Historical 60 remain `WORKING_DRAFT_NOT_ACTIVE`; visual A/B remain candidates. No deployment. See CURRENT and `BADGE/BADGE_LEDGER_SOURCE_AUDIT_2026-09-26.md`.

---

# LATEST RESUME OVERRIDE — AWARD LEDGER SOURCE AUDIT — 2026-09-26

- Verified current main repositories: there is NO grounded executable Badge Award Ledger read/verification provider at present. Historical Snap `badgeCandidateReviews` / `badgeEvents` / `badgeProgress` are NOT final Award Ledger.
- `BADGE/badge-ledger-projection-bridge.js` creates a fail-closed interface for a complete, child/badge-scoped, verified award history. It is NOT a live connection.
- Do not claim real Award Ledger integration or badge runtime display merely because this bridge CI passes. Find actual owner API/receipt schema first and then connect, without reopening CLOSED award decision behavior.
- First award unlocks with zero stars, approved distinct reawards add one, five reawards promote tier; raw observation counts do not count.
- See `BADGE/BADGE_LEDGER_SOURCE_AUDIT_2026-09-26.md` and latest `CURRENT/BADGE_VISUAL_BINDING_CURRENT_2026-09-26.json`.

---

# LATEST RESUME OVERRIDE — REAWARD VISUAL CORRECTION MAIN CLOSURE — 2026-09-26

Direct user correction of star semantics and exploration merit-insignia presentation merged to TAKY main: `568c4126f596c513738287fb947273c1f8bee2a9`. Post-merge Badge Visual Registry Validation: SUCCESS.

FIRST award unlocks a badge with zero stars. Distinct approved REAWARD ledger receipts increment stars; five trigger tier change. Actual ledger adapter is NOT wired yet. Post-promotion zero reset is provisional, not explicitly approved. Pure projection and layered renderer contract/CSS are on main but not imported into app runtime.

Drive image search (both connected accounts, badge/배지/뱃지/pastel/explorer terms and matching image inspection) found no verified exact final badge sheet. Candidate A/B remain reference only; do not auto-approve.

Current state: `REAWARD_VISUAL_CORRECTION_MAIN_CLOSED_FINAL_ASSET_AND_APP_WIRING_OPEN`.
CLOSED logic remains CLOSED. Historical 60 badges remain `WORKING_DRAFT_NOT_ACTIVE`.
NEXT: locate explicit final asset approval, ledger adapter integration, child-scoped overlay and app surface binding; resolve tier rollover/terminal policy.
No asset selection, catalog activation, app deployment or Netlify action was done.

---

# BADGE VISUAL BINDING — NEW CHAT START — 2026-09-26 LATEST

## LATEST DIRECT USER CORRECTION (highest priority)

- `stars != grade classification`
- First verified award unlocks the badge with 0 stars.
- A distinct reviewed/approved REAWARD of the SAME badge for the SAME child adds exactly 1 star.
- FIVE reaward stars promote to the next configured tier. Five stars triggering the tier change is confirmed; showing the completed five and restarting the next tier at zero are provisional until explicitly confirmed.
- Raw activity/repetition telemetry NEVER equals reaward. Projection requires prevalidated Award Ledger receipt, has duplicate and member-scope guards.
- Design: fictional exploration-crew campaign-merit insignia / unit-patch feeling, pastel, round, hand-drawn; not an actual military insignia.
- Base art and child-specific profile character are separate layers.
- LOCKED/unearned = silhouette; EARNED = active pastel.
- Border = soft, disappearing gradient fade.
- Exact last approved asset sheet is NOT verified. Candidate A/B remain candidate evidence only.

This section explicitly supersedes all former text saying stars mean `GRADE_CLASSIFICATION`.

## Authority and resume

INHERIT previous badge Evidence → Candidate Review → Achievement Decision → Award Ledger CLOSED.
Read `CURRENT/BADGE_VISUAL_BINDING_CURRENT_2026-09-26.json`.
Verify latest main plus any correction PR exact head/CI.
Continue only Visual Binding / reaward PROJECTION / app surface OPEN; do not recreate badge decision/award logic.

## 60 historical names

`BADGE/badge-visual-registry-working.json` has 60 draft IDs, all inactive, unbound, unapproved and not renderer bound.
`WORKING_DRAFT_NOT_ACTIVE` remains unchanged.

## Corrected files on correction branch

- `BADGE/badge-visual-registry-working.json`
- `BADGE/badge-visual-registry.js` + test
- `BADGE/badge-reaward-progress.js` + test
- `BADGE/badge-visual-renderer.js` + test
- `BADGE/badge-visual-presentation.css`
- `BADGE/BADGE_VISUAL_BINDING_CONTRACT_2026-09-26.md`
- `BADGE/BADGE_VISUAL_APPROVAL_PACKET_2026-09-26.md`

The reaward module is a pure projection from prevalidated ledger receipts and must not independently issue awards.
Presentation CSS is a contract, not proof of app runtime loading.

## Remaining OPEN

1. Locate / explicitly approve exact final pastel asset source; do NOT silently select either recovered 12-badge candidate sheet.
2. Bind approved base images `badge_id → visual_id → approved asset`.
3. Connect the correct award-ledger schema adapter for verified reaward receipts.
4. Integrate child profile overlay, locked silhouette, earned state and gradient-fade presentation on actual app surfaces.
5. Decide exact cross-app display surfaces, final tier sequence and terminal-tier behavior; preserve source authority.
6. Run exact-head, runtime and device validation. No deployment assumption.

Hard locks: USER != DEBUGGER; no historical catalog auto activation/award; no telemetry inference of ERROR_DISCOVERY/DEEP_THINKING/SPECIAL_BEHAVIOR; no EXP/gem/affinity/power equivalence.
