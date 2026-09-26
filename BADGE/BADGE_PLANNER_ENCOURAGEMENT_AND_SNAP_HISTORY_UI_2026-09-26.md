# OPTIONAL ACQUIRED BADGE ENCOURAGEMENT — WEEK / DAY EXPLORATION AND SNAP RECORDS — 2026-09-26

## Direct user decision
Show actually acquired badges as a light, witty, uplifting reminder in Ready's weekly and daily exploration plan. Treat a badge as a **souvenir of a verified experience**, not a performance target. The planning engine keeps ownership of task timing, completion, carry-over and outcome. Zero newly acquired badges is a neutral week/day, not a failed target or a prompt to manufacture achievements.

## Cross-app read-only contract
Source: server-validated, signed TAKY Award Ledger -> `TAKY_CHILD_BADGE_CALENDAR_V1` in Asia/Seoul, plus `TAKY_FAMILY_BADGE_DETAIL_HISTORY_V1` and a separately approved active Child collection. Reaward star/tier progression is unchanged. Promotion is ONE underlying receipt. Dates use signed actual `awarded_at`; historical valid awards lacking a timestamp remain in an undated archive, not on a guessed day.

Ready Week: on each date, small `훈장 N` marker only when verified records exist, and a maximum of 3 text merit pins for the week. Ready Day: `이날 발견한 훈장`, labels `첫 발견`, `다시 만난 훈장`, `훈장이 자란 날`. No direct sticker on a task row without a separately verified task-award association. Never affect task state or demand a weekly quota.

Snap Records: single-screen `탐험일지 / 배지 도감 / 캘린더` switching, then owned badge detail history. Approved but unearned catalogue entries may have truthful neutral placeholders; never render an unapproved candidate sheet as approved art. Public frontend cannot independently validate a ledger signature. The real `getViewer/getMonth/getCollection/getBadgeHistory` must be implemented by an authenticated server that derives child/family from its own current session. Browser test adapters are mock visual fixtures, not authority. Snap static PWA presently lacks those real endpoints and uses explicit unconnected state.

Family praise badge and gem gifts remain **separate signed gift-journal calendar lanes**, never count as achievement reawards or auto-credit the wallet. Parent has no personal unearned badge atlas. Gift permission differs from family relation; Gem gift limit remains 1–5 per transaction. Other relatives never inherit private Child history read from merely being a family member or gift-giver.

## Verified PR pointers (not deployed)
- Ready-Set PR #111 (https://github.com/hns140412-glitch/Ready-Set/pull/111), exact head `c038a37bb2728522ef8312e69ee4c84745ac4725`, all PR checks SUCCESS including Chromium Runtime E2E. DRAFT/UNMERGED; main at branch start `1d672d862cc8329a5f19ca91c9ed6a338752f5ae`.
- Snap-Pop PR #9 (https://github.com/hns140412-glitch/Snap-Pop/pull/9), exact head `7652c3fb0ec99796768f3993b05cf7c0946dcd9e`, Validate Snap & Pop SUCCESS including Playwright. DRAFT/UNMERGED; main at branch start `3de97be0d12dd6244a942b0c137c2efe578a43b6`. Private `/api/` GET requests bypass service-worker cache.
- TAKY PR #153 central history/calendar is in main `76b9dbc77f147c44f44818b62bb66af891a9be65`, post-merge Badge CI SUCCESS.

## OPEN
Real credentialed no-store session-bound read adapter in Ready and Snap, actual approved visual registry/assets, authenticated and atomic production Award Ledger history source, actual user-scope and privacy verification, and exact-head conflict tests with independently open Ready family relation PR #110. These draft PRs must NOT be promoted to main until main-to-Netlify auto-deploy linkage and release gate are verified. No Netlify deployment or award activation authorized by this document.
