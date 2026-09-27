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

---

## LATEST OVERRIDE — 60 VECTOR CANDIDATE ART + TRUE VISUAL QA (2026-09-27)

After inheriting PR #160's state, work continued on a **separate draft PR #163** (`taky/badge-60-independent-scene-art-20260927`, base: PR #160 branch, NOT main). See `CURRENT/BADGE_INDIVIDUAL_ART_CURRENT_2026-09-27.json` and `BADGE/ui/ART_VISUAL_QA_2026-09-27.md`.

Produced 60 individual candidate scene pairs: `BADGE/ui/assets/individual/001..060/{background,interior}.svg` = 120 distinct SVG files; source-anchored manifest and isolated single-scene inspector; CI additionally rendered 60 **independent** 1024px PNG previews (no contact sheet). Structural 60-ID mapping and raster QA at 64/120/200/320 passed. CI runs at inspected art HEAD `abd78c5175d708d76d1df0160f10fae7d142f334`: UI 36289956771 SUCCESS, Visual Registry 36289956704 SUCCESS; 60-PNG artifact ID 10921779029.

**CRITICAL CORRECTION:** Actual preview images 001 and 026 were visually inspected and FAIL the approved high-density painterly illustration direction: too flat/simple. The other 58 are NOT certified by that sample. The 60 SVGs are rejectable structural **vector sketch candidates**, NOT finished or approved badge originals. Production-quality approved illustration count **0/60**; runtime binding and historical catalog activation **0**. Do not cite CI or image count to claim design fidelity or finished work. User does NOT want 60 per-artwork human approval loops; execution owner must self-QA as a batch against each unique storyline, motif, layer, art quality and approved six-screen image reference. Keep source references and prior CLOSED untouched.

Next exact OPEN: replace draft illustrations with independently authored high-density originals, preserve individual layer separation and common rim/star/tier/lock, compare actual browser UI against the user-supplied original. No new storyboard, no arbitrary Crew, no concept-sheet crops, no auto asset approval/activation, no main merge, Work OS or Netlify.


---

## LATEST RESUME OVERRIDE — INDEPENDENT ASSET MANAGEMENT AND OPTIONAL CHARACTER OVERLAP — 2026-09-27

Direct instruction: "에셋으로 만들어서 별도 관리해 캐릭터 오버랩될수 있게 하고" and then execution command ㄱ. This is **implementation authorization** for independent asset structure and character overlap, **not** authorization for Netlify, main merge, historical catalog activation, fictitious Crew or automatic award. Previous flat 60 vector previews still FAIL the original high-density visual storyboard and remain unapproved. The user does NOT want 60 individual approval loops; execution owner should batch self-QA without bypassing runtime evidence.

On DRAFT PR #163 (base: PR #160 branch, not main), newly added:
- `BADGE/assets/asset-registry-working.json`: independent central 60 ID/Visual ID/storyline/scene-path index, all runtime_approved=false, runtime_bound=false, active=false. Existing 120 scene SVGs remain under `BADGE/ui/assets/individual/001..060`; avoid duplication/rename and preserve original user files.
- Four **reusable** shared SVG assets in `BADGE/assets/shared/{rim,shadow,star-mask,lock}.svg`; never make stars or tiers for each badge. Tier colors/reaward count continue to come from verified Ledger projection / shared renderer. These four SVGs are implementation scaffolding, not a newly approved art direction.
- `BADGE/assets/overlays/slots-working.json`: profile and Snap Crew anchors for 60 individual Visual IDs; only provisional geometry. No actual child/Crew images or character IDs inserted.
- `BADGE/ui/badge-atlas.js` and CSS: preserve character-free base; optional same-child/same-family approved CHILD_PROFILE and Snap-owned approved individual Crew image overlays. Fail closed on supplied malformed/foreign/unapproved overlays and unreviewed layout. Locked state suppresses all character overlays. Shared asset frame/shadow/star-mask/lock reused once, independent scene background/interior/optional foreground layered under it. Preview defaults remain assets={} and awards={}, not pretend live.
- Additive `BADGE/badge-managed-asset-compositor.js` + test: central read-only composition contract instead of reopening CLOSED original renderer. Reject baked Crew or per-badge rim/shadow/effect for managed assets; the original renderer remains available. It does not approve assets or issue Award Ledger records.
- `BADGE/assets/test_badge_assets.py` plus UI CJS/ESM and managed compositor tests; existing UI CI runs all of them from one entry point. Original exact storyboard and parent #160 retain authority.

**Important status:** 60 draft vector candidates and 120 source layers do exist; final visually accepted originals 0/60; approved individual child/Crew visual content 0; production binding/activation 0. Slot position and layer implementation must not be described as real reviewed characters or completed UI visual parity. Work OS HOLD, no Netlify, main merge, auto-award or catalog promotion. Next open: generate actual high-density individual originals, self-verify per story, approve true layered assets and placement with recorded evidence, then connect reviewed asset registry / true server ledger reader to apps. Exact PR HEAD and CI must always be refreshed after this HANDOFF save.
