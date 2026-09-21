# SNAP & POP — APPROVAL / IMPLEMENTATION / AUTO-DEPLOY WORKFLOW

Status: ACTIVE PROJECT WORKFLOW CANDIDATE
Date: 2026-09-05
Authority: latest user direction + TAKY governance
Coverage companion: `PROJECTS/SNAP_POP_DECISION_COVERAGE_AUDIT_REV_00.md`

## 1. Latest User Decision — HARD PROCESS ORDER

Snap & Pop shall proceed in this order:

`SOURCE / DECISION COVERAGE AUDIT`
→ `DESIGN MOCKUP IMAGE`
→ `MOCKUP REVIEW / CORRECTION`
→ `UI IMPLEMENTATION FROM APPROVED MOCKUP`
→ `UI PREVIEW SCREENSHOT + LIVE URL`
→ `PREVIEW REVIEW / CORRECTION`
→ `HUMAN UI APPROVAL`
→ `UI FREEZE`
→ `FUNCTION IMPLEMENTATION REVIEW`
→ `FUNCTION TRACEABILITY / VALIDATION`
→ `FUNCTION PREVIEW SCREENSHOT + LIVE URL`
→ `HUMAN FUNCTION APPROVAL`
→ `PWA BUILD`
→ `LOCAL BROWSER / AUTOMATED / DATA / OFFLINE / CACHE TEST`
→ `RELEASE CANDIDATE`
→ `GITHUB COMMIT / PUSH`
→ `NETLIFY AUTO-DEPLOY`
→ `DEPLOYED URL SMOKE / INSTALL / OFFLINE / UPDATE TEST`
→ `RELEASE PASS`

No later stage may be used to bypass an earlier approval gate.

## 2. Source / Decision Coverage Gate

Before new design work:
- recover relevant full conversation state when accessible
- inspect original attachments/source documents at content level
- treat HANDOFF as recovery aid, not proof of coverage
- extract material decisions and later corrections
- classify every material item as PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED
- record destination or explicit HOLD/REJECT reason
- reverse-check that recovered items are actually represented in the current result/workflow

`SOURCE REVIEWED != DECISION COVERED`
`HANDOFF COVERAGE != FULL CONVERSATION COVERAGE`
`NOT ADOPTED != FORGOTTEN`

A material source item with no disposition is MISSING and blocks a full-coverage PASS.

Detailed current recovery state is tracked in `PROJECTS/SNAP_POP_DECISION_COVERAGE_AUDIT_REV_00.md`.

## 3. Design Mockup Stage

`DESIGN_MOCKUP` is a static image used to decide visual direction.

When the user says `시안 만들어줘` or equivalent:
- check current MASTER + coverage audit
- produce one design mockup image at a time unless another scope is explicitly requested
- self-validate the actual image before presenting it
- do not call a mockup an executable UI preview

When the user says `시안 수정해줘` or equivalent:
- revise the current design direction rather than inventing an unrelated replacement
- self-validate the revised result
- provide the revised image

Historical V12/V13 visual boards remain REFERENCE ONLY unless an element is explicitly re-approved.

## 4. Illustration Asset / DOM Separation — HARD LOCK

The approved mockup is a design reference, not a production asset sheet.

Production/UI implementation rules:
- DO NOT crop/slice the approved mockup and use those slices as final PWA assets
- create separate fit-for-purpose high-density illustration assets for background/environment/landmarks/Character/Guide/Gem/Growth Tree/decorative elements that are actually required
- keep runtime text, buttons, navigation, progress, counts, inputs, status, errors and dynamic data as live HTML/CSS/DOM components
- generated Korean text/numbers/buttons/data baked into runtime artwork = DESIGN FAIL
- illustration handles world/character/environment; live web UI handles language, controls and dynamic state

`MOCKUP != PRODUCTION ASSET`
`IMAGE LAYER != LIVE UI COMPONENT`

## 5. UI Implementation / Preview Stage

The UI may be redesigned, but material product/function decisions must not be dropped because the visuals change.

When the user says `UI 구현해줘`, `UI 만들어줘`, or equivalent:
- implement from the approved mockup using separate high-density assets + live DOM
- verify mobile layout and interaction feasibility
- deploy an executable preview
- provide BOTH:
  1. current rendered screenshot image
  2. mobile-openable live UI Preview URL

When the user says `UI 수정해줘` or equivalent:
- modify the implementation
- run visual/layout/copy regression
- provide the updated screenshot image + updated Preview URL

A static image, code file, ZIP or HTML file that is not reachable as a usable mobile preview is not `UI_PREVIEW_DELIVERED`.

Preview review checks include:
- product hierarchy
- ORIGINAL vs FAMILY boundary
- five freely usable writing tools
- three-step exploration
- voice / right-side walkie-talkie behavior
- bottom navigation structure
- Safe Area and touch targets
- Character / Guide hierarchy
- one persistent Growth Tree concept
- gem/wish/blessing flow presentation
- records/calendar access
- typography/readability
- accessibility
- no fake status-bar/device chrome
- no generated baked runtime text
- implementation feasibility

Only the user-approved preview becomes the new `UI_FREEZE_REFERENCE`.

## 6. UI Approval Gate

`PREVIEW VALIDATED != UI APPROVED`

UI approval requires explicit user approval after preview review.

After approval:
- freeze screen hierarchy
- freeze component hierarchy
- freeze design tokens
- freeze responsive behavior
- freeze illustration/icon asset requirements
- freeze loading/error/offline states
- record approval evidence and scope

Function implementation may not silently alter the approved UI.

## 7. Function Implementation Review

Function implementation begins only after UI approval.

Required traceability:
`MASTER REQUIREMENT -> APPROVED UI -> INTERACTION -> DATA STATE -> IMPLEMENTATION -> TEST CASE`

At minimum validate:
- exploration state machine and resume
- 3-step save/completion
- records/calendar
- gem shards / completed gems / balance
- duplicate reward prevention
- wish selection / blessing confirmation
- duplicate debit prevention
- EXP / growth logic
- one persistent Growth Tree state
- Character / Guide settings behavior
- TTS / speech recognition + fallback
- camera/profile flows and filter correctness
- Google Calendar optional integration isolation
- IndexedDB persistence / migration safety
- ORIGINAL/FAMILY feature flags
- FAMILY per-child data isolation and migration when enabled
- error taxonomy

Function QA must not be delegated to the user.

When the user says `기능 구현해줘` or `기능 수정해줘`:
- implement only against the approved UI and current MASTER
- run function + UI regression before delivery
- deploy an executable Function Preview
- provide BOTH:
  1. current rendered screenshot image
  2. actual mobile-openable Function Preview URL

## 8. Function Approval Gate / Automatic Production Trigger

`FUNCTION VALIDATED != FUNCTION APPROVED`

Explicit user phrase `기능 승인` or an unambiguous equivalent does two things:
1. freezes the approved function scope for the release candidate
2. authorizes the routine PWA validation + GitHub + Netlify production pipeline without repeated approval prompts for mechanical steps

`기능 승인` does NOT waive validation.

After `기능 승인`:
`PWA BUILD`
→ `SYNTAX / BUILD`
→ `LOCAL BROWSER TEST`
→ `AUTOMATED TEST`
→ `FUNCTION REGRESSION`
→ `UI LAYOUT / OVERLAP / TRUNCATION`
→ `TYPO / COPY CHECK`
→ `TOUCH / INTERACTION`
→ `INDEXEDDB / DATA`
→ `OFFLINE / ONLINE RECOVERY`
→ `SERVICE WORKER / CACHE`
→ `MANIFEST / INSTALLABILITY`
→ `MIGRATION / USER-DATA PRESERVATION`
→ `SEVERITY GATE`
→ `GITHUB PRODUCTION UPDATE`
→ `NETLIFY GIT AUTO-DEPLOY`
→ `EXISTING PRODUCTION URL VERIFICATION`
→ `INSTALLED PWA UPDATE / CACHE / DATA VERIFICATION`
→ `RELEASE PASS`

If BLOCKER / CRITICAL / MAJOR defects remain, production publication stops.
TAKY may self-correct and rerun validation when the correction does not alter protected product decisions. If a product decision must change, the target is ambiguous, a destructive action is required, credentials are missing, or a major defect cannot be safely self-corrected, stop as HOLD and request human decision.

## 9. PWA Build Gate

PWA is built only after both:
- `UI_APPROVED = true`
- `FUNCTION_APPROVED = true`

Required local verification:
1. first online load
2. asset load
3. IndexedDB create/update
4. refresh persistence
5. offline transition
6. cold restart offline
7. record recovery
8. online return
9. service-worker scope
10. manifest/installability
11. cache/version migration
12. responsive target viewports
13. accessibility checks
14. UI placement / overlap / clipping
15. Korean/English typo and copy check
16. protected ORIGINAL/FAMILY behavior regression
17. existing user-data preservation

BLOCKER / CRITICAL / MAJOR defects must be zero before deployment.

## 10. GitHub Automatic Publication

After PWA local validation passes and release candidate is frozen:
- create/update the project branch/repository files automatically through the connected GitHub integration
- use GitHub as the deployment Source of Truth
- preserve protected deployment/configuration files
- update only intended managed files
- run post-write verification
- preserve commit SHA as release evidence
- do not call GitHub commit success a deployment success

If the production repository is not yet unambiguously identified, repository resolution remains HOLD and deployment must not guess.

## 11. Netlify Automatic Deployment

Target behavior after release-candidate validation:

`GitHub approved production commit -> Netlify build/deploy automatically -> deployed URL verification`

Preferred setup:
- Netlify connected to the existing production GitHub repository/branch
- every approved production commit triggers Netlify build/deploy automatically
- preview/candidate branches do not replace production unless intentionally configured
- do not mix routine manual ZIP deploy with Git-based production deploy

Netlify is user-confirmed connected for this workflow. At deployment stage, use connected Netlify capability when exposed in the active toolset.
If the deployment target/site is ambiguous, remain `HOLD_TARGET_RESOLUTION` rather than guessing.

## 12. Production URL / Installed PWA Preservation — HARD LOCK

The user already uses the existing production URL through Safari and has added it to the iPhone Home Screen.

Therefore routine updates SHALL preserve:
- existing production URL
- existing GitHub -> Netlify production relationship
- installed Home Screen PWA continuity
- user records/data through application updates

A release must verify stale-cache/update behavior so that the Home Screen PWA does not remain on an old UI/logic build after successful Netlify deployment.

## 13. Deployment Verification

After Netlify reports success, independently verify the real existing production URL:
- HTTP/HTTPS load
- expected build/version marker
- correct approved UI
- main interactions
- responsive mobile render
- PWA manifest
- service worker
- installability where testable
- offline reload
- IndexedDB persistence
- stale cache/update behavior
- existing data preserved

`NETLIFY DEPLOY SUCCESS != RELEASE PASS`

Release Pass requires deployed-result verification.

## 14. Automatic Operation Boundary

Once the user approves UI and then function specification, the remaining routine build/publish workflow should proceed without requiring repeated manual approval for each mechanical step, unless:
- a protected product decision changes
- deployment target/repository/site is ambiguous
- destructive/irreversible action is required
- credentials/connections are missing
- a regression or major defect is found

The system must stop and report HOLD rather than guess in those cases.

## 15. Latest UI Redesign Override

The previous `Golden Reference inheritance` behavior is superseded for visual design only.

PRESERVE:
- product logic
- confirmed terminology
- data/state rules
- ORIGINAL/FAMILY boundary
- accessibility/voice principles
- PWA/data safety
- release governance
- premium/high-density illustration quality floor
- live DOM vs illustration separation

REDESIGN / RE-REVIEW:
- overall UI concept
- map visual composition
- Character visual design
- Guide visual design
- gem visual treatment, subject to functional meaning
- Growth Tree visual treatment
- typography visual system
- icon system
- color/material system
- screen layout and animation language

Historical UI remains REFERENCE ONLY unless the user explicitly re-approves an element.

## 16. State Definitions

- `SOURCE_AUDIT_IN_PROGRESS`
- `DESIGN_MOCKUP_DRAFT`
- `DESIGN_MOCKUP_REVIEWED`
- `UI_DRAFT`
- `UI_PREVIEW_VALIDATED`
- `UI_APPROVED`
- `FUNCTION_DRAFT`
- `FUNCTION_VALIDATED`
- `FUNCTION_APPROVED`
- `PWA_CANDIDATE`
- `LOCAL_PASS`
- `GITHUB_COMMITTED`
- `NETLIFY_DEPLOYED`
- `DEPLOY_PASS`
- `RELEASED`

These states are not interchangeable.

## 17. Current State

Current:
- source/decision coverage audit: RECOVERED MATERIAL MAPPED / FULL RAW HISTORICAL CHAT EXACT COVERAGE = UNVERIFIED
- design mockup: REDESIGN / RE-REVIEW NOT YET STARTED
- UI implementation: BLOCKED BY MOCKUP REVIEW/APPROVAL
- UI approval: NOT YET
- function implementation review: BLOCKED BY UI APPROVAL
- PWA build: BLOCKED BY UI + FUNCTION APPROVAL
- GitHub production publication: BLOCKED BY LOCAL PASS
- Netlify deployment: CONNECTED BY USER CONFIRMATION, BLOCKED BY RELEASE CANDIDATE

Next:
1. use coverage audit as anti-omission source map
2. produce one design mockup image when requested
3. self-validate actual image
4. after mockup direction is accepted, implement live UI with separate high-density assets + DOM
5. show screenshot image + live UI Preview URL for UI approval
