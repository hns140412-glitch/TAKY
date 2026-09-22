# LEARNING APP FAMILY UI DECISION REGISTRY — 2026-09-22

Status: ACTIVE CROSS-APP UI DECISION REGISTRY
Purpose: share UI review/lock state across Ready & Set / Snap & Pop / Hide & Seek without flattening different maturity levels.

## 0. Why this registry exists

Each app is being reviewed in a separate conversation/repository.
Therefore UI decisions can become fragmented unless TAKY records:

- what is already LOCKED;
- what is PROVISIONAL / LOCK_CANDIDATE;
- what remains OPEN;
- what is SUPERSEDED;
- which decisions are app-local;
- which decisions must propagate across the family.

A shared family criterion does not mean all apps have the same UI freeze state.

## 1. Status vocabulary

### LOCKED
Accepted product/UI decision.
Later work may refine implementation detail but may not silently change meaning/structure.

### LOCK_CANDIDATE
Reviewed and coherent enough to drive structured work, but still subject to explicit cross-validation before final freeze.

### PROVISIONAL
Useful current working direction; may change after source/UI reconciliation.

### OPEN
Not decided. Do not visually hard-code as if canonical.

### SUPERSEDED
Historical/previous direction that must not return through fallback or old mocks.

### RUNTIME_VERIFIED
Behavior/layout rule proven in browser/runtime evidence.
Does not automatically mean final visual is locked.

### DEVICE_OPEN
Physical-device visual/interaction verification remains unverified.

## 2. Family-wide UI locks

LOCKED:
- one shared island world;
- Ready = Base Camp / Island Map;
- Snap = Beach;
- Hide = Jungle / Waterfall;
- current companion continuity across regions;
- island/base-camp identity persistence;
- exploration crew identity rendered from runtime slots rather than hard-coded character;
- child-facing UI uses exploration language rather than developer/module language;
- 390×844 mobile baseline;
- one dominant primary action per task screen;
- non-happy states are first-class;
- Badge / Growth / Gem-Wish / Affinity are semantically distinct;
- Badge star count = Star Grade / 성급 1–5;
- shared badge system crosses apps;
- share may carry badge/history context;
- no Netlify / production / main merge during UI definition.

LOCK_CANDIDATE:
- family Screen Composition Standard;
- island world pre-mockup criteria;
- shared Badge Canonical/Visual/Share contracts.

OPEN:
- exact family-wide visual art style;
- exact pixel topology of island;
- final shared badge collection entry point;
- final cross-app visual transition choreography.

## 3. Ready & Set UI state

### LOCKED / authoritative structure
- Ready is Base Camp and session/planner orchestrator.
- shared island map role.
- TODAY / Mission / Focus / Wrap-up / Result / Planner Week / Planner Day / intake / parent-admin / history/profile/settings must have explicit UI destinations.
- UI productization order:
  PRODUCT PURPOSE → IA → SCREEN → COMPONENT → OWNER → STATE/EVENT → NAVIGATION → RESPONSIVE → VISUAL → HIGH-FI → IMPLEMENTATION.
- character/crew slots are runtime-driven.
- specialist app logic is not reimplemented inside Ready.
- Share Golden Contract:
  탐험 시작 공유 / 탐험 완료 공유;
  profile theme/avatar inherited;
  information before background;
  no share-time theme/avatar re-selection.
- phone baseline 390×844.

### RUNTIME_VERIFIED / current implementation evidence
- TODAY → Mission → Focus → Result runtime flow.
- mobile browser interaction/responsive evidence.
- Planner/browser flows.
- current share-card renderer exists.
- current frozen implementation candidate is not equivalent to final UI freeze.

### PROVISIONAL / in active UI review
- exact final Home/TODAY composition;
- exact Planner visual layout;
- exact island/base-camp visual framing;
- final Design System;
- final high-fi screens.

### CONFLICT / REVIEW_REQUIRED
- current generic Ready “획득 별” in share runtime conflicts semantically with shared Badge Star Grade.
- resolve under Ready product authority; do not relabel automatically.

### DEVICE_OPEN
- physical keyboard/safe-area/audio/camera and installed PWA visual behavior.

## 4. Hide & Seek UI state

### LOCKED / authoritative structure
- product identity = Hide & Seek.
- world = vocabulary treasure/seek exploration; no police/detective/arrest framing.
- island region = Jungle / Waterfall.
- crew is companion, not teacher/grader.
- Ready owns planner/date/family-session completion.
- Hide returns specialist completion to Ready.
- Calendar = history, not streak.
- Badge Book = growth/history, not power/score.
- no Snap Gem/Wish economy import.
- character art is character_id-driven.
- one dominant action where possible.
- 390×844 baseline.

### UI DESIGN HANDOFF SEQUENCE — LOCK_CANDIDATE
A. Bottom Nav
B. Home / Today exploration
C. Explore Hub
D. TRACE first/new + review
E. LINK three-state
F. PIECE
G. Completion + Ready report
H. CATCH / items / Badge Book / Calendar / item detail + Memory Ladder
I. Shared badge award overlay
J. Crew appearance slots

### RUNTIME_VERIFIED / current evidence
- child-facing core UI browser/mobile viewport.
- home/mission/learning/completion/Memory Ladder/OCR review-recovery.
- exploration crew presentation layer.
- mission management.
- record/wordbook surfaces.
- 390×844 browser layout.

### PROVISIONAL / active UI review
- exact final visual composition of the above screen sequence.
- exact Badge Book collection composition.
- exact shared badge award overlay treatment.
- final art direction and illustration master.

### SUPERSEDED
- police/detective/arrest/case child-facing world.
- generic reward/achievement assets cannot be promoted merely because they exist in legacy assets.

### DEVICE_OPEN
- physical camera/touch/keyboard/PWA install lifecycle.

## 5. Snap & Pop UI state

### LOCKED product rules
- thought-to-expression specialist + Ask→Understand axis.
- Beach region.
- five expression landmarks always accessible.
- child final authorship.
- Ask and Imagination are semantically distinct.
- crew interaction and slot rules.
- Wish Economy is Snap-owned.
- Badge != score/power.
- Special = special encounter method, not stronger character.
- Growth / Badge / Wish separation.
- shared island / companion continuity.
- badge visual lineage and Star Grade semantics.

### LOCK_CANDIDATE structure
- Product/UI Architecture draft.
- final mockup/UI criteria.
- Home purpose reduction.
- task surfaces calmer than world surfaces.
- non-happy state design system.
- runtime slot model.
- Screen Composition Standard inherited from TAKY.

### PROVISIONAL
- 4-item child nav proposal: 탐험 / 기록 / 성장 / 보물함.
- exact Home composition.
- exact Result composition.
- exact location of Ask/Imagination entries.
- exact visual synthesis previously described as “Modern Field Kit + Living World moments”.
These must not be treated as final locks until current criteria-first review closes.

### OPEN
- final high-fi visual language.
- final screen arrangement.
- exact component geometry.
- final map composition.
- final badge collection entry point.
- actual art asset set.

### IMPORTANT
Snap is currently **not UI-frozen**.
Do not propagate Snap provisional UI choices as family-wide visual authority.

## 6. Cross-app propagation rules

### Propagate automatically to all apps
Only decisions classified FAMILY_LOCKED, such as:
- island topology roles;
- shared crew slot semantics;
- badge semantics/star-grade;
- common share/privacy rules;
- cross-app continuity constraints;
- terminology corrections.

### Propagate as reference, not lock
App-local UI solutions:
- Ready planner layout;
- Hide TRACE/LINK/PIECE composition;
- Snap writing screen composition.

Other apps may learn from them but must not copy blindly.

### Never propagate
- app-specific economy;
- app-specific learning semantics;
- app-specific result scoring;
- legacy assets;
- provisional high-fi visual choices.

## 7. Required UI update packet

Whenever an app conversation locks or changes UI, it should produce a compact packet:

UI_DECISION_ID
APP_ID
SCREEN_ID / DOMAIN
STATUS
DECISION
WHY
SOURCE / EVIDENCE
AFFECTS
CROSS_APP_PROPAGATION = YES / REFERENCE_ONLY / NO
REGRESSION_RISK
SUPERSEDES
OPEN_GAPS

TAKY absorbs the packet into this registry or its successor.

## 8. Human approval boundary

A decision becomes FINAL_VISUAL_LOCK only when:
- product purpose and screen contract are closed;
- runtime owner/state/event mapping exists;
- cross-app conflicts are checked;
- user has accepted the visual direction where required;
- regression risks are recorded.

Static mockup alone never creates a final lock.

## 9. Current family snapshot

Ready:
- product/function structure: mature
- UI productization: active
- several structural/share rules locked
- final visual: NOT FROZEN

Hide:
- runtime/UI architecture: comparatively mature
- screen sequence and learning UI semantics strongly defined
- final visual: NOT FROZEN

Snap:
- product rules/architecture: defined
- UI structure: LOCK_CANDIDATE / PROVISIONAL
- final visual: OPEN
- no high-fi should be treated as authority yet

## 10. Regression rule

Before any new mockup or UI implementation:
1. read this registry;
2. read app-local latest UI handoff;
3. preserve LOCKED decisions;
4. flag conflicts instead of silently harmonizing;
5. update this registry when a new decision crosses app boundaries.

END


## 11. 2026-09-22 integrated UI decision delta — Hide / shared island / records

### FAMILY_LOCKED additions
- fixed-island topology remains one persistent island; app regions are not separate worlds.
- onboarding continuity:
  CHARACTER / EXPLORER BUILD
  → TRAVEL-PREPARATION / CREW BUILD
  → DROP OR VOYAGE
  → ENTER FIXED ISLAND
  → NAME ISLAND
  → ENTER READY BASE CAMP
  → NAME BASE CAMP
  → CONTINUE THROUGH SAME ISLAND.
- island name and base-camp name are editable later.
- renaming island/base-camp never resets learning history, Planner, badges, crew relationship, Explorer_ID, island geography, or app-region placement.
- Ready & Set = Base Camp / Island Map.
- Hide & Seek = Jungle / Waterfall.
- Snap & Pop = Beach.
- current Explorer and companion continuity crosses regions.
- app switching should visually read as movement within one island, not launching unrelated worlds.
- shared badge award may appear as a dedicated cross-app overlay/window in Ready / Hide / Snap at meaningful transitions.
- badge/calendar history must never become streak-pressure or punitive absence tracking.

### HIDE LOCKED additions
- Hide learner-facing IA is TRACE / LINK / PIECE / CATCH and is NOT a mandatory linear projection of Runtime V2 internal states.
- first TRACE = NEW-only.
- review TRACE is a distinct review-play variant and may mix prior / re-hidden / weakness-priority items.
- LINK = verified principle/relationship → related-choice discrimination → mixed tap-based connection test.
- PIECE = final missing critical-structure completion, generalized beyond English.
- CATCH = cumulative treasure/record space containing item history, Badge Book, Calendar, item detail, and contextual Memory Ladder.
- Memory Ladder is contextual, not a required bottom tab.
- primary Hide bottom navigation candidate: HOME / 홈, EXPLORE / 탐험, CATCH / 보물함.
- Hide Home is a Jungle/Waterfall regional base point, not the whole-island map.
- Home states:
  1) no confirmed set → acquire clues/homework source;
  2) clue review → OCR/review/correction/merge/exclude;
  3) set ready → show actual learning set and launch learning.
- when Ready Planner provides an explicit target/set, Hide shows that target.
- when no Ready target exists, Hide default child-facing set may show confirmed English vocabulary 12.
- confirmed English 12 should be visible as a wordbook-like translucent tile/slip board; preferred initial study is 3×4 on 390×844, subject to visual QA.
- homework/photo intake is framed as acquiring clues, not technical file upload.
- crew appearance slots in Hide: pre-start companion / walkie-talkie / context reaction / LINK support / PIECE support / CATCH-badge reaction / completion.
- crew remains companion, not teacher/grader/answer engine.
- badge book is growth/history, not score/power.
- calendar is date-oriented learning history, not streak.
- cumulative English lexical/sense history survives mission boundaries and can later feed review.

### HIDE LOCK_CANDIDATE visual direction
- fixed island world/environment is the visual anchor; app surfaces must preserve regional continuity.
- environment is high-density and spatial; UI floats over it rather than replacing it with card walls.
- translucent learning panels/wordbook slips are preferred over opaque dashboard tiles where legibility permits.
- visual reference direction: commercial game main-screen composition with deep environment, layered depth and restrained overlays; do NOT copy a copyrighted game's exact art/style/assets.
- character/explorer must share the island's lighting/material/detail language and must not read as a separate glossy doll/avatar-maker render pasted over the world.
- final Explorer visual ID is supplied by the separate character/travel-preparation workflow and consumed through runtime identity slots.

### HIDE SUPERSEDED / forbidden
- mandatory child-facing FIRST FIND → MEANING CLUE → CONNECTION TRAIL → HIDDEN WORDS → FINAL SEEK → SEEK AGAIN as the UI IA.
- Hide drawing a new/random island or unrelated forest background per screen.
- hard-coded character art replacing character_id/Explorer_ID continuity.
- treating the learner avatar as an Exploration Crew member.
- glossy card-wall / generic dashboard treatment that obscures the fixed island environment.

### Cross-app propagation
- fixed-island onboarding/naming/rename invariants: YES / FAMILY_LOCKED.
- Ready/Hide/Snap region placement: YES / FAMILY_LOCKED.
- cross-app badge award overlay semantics: YES / FAMILY_LOCKED; exact visual treatment remains app/family UI review.
- Hide TRACE/LINK/PIECE/CATCH composition: REFERENCE_ONLY.
- Hide 12-word translucent wordbook board: REFERENCE_ONLY / Hide-local.
- high-density environment + translucent overlay composition: LOCK_CANDIDATE reference for family visual synthesis, not final family visual lock.

### Remaining OPEN
- final family-wide art direction and exact rendering language.
- exact island pixel topology / landmark geometry.
- exact transition choreography between Ready map and specialist regions.
- exact badge-overlay art treatment and cadence.
- final physical-device visual QA.
