# SNAP & POP — APPROVAL / IMPLEMENTATION / AUTO-DEPLOY WORKFLOW

Status: ACTIVE PROJECT WORKFLOW CANDIDATE
Date: 2026-09-05
Authority: latest user direction + TAKY governance

## 1. Latest User Decision — HARD PROCESS ORDER

Snap & Pop shall proceed in this order:

`SOURCE / DECISION COVERAGE AUDIT`
→ `UI CONCEPT REDESIGN`
→ `INTERACTIVE PREVIEW`
→ `PREVIEW REVIEW / CORRECTION`
→ `HUMAN UI APPROVAL`
→ `UI FREEZE`
→ `FUNCTION IMPLEMENTATION REVIEW`
→ `FUNCTION TRACEABILITY / VALIDATION`
→ `HUMAN FUNCTION APPROVAL`
→ `PWA BUILD`
→ `LOCAL BROWSER / DATA / OFFLINE / CACHE TEST`
→ `RELEASE CANDIDATE`
→ `GITHUB COMMIT / PUSH`
→ `NETLIFY AUTO-DEPLOY`
→ `DEPLOYED URL SMOKE / INSTALL / OFFLINE TEST`
→ `RELEASE PASS`

No later stage may be used to bypass an earlier approval gate.

## 2. UI / Preview Stage

The UI is being re-reviewed and may be rewritten. Historical UI boards are reference material, not mandatory Golden References.

Before UI design:
- complete source/decision coverage audit
- classify prior requirements as PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED
- verify no material product/function requirement is dropped merely because UI is redesigned

The preview must be an applied, realistic mobile preview rather than a text-only spec board.

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

## 3. UI Approval Gate

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

## 4. Function Implementation Review

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
- error taxonomy

Function QA must not be delegated to the user.

## 5. Function Approval Gate

`FUNCTION VALIDATED != FUNCTION APPROVED`

After technical validation, present concise functional verification evidence to the user.
Explicit user approval freezes the function specification for the PWA build.

## 6. PWA Build Gate

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

BLOCKER / CRITICAL / MAJOR defects must be zero before deployment.

## 7. GitHub Automatic Publication

After PWA local validation passes and release candidate is frozen:
- create/update the project branch/repository files automatically through the connected GitHub integration
- run post-write verification
- preserve commit SHA as release evidence
- do not call GitHub commit success a deployment success

If the production repository is not yet unambiguously identified, repository resolution remains HOLD and deployment must not guess.

## 8. Netlify Automatic Deployment

Target behavior after release-candidate validation:

`GitHub approved production commit -> Netlify build/deploy automatically -> deployed URL verification`

Preferred setup:
- Netlify connected to the production GitHub repository/branch
- every approved production commit triggers Netlify build/deploy automatically
- preview/candidate branches should not replace production unless intentionally configured

Netlify is now connected for this workflow. At the deployment stage, use the connected Netlify capability for site/deploy setup or verification when exposed in the active toolset.
If the deployment target/site is ambiguous, remain `HOLD_TARGET_RESOLUTION` rather than guessing.

## 9. Deployment Verification

After Netlify reports success, independently verify the real deployed URL:
- HTTP/HTTPS load
- expected build/version marker
- correct UI
- main interactions
- responsive mobile render
- PWA manifest
- service worker
- installability where testable
- offline reload
- IndexedDB persistence
- stale cache/update behavior

`NETLIFY DEPLOY SUCCESS != RELEASE PASS`

Release Pass requires deployed-result verification.

## 10. Automatic Operation Boundary

Once the user approves UI and then function specification, the remaining routine build/publish workflow should proceed without requiring repeated manual approval for each mechanical step, unless:
- a protected product decision changes
- deployment target/repository/site is ambiguous
- destructive/irreversible action is required
- credentials/connections are missing
- a regression or major defect is found

The system must stop and report HOLD rather than guess in those cases.

## 11. Latest UI Redesign Override

The previous `Golden Reference inheritance` behavior is superseded for visual design only.

PRESERVE:
- product logic
- confirmed terminology
- data/state rules
- ORIGINAL/FAMILY boundary
- accessibility/voice principles
- PWA/data safety
- release governance

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

## 12. State Definitions

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

## 13. Current State

Current:
- source/decision coverage audit: IN PROGRESS
- UI: REDESIGN / RE-REVIEW
- UI approval: NOT YET
- function implementation review: BLOCKED BY UI APPROVAL
- PWA build: BLOCKED BY UI + FUNCTION APPROVAL
- GitHub production publication: BLOCKED BY LOCAL PASS
- Netlify deployment: CONNECTED, BLOCKED BY RELEASE CANDIDATE

Next:
1. complete full conversation/source coverage audit
2. produce one applied mobile UI preview candidate
3. validate internally
4. show for user review/approval
