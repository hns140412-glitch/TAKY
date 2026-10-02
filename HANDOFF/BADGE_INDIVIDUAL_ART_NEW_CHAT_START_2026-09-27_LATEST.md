# BADGE UI / INDIVIDUAL ART — NEW CHAT START — 2026-09-27 LATEST

STATUS: HANDOFF ONLY / NO CATALOG ACTIVATION / NO DEPLOYMENT. This document records user intent and actual verified state; it does not approve artwork.

## HARD LOCK / user correction
User repeatedly requested IMPLEMENT the approved storyboard and make EACH of 60 individual badge illustrations. Do not generate another 60-up contact sheet, presentation board, architecture diagram, alternate mockup, or text-only status in place of deliverables. The last two generated images were erroneous sheets and are NOT APPROVED ASSETS. Do not crop any contact sheet to pretend they are individual originals. User must not be asked to re-upload already-provided approved mockups merely because the chat changed; recover available references first, and state explicitly if inaccessible. No invented crew characters or labels. In-world framing is 동행탐험 이야기; GUIDE is not an approved character/name.

Most immediate next deliverable: **001 이불 왕국 탈출기**, ONE standalone high-resolution illustration only, no rim/frame, stars, tier, lock, shadow, label, badge number, UI board, typography, or extra badges. Artwork must reflect this badge's actual canonical story (waking and escaping the blanket/bed kingdom), not a generic tent/forest badge. Independent background/interior/optional foreground/crew only if necessary. Do not claim image_gen outputs separated transparent layers unless actual separate files are delivered. If a specific image target is to be edited, ensure a usable image is present in the conversation.

## Shared asset contract — user-approved direction
One individual art per badge, common reusable rim/frame, stars 1–5, tier star colors Green/Blue/Red/Gold/Platinum rainbow, lock/gray state, shadow and effects. No per-badge duplicate frame/star/tier asset. Optional crew/child-scoped overlay separate from base. Locked grayscale silhouette. Ledger verification required for actual earned state; never fabricate awards.

## Approved visual reference description (six user-uploaded images in prior chat)
Five-phone flow: home illustrated island/waterfall/village/explorer child and penguin, wood sign 배지 도감 / 내가 모은 이야기 조각들, parchment 24/60 counter as mockup reference only (not actual account state), 3-col badges, bottom navigation; illustrated tree catalogue; earned detail; grayscale locked detail; celebration scene. Also 60-badge contact sheet as visual inspiration only, plus two layer/tier diagrams. Warm cream/ivory parchment, wood, moss/olive/gold/coral; avoid blue UI controls. Do not replace exact approved characters with generic mascot. Exact visual acceptance still OPEN.

## Source of truth and verified repo state
Repository hns140412-glitch/TAKY, draft PR #160 https://github.com/hns140412-glitch/TAKY/pull/160
Branch taky/badge-optional-child-overlay-20260927
Verified HEAD at handoff: 34de7908f87d8a4883db5e3554a964fc09d79d9b
Base SHA at handoff: 8e78af8b77d1f3e132f05c99cd6b69a7f258a23e
Two CI workflow runs at that HEAD completed SUCCESS: 36288244388 and 36288244440. Recheck latest main/PR HEAD on resume, do not assume SHAs remain current.
Files:
- BADGE/ui/badge-atlas.js, badge-atlas.css, preview.html, badge-atlas.test.cjs
- BADGE/badge-visual-renderer.js and tests, badge-visual-presentation.css
- BADGE/badge-ledger-visual-binding.js and tests
- BADGE/badge-visual-registry-working.json (60 UNBOUND/UNAPPROVED/INACTIVE; do not auto-approve)
- BADGE/badge-wow-inspired-copyworking.json (canonical working copy; check IDs/copy before artwork)
- .github/workflows/badge-ui-contract.yml
Latest change: atlas validAsset requires approved individual interior art; optional background, foreground, crew; disallows duplicate per-badge frame. Common rim/shadow/stars via CSS. UI preview exists but no approved 60 individual assets; storyboard pixel matching not verified. Ledger reaward count 0 projects to first visible star 1 without changing persisted ledger meaning. Existing renderer may have separate legacy layer contract; reconcile without breaking its approved BASE-only and optional child overlay semantics. No merge, no Netlify.

## Resume execution order
INHERIT APPROVED STATE -> CURRENT and latest HANDOFF -> exact main and PR HEAD -> CLOSED inherited -> OPEN only. Apply slogans in original meaning: Think Again, Keep Your Key / Think Again, You're The Key. USER != DEBUGGER. Next: deliver independent 001 art, verify no unwanted sheet/text/rim/star and visually compare against original approved style; then proceed badge by badge 002..060 with unique IDs and no automatic activation. Update UI binding only when each actual approved asset exists. Do not conflate generated proposal with approved runtime art. Run tests and visual comparison before claiming done. Do not stop for unnecessary approval questions, but do not bypass asset approval/merge/deploy gates.
