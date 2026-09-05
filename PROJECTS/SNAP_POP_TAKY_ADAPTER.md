# SNAP & POP — TAKY PROJECT ADAPTER

Status: REV_00 / VALIDATED CANDIDATE / NOT RELEASED
Date: 2026-09-05
Authority: TAKY GRAND MASTER > SNAP & POP PROJECT MASTER
Legacy baseline: `Snap_Pop_UI_MASTER_LOGIC_REV_10.md`
Legacy baseline SHA-256: `fbdb89eb4fdd1060d17acee5ac68445baca1503de97a617c3ddccb96d49a7a5d`

Purpose: preserve the full legacy REV_10 product/design locks while applying TAKY evidence, state, cross-validation, approval, commit and release governance. This adapter does not declare REV_11 and does not itself make any UI/PWA release-ready.

## 1. Authority / State Lock

Snap & Pop follows:

`TAKY GRAND MASTER > SNAP & POP PROJECT MASTER > FUNCTION / UI / ASSET / PWA SPEC > TOOL / AGENT`

Hard state distinctions:
- `AI APPROVAL != HUMAN APPROVAL`
- `VALIDATED != APPROVED`
- `APPROVED != COMMITTED`
- `COMMITTED != RELEASED`
- `LOGIC PASS != DESIGN PASS != FUNCTION PASS != BUILD PASS != LOCAL PASS != DEPLOY PASS != RELEASE PASS`

Generated text such as `PASS`, `PWA READY` or `PRODUCTION RELEASE READY` is not validation evidence.

## 2. Protected State Manifest — REQUIRED

Before mockup, asset or PWA work, create and lock:

| ID | Protected State | Required Evidence | Missing Evidence State |
|---|---|---|---|
| PS-01 | GOLDEN_REFERENCE | approved image + approval evidence | UNVERIFIED |
| PS-02 | WORLD_MAP_GEOGRAPHY | approved map/spatial relation | HOLD |
| PS-03 | CHARACTER_MASTER | approved character source | HOLD |
| PS-04 | GUIDE_MASTER | approved guide source | HOLD |
| PS-05 | GEM_MASTER_APPROVED | approved gem source | HOLD |
| PS-06 | GROWTH_TREE_MASTER | approved persistent tree source | HOLD |
| PS-07 | TYPOGRAPHY_DNA | approved hierarchy | UNVERIFIED |
| PS-08 | MATERIAL_DNA | approved material language | UNVERIFIED |
| PS-09 | NAVIGATION_DNA | MASTER 5-tab nav | PRESERVE |
| PS-10 | COLOR_LIGHTING_DNA | approved palette/light | UNVERIFIED |
| PS-11 | LANDMARK_STATE_RULES | MASTER rules | PRESERVE |
| PS-12 | WALKIE_TALKIE_POSITION | MASTER rule | PRESERVE |

Every protected state shall track:
`SOURCE -> STATUS -> FILE/ID -> APPROVAL EVIDENCE -> ALLOWED DELTA -> TEST`.

Missing evidence remains `UNKNOWN / UNVERIFIED / HOLD`. It must not be replaced by assumption or a newly generated asset.

## 3. Evidence Ledger — REQUIRED

Each important decision records:
- Evidence ID
- requirement / claim
- source
- source authority
- source location / file / commit
- freshness
- confidence
- completeness
- reproducibility
- relevance
- validation result
- unresolved gap

Golden Reference, Approved Gem, Character Master, Guide Master and Growth Tree Master cannot become `APPROVED` without recoverable evidence.

## 4. Golden Reference Freeze Contract

A Golden Reference freeze records:
- GR_ID
- immutable source pointer/checksum
- user approval evidence
- approval scope
- viewport/crop/state
- protected features
- allowed delta
- forbidden delta
- superseded references
- validation date

Hard rules:
- `FILE EXISTS != USER APPROVAL`
- `PRESENTATION BOARD != RUNTIME ASSET`
- `GENERATED PASS LABEL != VALIDATION EVIDENCE`

Until approval evidence is recovered:
`GOLDEN_REFERENCE_STATE = UNVERIFIED`.
Deployment UI cannot be approved while this state is UNVERIFIED.

## 5. Design Token Contract

Implementation shall not reinterpret visual rules ad hoc.
Required token groups:
- `world.light.*`
- `world.palette.*`
- `world.atmosphere.*`
- `material.paper.*`
- `material.wood.*`
- `material.stone.*`
- `type.display.*`
- `type.body.*`
- `layout.safe.*`
- `layout.bottomNav.*`
- `layout.cta.*`
- `landmark.label.*`
- `character.scale.*`
- `guide.scale.*`
- `voice.walkie.*`

Flow:
`Approved Visual Language -> Protected Design Tokens -> CSS Variables/Components -> Browser Render -> Screenshot Validation`.

## 6. Visual Regression Gate

Visual validation has two independent layers.

### A. Deterministic regression
- fixed viewport
- fixed browser/project
- stable animation state
- baseline screenshot
- candidate screenshot
- expected/actual/diff retained

Recommended implementation: Playwright `expect(page).toHaveScreenshot()`.
Screenshot baselines must be generated and compared in a consistent environment. Diff thresholds are diagnostic and cannot independently approve design.

### B. Human design review
Review:
- map geography
- Character/Guide identity
- material language
- typography mood
- visual hierarchy
- narrative atmosphere
- `better, not different`

Protected regions override a global pixel score. A small change in a protected Character face, map geography or Approved Gem may still be FAIL.

## 7. Accessibility Gate

Minimum review target: WCAG 2.2 AA, plus child-friendly internal quality targets.

Required checks:
- Target Size (Minimum)
- focus visible
- focus not obscured by sticky/bottom UI
- text/non-text contrast
- text resize/reflow
- touch/keyboard/voice fallback
- TTS/speech failure fallback to text/touch

Snap & Pop internal quality target for major child-facing controls: preferably `44 x 44 CSS px` or larger. This is an internal usability target, not a claim that WCAG AA universally requires 44x44.

## 8. AI5 Execution Contract

### ORCHESTRATION
Separate Visual / UX / Asset / Function / Data / PWA / Validation.

### ROUTING
Use deterministic methods first when reliable. Image generation is restricted to approved visual refinement; coding follows approved UI contracts; browser tests verify actual rendered results.

### HANDOFF
Handoff is a lossless recovery map. Every relevant prior item is classified as:
`PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED`.

### CROSS-VALIDATION
At minimum:
- MASTER Validator
- Visual Regression Validator
- Functional/PWA Validator

Their evidence remains independent.

### HUMAN APPROVAL
Human approval is required for:
- Golden Reference replacement
- Design DNA change
- product scope/feature change
- Deployment UI Freeze
- production deployment / release

Internal QA must not be delegated to the user.

## 9. Lifecycle Adapter

Artifact states:
`DRAFT -> CANDIDATE -> VALIDATED -> APPROVED -> COMMITTED -> RELEASED -> SUPERSEDED`.

Forbidden:
- calling a CANDIDATE approved
- treating LOCAL PASS as DEPLOY PASS
- treating a mockup image as PWA PASS
- treating static code inspection as RELEASE PASS

Each transition requires Evidence IDs and approval scope.

## 10. PWA / Offline / Data Lifecycle Gate

Required scenarios:
1. first online load
2. required assets cached
3. exploration data create/update
4. IndexedDB persistence
5. offline transition
6. cold restart while offline
7. saved record recovery
8. online return
9. new-version/cache migration
10. stale-cache/update behavior
11. installability/manifest
12. service-worker scope
13. actual HTTPS deployed URL smoke

`SERVICE WORKER EXISTS != OFFLINE PASS`
`MANIFEST EXISTS != INSTALL PASS`

## 11. Handoff Upgrade

Handoff shall include:
- latest canonical reference
- goal/scope
- Protected State Manifest
- approved decisions
- active decisions
- user corrections
- implemented/last-valid state
- candidates
- HOLD / CONFLICT / MISSING / UNKNOWN / UNVERIFIED
- rejected/superseded states
- source/evidence pointers
- rollback reference
- validation state
- open defects
- exact next action

Coverage Gate:
`SOURCE ITEM -> CLASSIFICATION -> HANDOFF LOCATION/POINTER -> RECOVERY CHECK -> RESULT`.

Any materially relevant source item without representation or recoverable pointer = HANDOFF FAIL.

## 12. Existing PASS Reclassification

The legacy statement `REV_10 MASTER SELF-VALIDATION RESULT: PASS` is limited to:
`DOCUMENT-LOGIC SELF-VALIDATION PASS`.

It does not mean:
- DESIGN PASS
- GOLDEN REFERENCE PASS
- FUNCTION PASS
- BUILD PASS
- LOCAL PASS
- PWA PASS
- DEPLOY PASS
- RELEASE PASS

Prior generated boards claiming `PASS / PWA READY / PRODUCTION RELEASE READY` without actual evidence are invalid/superseded.

## 13. Recovery Classification

PRESERVE:
- REV_10 UI Concept Continuity Lock
- Golden Reference priority
- Character/Guide/Map/Gem/Tree lineage
- Live DOM / illustration separation
- No User-as-QA
- filename no-space/no-% rule

ADOPT:
- Protected State Manifest
- Evidence Ledger
- Design Token Contract
- deterministic Visual Regression + human review
- Accessibility Gate
- TAKY AI5 adapter
- TAKY lifecycle

ADJUST:
- Handoff -> lossless recovery package
- PASS semantics -> scoped PASS only

REJECT:
- generated-image PASS as evidence
- arbitrary Golden Reference selection
- generic implementation replacing approved visuals

HOLD:
- actual Approved Gem source evidence
- actual Character Master source evidence
- actual Guide Master source evidence
- actual Growth Tree source evidence

UNVERIFIED:
- exact latest user-approved Golden Reference approval evidence

CONFLICT:
- prior `PRODUCTION RELEASE READY` label vs absent deployed validation evidence -> prior label invalid/superseded

## 14. TAKY-Aligned End-to-End Workflow

`SOURCE RECOVERY`
-> `MASTER + TAKY LOAD`
-> `DECISION EXTRACTION`
-> `COVERAGE MATRIX`
-> `PROTECTED STATE MANIFEST`
-> `EVIDENCE LEDGER`
-> `GOLDEN REFERENCE FREEZE`
-> `DESIGN TOKEN BASELINE`
-> `IMPACT / CONFLICT / OMISSION CHECK`
-> `CANDIDATE`
-> `ACTUAL RESULT INSPECTION`
-> `DETERMINISTIC VISUAL REGRESSION`
-> `HUMAN DESIGN REVIEW`
-> `ACCESSIBILITY CHECK`
-> `SELF-VALIDATION`
-> `CROSS-VALIDATION`
-> `REGRESSION`
-> `DEPLOYMENT UI HUMAN APPROVAL`
-> `FUNCTION TRACEABILITY`
-> `PWA IMPLEMENTATION`
-> `LOCAL BROWSER / DATA / OFFLINE TEST`
-> `RC FREEZE`
-> `PRODUCTION DEPLOY APPROVAL`
-> `DEPLOY`
-> `DEPLOYED URL TEST`
-> `INSTALL / OFFLINE / CACHE / MIGRATION TEST`
-> `RELEASE APPROVAL`
-> `RELEASE`
-> `HISTORY`
-> `FEEDBACK`
-> `EVOLUTION`.

Skipping a gate is quality debt, not speed.

## 15. External Evidence References

These are implementation/validation evidence, not master authority:
- Playwright visual comparisons: https://playwright.dev/docs/test-snapshots
- WCAG 2.2 Target Size (Minimum): https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- web.dev Learn PWA: https://web.dev/learn/pwa/

## 16. Self-Validation

Validated against the legacy REV_10 constraints:
- ORIGINAL/FAMILY split preserved
- five freely usable landmarks preserved
- 3-step exploration preserved
- Character Master lock preserved
- Guide lock preserved
- Approved Gem lock strengthened
- one persistent Growth Tree identity preserved
- bottom navigation lock preserved
- right walkie-talkie preserved
- live DOM separation preserved
- typography mood lock preserved
- Golden Reference continuity strengthened
- No User-as-QA strengthened
- release gates strengthened
- prior PASS overclaim blocked
- AI5 / evidence / lifecycle governance added

Result: `VALIDATED CANDIDATE`.

`VALIDATED CANDIDATE != DEPLOYMENT UI APPROVED != RELEASED`.

## 17. Immediate Next Gate

Do not generate another PWA yet.

1. recover actual latest user-approved Golden Reference evidence;
2. change PS-01 from UNVERIFIED only after evidence is found;
3. recover Approved Gem / Character / Guide / Growth Tree source evidence;
4. prepare HOME Default browser/visual baseline;
5. generate/correct one `HOME_MAP_DEFAULT` candidate;
6. run visual regression + human design review;
7. proceed to `HOME_MAP_LANDMARK_SELECTED` only after PASS.
