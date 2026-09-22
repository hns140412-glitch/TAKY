# LEARNING APP FAMILY UI DECISION REGISTRY — 2026-09-22

Status: ACTIVE CROSS-APP UI DECISION REGISTRY
Purpose: share UI review/lock state across Ready & Set / Snap & Pop / Hide & Seek without flattening different maturity levels.

## 0. READ FIRST — integrated successor authority

For Character / Profile Update / Age Progression / Exploration Crew / Voice & Listening / Episode & Memory / Badge / Shared Island / Ready / Hide / Snap UI projection, read first:

`C2S/LEARNING_APP_FAMILY_INTEGRATED_LOGIC_UI_CANONICAL_2026-09-22.md`

That file is the current correction-propagation authority for the integrated scope.
This registry remains the cross-app UI status ledger, but stale app/family entries here must not override the integrated canonical.

Important corrections carried by the integrated canonical:
- Ready primary UI = exactly 3 screens: 이번 주 여정 / 오늘의 탐험길 / locked Timer.
- Character consumer projection = V02; V01 is superseded.
- Exploration Crew shared semantics are centralized at TAKY family level; Snap remains source lineage and app-local adapter, not sole family owner.
- Character/Profile becomes versioned across profile photo updates and age progression; Explorer_ID persists.
- initial Core Crew 6 + Expansion Crew 12 + Special Guest separate class is the current roster direction; historical max-20 character ceiling is not hard authority.
- Crew listening/waiting/voice/episode/memory rules are shared logic and must project consistently to all apps.
- Badge and Crew are family-wide continuity systems.

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
- Ready = Base Camp / Planner orchestration;
- Snap = Beach;
- Hide = Jungle / Waterfall;
- current Explorer and companion continuity across regions;
- island/base-camp identity persistence;
- exploration crew identity rendered from runtime slots rather than hard-coded character;
- child-facing UI uses exploration language rather than developer/module language;
- 390×844 mobile baseline;
- one dominant primary action per task screen;
- non-happy states are first-class;
- Badge / Growth / Gem-Wish / Affinity are semantically distinct;
- Badge star count = Star Grade / 성급 1–5;
- shared badge system crosses apps;
- shared Exploration Crew semantics cross apps;
- share may carry badge/history context;
- no Netlify / production / main merge during UI definition.

LOCK_CANDIDATE:
- family Screen Composition Standard, subject to Ready 3-screen correction;
- island world pre-mockup criteria;
- shared Badge Canonical/Visual/Share contracts;
- age-aware Character progression and profile-refresh UI contract;
- standard Crew roster target = Core 6 + Expansion 12.

OPEN:
- exact family-wide visual art style;
- exact pixel topology of island;
- final shared badge collection entry point;
- final cross-app visual transition choreography;
- exact age-stage thresholds;
- Special Guest roster/count;
- final Crew encyclopedia / friend-album IA.

## 3. Ready & Set UI state

### LOCKED / authoritative structure
- Ready is Base Camp and session/planner orchestrator.
- primary UI = exactly 3 screens:
  1. 이번 주 여정
  2. 오늘의 탐험길
  3. 그냥! 지금 하면 돼! Timer
- Timer visual direction + assets are locked; redesign forbidden unless explicitly reopened.
- Mission / Focus / Wrap-up / Result / approval / carry-over / capture are state/component/sheet/overlay/transition concerns unless explicitly promoted through impact review.
- character/crew slots are runtime-driven.
- specialist app logic is not reimplemented inside Ready.
- phone baseline 390×844.

### PROVISIONAL / active UI review
- exact Weekly composition;
- exact Daily composition;
- Base Camp / translucent planner balance;
- final Design System;
- final high-fi Weekly/Daily.

### CONFLICT / REVIEW_REQUIRED
- current generic Ready “획득 별” conflicts semantically with shared Badge Star Grade.
- older central screen models that treat Base Camp / Map / Session / Result as separate Ready primary screens are stale.

### DEVICE_OPEN
- physical keyboard/safe-area/audio/camera and installed PWA visual behavior.

## 4. Hide & Seek UI state

### LOCKED / authoritative structure
- Hide = Jungle / Waterfall vocabulary retrieval specialist.
- Home states: acquire → review/correct → confirmed set ready.
- learner-facing IA: TRACE / LINK / PIECE / CATCH.
- Memory Ladder contextual.
- Ready owns planner/date/family-session completion.
- Calendar = history, not streak.
- Badge Book = growth/history, not power/score.
- no Snap Gem/Wish economy import.
- character/crew art runtime-driven.
- crew is companion, not teacher/grader/answer engine.

### LOCK_CANDIDATE
- screen sequence and visual composition.
- crew walkie-talkie/listening/reaction slots.
- translucent wordbook treatment.
- final badge overlay treatment.

### OPEN
- final high-fi art direction;
- exact island transitions;
- exact badge award visual;
- device visual QA.

## 5. Snap & Pop UI state

### LOCKED product rules
- thought-to-expression specialist + Ask→Understand axis.
- Beach region.
- five expression landmarks always accessible.
- child final authorship.
- Ask and Imagination semantically distinct.
- Wish Economy is Snap-owned.
- Badge != score/power.
- Special = special encounter method, not stronger character.
- Growth / Badge / Wish separation.
- shared island / Character / Crew continuity.

### CENTRALIZATION CORRECTION
Historical Snap Crew master remains important source lineage for:
- personality,
- listening/waiting,
- intervention ladder,
- relationship,
- world routine,
- episode behavior,
- voice accessibility.

But family-wide Crew semantics are now TAKY shared canonical.
Snap keeps app-local Crew projection, not sole family ownership.

### PROVISIONAL / OPEN
- primary nav proposal;
- exact Home composition;
- exact Result composition;
- exact Ask/Imagination placement;
- final high-fi language;
- exact component geometry.

Snap must be recomposed under the integrated family logic before final visual freeze.

## 6. Character / Profile state

### HARD LOCK / current
- source-photo identity authority for each visual version;
- same child, different A/B/C direction;
- two direct mood/direction choices + system auto contrast;
- exactly one Signature Exploration Item;
- no completed user character before A/B/C;
- natural age-appropriate child proportions;
- generic/chibi identity compression forbidden;
- current consumer contract = CHARACTER_VISUAL_ID_PROJECTION_V02.

### NEW lifecycle requirement
- Explorer_ID persists across profile/photo changes.
- Character Visual ID is versioned.
- profile/photo updates may trigger same-identity refresh after review/confirmation.
- age progression uses explicit profile age context + elapsed time, not age guessing from image.
- previous Character versions remain historical lineage.

## 7. Exploration Crew state

### HARD LOCK
Core 6 Visual IDs:
- 두비
- 로리
- 잉크
- 노바
- 테이크
- 제로

Korean 로리 preserved; historical English Tori remains name-lineage review.

### Current roster direction
- Core Crew = 6
- Expansion Crew = +12 after Core quality stabilizes
- Standard Crew target = 18
- Special Guests = separate encounter class

Historical 20 behavior slots remain archetypes, not a 20-character roster requirement.

### Shared behavior
PERSONALITY → HABIT → REACTION → RELATIONSHIP EXCEPTION → WORLD ROUTINE → MEMORY

Intervention:
OBSERVE → WAIT → SHORT REACTION → QUESTION → HINT → MINIMAL RE-QUESTION → CHILD EXPRESSION

Listening/waiting are explicit shared states.
Absence never creates penalty.
Return is reunion opportunity.

## 8. Badge state

Badge remains family-wide shared process/experience history.

Pipeline:
local action → observation → evidence → shared event → candidate → review → activation → instance/progress → presentation/history/share.

No app may silently award family badge from local event.

Badge != EXP != Gem != Affinity != Character Level != Mastery.

## 9. Cross-app propagation rules

Propagate automatically:
- Explorer/Character continuity;
- Crew canonical identity and behavior semantics;
- Crew listening/waiting rules;
- Badge semantics/star-grade;
- shared island topology;
- continuity/return constraints;
- terminology corrections.

Reference only:
- Ready planner composition;
- Hide TRACE/LINK/PIECE composition;
- Snap writing composition.

Never propagate:
- app-specific economy;
- app-specific learning semantics;
- provisional high-fi choices;
- legacy assets.

## 10. Regression rule

Before any new mockup or implementation:
1. read the integrated canonical first;
2. read this registry;
3. read app-local latest C2S/handoff;
4. preserve LOCKED decisions;
5. flag conflicts;
6. map logic → owner/state/event/persistence → UI before high-fi.

END
