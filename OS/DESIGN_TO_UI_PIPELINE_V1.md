# TAKY DESIGN-TO-UI PIPELINE V1

Status: DRAFT / CENTRAL EXECUTION CONTRACT / NO MAIN MERGE / NO NETLIFY / NO IMAGE GENERATION

## 0. Purpose

This contract closes the gap between an approved UI mockup and production UI.

It does not redesign approved screens. It converts already-approved visual authority into:
1. frozen source evidence,
2. machine-readable screen contracts,
3. separately owned/bound asset layers,
4. real DOM/CSS/runtime implementation,
5. deterministic state fixtures,
6. matched-viewport browser renders,
7. visual + interaction + responsive + asset evidence,
8. correction loops,
9. a design receipt that can be consumed by a later release gate.

USER != DEBUGGER. A user-approved mockup is not implementation evidence, and successful code/tests are not visual approval.

## 1. Fixed execution chain

`APPROVED MOCKUP
-> SOURCE FREEZE
-> SCREEN CONTRACT
-> ASSET/LAYER CONTRACT
-> STATE FIXTURES
-> LIVE UI IMPLEMENTATION
-> MATCHED-VIEWPORT RENDER
-> VISUAL COMPARE
-> CORRECTION LOOP
-> INTERACTION/RESPONSIVE/ASSET REGRESSION
-> DESIGN RECEIPT
-> RELEASE AGGREGATOR`

Stages cannot be silently skipped.

## 2. Authority order

1. app CURRENT / explicit user-approved screen
2. approved Golden Reference + exact SHA
3. approved Visual ID / production asset authority
4. screen interaction/state contract
5. implementation
6. external references as technique evidence only

A runtime screenshot can never promote itself to Golden.

## 3. Stage contracts

### S0 APPROVED MOCKUP FREEZE
Required:
- screen_id
- authority_ref
- source identity
- exact source SHA-256
- approved viewport/aspect scope
- explicit approval scope
- explicit exclusions

Output: immutable Golden pointer. A composite mockup stays REFERENCE_ONLY unless an individual layer is separately approved as a production asset.

If approval identity + SHA are known but the binary has not yet been imported into the app repo, declare `golden.status=IMPORT_OPEN`. This is a valid contract blocker, not Design PASS. `BOUND` requires the local file to match the pinned SHA.

### S1 SCREEN CONTRACT
Machine-readable per screen:
- Golden identity
- viewport(s) and safe areas
- typography hierarchy
- composition regions
- z-order
- responsive behavior
- states
- interactions
- accessibility
- component/code owners
- required layers
- motion/effect contract where applicable

No Markdown-only implementation authority. Human-readable docs may accompany JSON but cannot replace it.

### S2 ASSET/LAYER CONTRACT
Minimum layer roles:
- BACKGROUND
- FOREGROUND
- OBJECT
- CHARACTER_SLOT
- FUNCTION_UI

Each bound art asset must carry owner, source/provenance, immutable SHA or approved external SHA pointer, anchor/fit behavior and whether it is production art or reference-only.

Layer resolution states:
- `BOUND`: local file asset with verified SHA.
- `LIVE_DOM`: FUNCTION_UI implemented as live DOM/component with stable selector + owner.
- `RUNTIME_SLOT`: CHARACTER_SLOT resolved dynamically through an approved resolver contract.
- `ASSET_PRODUCTION_OPEN`: art still missing; contract work may continue, Design PASS stays blocked.
- `NOT_APPLICABLE`: explicitly inapplicable role; omission is not allowed.

Forbidden:
- flattening the whole mockup and adding hotspots,
- regenerating an approved background/character without explicit revision authority,
- embedding sample schedule/task/result text in runtime art,
- using a reference crop as a production background unless separately approved.

### S3 STATE FIXTURES
Every screen defines deterministic visual states needed for review, not just HOME idle.

At minimum where applicable:
- INITIAL/LOADED
- EMPTY
- SELECTED/ACTIVE
- ERROR/RETRY
- COMPLETED
- OFFLINE

Learning apps add their own canonical states, e.g. correct/incorrect/hint/listening/confirming. Fixtures must not fabricate real learner FACT, achievement or score.

### S4 LIVE UI IMPLEMENTATION
Functional text and controls are live DOM/UI. Approved illustration owns the world; UI code owns interactive information.

Required:
- stable selectors/semantic IDs for test capture,
- no hidden Golden image overlay in production,
- no current-render-to-Golden copy path,
- real state/data binding,
- deterministic fixture injection isolated from production state.

### S5 MATCHED-VIEWPORT RENDER
Capture exact contract viewport(s). The capture manifest records:
- viewport width/height,
- DPR,
- browser/runtime version where available,
- fixture/state id,
- render SHA,
- source commit SHA.

No arbitrary resize to one universal comparison size.

### S6 VISUAL COMPARE V2
Compare reference and runtime at their declared matched viewport.

Evidence must include:
- full-frame distance,
- structure/edge distance,
- region-of-interest checks for critical UI areas,
- generated diff/heatmap path where supported,
- pass/fail per screen + state + viewport.

A single global score cannot hide a failed critical region.

### S7 CORRECTION LOOP
FAIL routes back to the owning layer:
- wrong source/asset -> S0/S2
- layout/typography/z-order -> S1/S4
- state mismatch -> S3/S4
- responsive clipping -> S1/S4
- interaction mismatch -> S4

Re-render and re-test. The reference is not weakened to make the candidate pass.

### S8 SUBGATES
Design completion requires machine-produced evidence files for:
- VISUAL
- INTERACTION
- RESPONSIVE
- ASSET_INTEGRITY

A CLI boolean such as `--interaction-pass` is not evidence.

### S9 DESIGN RECEIPT
Receipt issuer reads and hashes the actual evidence files. It may issue PASS only if every required evidence file itself reports PASS and matches the manifest identity.

Receipt contains:
- manifest SHA
- Golden SHA(s)
- render SHA(s)
- evidence file SHA(s)
- tested screen/state/viewport matrix
- source commit
- receipt SHA

### S10 RELEASE AGGREGATOR
Design receipt is only one release input.

Keep separate receipts for app-specific runtime concerns such as:
- Planner/Learning logic,
- OCR,
- IndexedDB/storage,
- offline/PWA,
- authentication,
- Safari/real-device,
- audio/BGM,
- accessibility/performance where required.

A failure in a non-design runtime gate must not be mislabeled as a visual-design failure, and a Design PASS must not imply Release PASS.

## 4. App adoption scope

### Ready & Set
Initial matrix:
- HOME
- WEEK
- DAY
- GOAL
- TIMER (existing approved Timer preserved, no redesign)

Priority while image generation is unavailable:
- import/hash-pin approved references already available,
- complete Screen Contract JSON,
- create deterministic Planner/Goal/Timer fixtures,
- produce matched viewport capture jobs,
- replace boolean design receipt inputs with evidence files.

### Hide & Seek
Expand beyond HOME:
- HOME
- TRACE
- LINK
- CORE
- RECALL
- major listening/confirm/correct/incorrect/completed/error states

Reuse approved Hide environment; no arbitrary new background generation.

### Snap & Pop
Expand beyond HOME using current approved screen lineage / 11-screen review scope where still authoritative.
Keep specialist GUIDE/Visual-ID production state independent from app Design Gate.

## 5. Image-generation HOLD behavior

Image generation is NOT required to implement this pipeline.

When a required production layer is missing:
- mark `ASSET_PRODUCTION_OPEN`,
- continue contracts, fixtures, DOM/runtime, comparison tooling and evidence wiring,
- fail closed only at the layer-dependent Design PASS boundary,
- do not fabricate placeholder art and call it approved.

This lets implementation advance now and makes later image work a bounded asset-fill step.

## 6. Required machine files for a consuming app

Recommended:
- `design-to-ui.json`
- `design/screens/<screen-id>.json`
- `design/layers/<screen-id>.json`
- `design/fixtures/<screen-id>.json`
- `ui-audit/render-manifest.json`
- `ui-audit/visual-result.json`
- `ui-audit/interaction-result.json`
- `ui-audit/responsive-result.json`
- `ui-audit/asset-result.json`
- `ui-audit/design-receipt.json`

## 7. Hard failures

- approved source missing or SHA mismatch
- runtime render promoted to Golden
- composite mockup used as interactive production UI
- production asset has no owner/provenance/hash
- required screen/state/viewport missing from capture
- critical-region compare failure
- evidence PASS supplied only as command-line flags/manual booleans
- visual correction loop skipped after mismatch
- app-specific function gate conflated with Design PASS
- user asked to debug implementation discrepancy

## 8. Current rollout policy

This V1 is a central Draft contract first.
No automatic app PR mutation, main merge, Netlify deployment or image generation is authorized by this document.
Apps adopt it through their own Draft branches and keep existing app-specific approvals authoritative.
