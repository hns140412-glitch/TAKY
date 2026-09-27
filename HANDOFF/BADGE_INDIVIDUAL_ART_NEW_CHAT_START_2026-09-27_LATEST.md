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

---

## LATEST VISUAL DETAIL — 001 WITTY DIRECTION + COMMON RIM / STAR / TIER (2026-09-27)

The user positively received the compact pastel hand-drawn illustration direction for 001, but specifically asked to ensure the border, stars and tier expression are correctly applied. Treat this as **direction acceptance conditional on shared decoration**, NOT as approved finished individual PNG, all 60 art approvals, any child/Crew identity acceptance or runtime activation.

Implementation on draft PR #163 only:
- Both `BADGE/ui/badge-atlas.css` and `BADGE/badge-visual-presentation.css` use the SAME shared pastel rim SVG `BADGE/assets/shared/rim.svg`, independent of tier; original scene never contains this rim.
- Single `BADGE/assets/shared/star-mask.svg` draws upper-arc stars; count 1–5 comes only from verified Ledger projection, `data-stars` drives proportional upper-arc positions in 64 / 120 / 200 / 320px layouts.
- Only star fill color varies with GREEN/BLUE/RED/GOLD/PLATINUM; never multiply rim files by tier or bake stars into 60 interiors. Locked state must not pretend an award, and optional character/Crew remain their separate approved overlays.
- Obsolete central CSS flex offsets were removed to avoid overriding the responsive arc. Both atlas and original read-only renderer have count/layout regression checks.
- SOURCE STYLE priority: witty symbolic image readable at icon sizes, pastel hand-drawn texture, core detail and original badge storyline before scenery or hyper-realistic painting. In particular, blanket/bedding hill, pillow fort, morning sun, tiny ladder/lantern for 001. Do not replace original identity or generate a 60-tile contact sheet.
- Prior 120 flat vector source assets still remain UNAPPROVED; their structural CI does not prove final visual quality. Recheck latest exact HEAD CI after this addendum. No merge, deployment or automatic award.

---

## LATEST RESUME OVERRIDE — SIXTY STORY-SPECIFIC DEV BINDINGS — 2026-09-27

User instructed: apply 001's witty pastel hand-drawn icon philosophy to **all 60 individual badges and bind**; user then said ㄱ. Verified current PR #163 was open draft based on PR #160 branch; original main and source IDs were preserved. This override records REAL implementation, not a promise or final art claim.

New deliverables:
- `BADGE/assets/individual-art-direction-60.json`: exactly **60 different source-ID-specific** visual briefs, story/metaphor, witty key detail and 64px silhouette, by canonical source title and proposed display title. NO 60-image contact sheet, no inferred child/Crew and no baked-in medal UI.
- `BADGE/ui/badge-dev-preview-bindings-60.json`: 60 explicit candidate background/interior file bindings plus shared four SVG ornaments. Each marked `preview_bound=true`, `production_bound=false`, `production_approved=false`, `active=false`.
- `BADGE/ui/badge-dev-binding-inspector.html`: standalone **one badge at a time** offline development inspector, embedded complete 60 bindings, original per-ID art refs, actual shared CSS/rim/star mask, selectable 64/120/200/320, one-to-five simulated star counts, five simulated star tier colors, locked state and optional placement guides with NO invented avatars. All sample stars are clearly marked visual QA fixtures; no Award Ledger or real award event is emitted.
- `BADGE/assets/asset-registry-working.json`: all 60 items now point explicitly to their source-specific direction and development-only binding, while `runtime_approved=false`, `runtime_bound=false`, `active=false` remain unchanged. Zero formal production bindings.
- CI additional checks in `BADGE/ui/test_dev_bindings_60.py` and `BADGE/assets/test_badge_assets.py` enforce 60 source IDs, distinct 60 scene ideas, valid physical layers, 60 single-scene preview mappings, zero auto-promotions. Existing UI test, renderer tests, structural 120-file QA and 60-file raster QA continue.

Exact code-validation head `a72890dbb664e36f2a3cf6be0d04029f053c85cb`, CI Badge UI contract checks run 36297842391 SUCCESS, Badge Visual Registry Validation run 36297842399 SUCCESS. Artifact ID 10924288028 holds preview HTML and CSS, 60-source idea registry, 60 draft bindings, central registry and overlay slots, four shared SVGs, **120 individual SVGs and 60 separate independent raster previews**. A container check confirmed 195 files in artifact and actual counts 60/120/60, zero production bindings or live activations. Only CURRENT/HANDOFF state updates follow code validation.

**HONEST LIMIT:** The physically bound SVGs are still the previous flat candidate vector illustrations that FAILED original high-density artwork style check. The 60 new creative directions are SPECIFICATIONS, not 60 new finished illustrations. 60 development mappings completed, **0/60 visually accepted final new art, 0 production binding and 0 activation**. Do not call the released 001 concept sheet a standalone final asset, crop it into production, or infer all 60 are finished from binding paths. The user does not want individual user-approval loops; execution owner must produce independent high-density badge symbols from these per-ID briefs and self-QA small-size parity, source motif and approved original six-screen reference. Shared rim/stars/tier, same-child profile and Snap-owned Crew overlays remain separate. No main merge, Netlify or Work OS.

---

## LATEST RESUME OVERRIDE — PHYSICAL 60-PNG VISUAL QA — 2026-09-27

User asked whether all 60 were actually created and to inspect noncompliant work against TAKY rules. Read `BADGE/assets/BADGE_60_PAINTERLY_VISUAL_QA_2026-09-27.md` first and its exact 31 ID list. Separate 60 1254×1254 transparent-corner PNGs were discovered and inspected at 64/120px: 29 conditional scene candidates, 31 rework/recreation. This was a real visual review, **not** an inferred success from CI. 044/053 fail circular silhouette; 033 missing magnifier, 034 wrong prop; 001–020 often repeat sunrise and 001/008/009/017/055 flag provenance requires correction. Previous board/contact sheet output is rejected and cannot fill individual slots.

The new PNGs are **not** committed to PR or production-bound; existing 60/60 code binding still references old visually rejected draft vector assets. New images are single flattened circular inner-scene previews, not independently authored background/interior/foreground. Existing common rim, count/tier stars, lock and optional child/Crew overlay boundaries remain unchanged. Actual final art approved=0/60, runtime PNG binding=0/60, activation=0 and award=0. No user per-item approval loop. Correct 31, reassess all at all four sizes, then create real bound reviewed evidence. Closed contracts remain inherited and main merge, Netlify, Work OS forbidden.
