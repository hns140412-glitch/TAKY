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


## 15. LATEST VISUAL WORK MODE — 2026-09-23

Parent correction:
`C2S/LEARNING_APP_FAMILY_UI_VISUAL_RESUME_C2S_2026-09-23.md`

LOCKED execution mode:
`RECOVER EXISTING BASE → ELEMENT-LEVEL REVIEW → DELTA MAP → DELTA EDIT`.

Current visual task is not a greenfield redesign.

Before a new candidate:
- recover actual prior visual lineage;
- identify exact BASE screen;
- separate ACCEPTED / REFERENCE_ONLY / REJECTED / SUPERSEDED by element;
- state only the deltas to change.

The user must not be used as the routine regression detector for already-known rules.

Onboarding continuity must retain:
Crew familiarity → Primary Companion → character formation → Shared Expedition Accent → Voyage/Drop → Island discovery/name → Base Camp move/name → Ready.

Ready Weekly visual composition remains OPEN/PROVISIONAL, but Planner semantics are LOCKED.
Timer remains LOCKED and outside current redesign.

Recent generic poster / invented-character / placeholder / crop-overlay patch outputs are REJECTED as current visual baselines.

END


## 16. CORRECTION PROPAGATION — 2026-09-23

### Character onboarding
LOCKED:
- direction/preference input and A/B/C result selection are different stages;
- do not repeat the same mood choice in both stages;
- 3-choice direction sets must be semantically distinct, not near-synonyms;
- Visual ID confirmation is followed by Shared Expedition Accent before world entry.

### World entry
LOCKED:
`Voyage/Drop → Island discovery → Island name → Base Camp move → Base Camp name → Ready`.

No visual compression may omit island naming or Base Camp naming.

### Ready Weekly
LOCKED semantic contract:
- Planner-first;
- Mon–Sun;
- fixed commitment / DATED TODO / free window separation;
- today marker;
- before-school task only when actual data contains one;
- island/Base Camp is contextual background, not the information owner.

REGRESSION:
- generic 5-tab bottom navigation on Ready Weekly that creates extra primary screens.

Ready primary architecture remains:
1. 이번 주 여정
2. 오늘의 탐험길
3. 그냥! 지금 하면 돼! Timer

This packet corrects a previously returned visual that did not reflect already-requested user deltas.


## 17. CORE 6 VISUAL ID STATE SPLIT — 2026-09-23

HARD LOCK:
- Core 6 Visual ID identity set and member mapping:
  두비 / 로리 / 잉크 / 노바 / 테이크 / 제로.
- locked species / silhouette / body proportion / identity markings / canonical visual lineage.

PER-CANDIDATE CHECK:
- every newly generated screen/pose/group image must be visually compared to the locked ID source.
- FAIL/OPEN applies to the candidate asset only.

Forbidden state propagation:
`CANDIDATE_UNVERIFIED -> CORE6_VISUAL_ID_OPEN`.

Correct propagation:
`CANDIDATE_UNVERIFIED -> CANDIDATE_UNVERIFIED`
`CANDIDATE_MISMATCH -> CANDIDATE_REJECTED`
`CORE6_VISUAL_ID -> REMAINS_HARD_LOCK`.

This distinction prevents a lost pointer or failed generation from silently recreating the Crew.


## 18. LATEST EXECUTION RESIDUE FILTER — 2026-09-23

Purpose:
prevent stale C2S/HANDOFF/contracts/assets from re-entering the active UI/Visual execution path.

### CURRENT read path
For Learning App Family UI/Visual implementation, read in this order only:
1. this UI Decision Registry;
2. `C2S/LEARNING_APP_FAMILY_VISUAL_MOCKUP_INTEGRATION_REGISTRY_2026-09-22.md`;
3. app-local `HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md`;
4. app-local latest approved-anchor / runtime-binding authority;
5. runtime source and asset manifest.

Older C2S/HANDOFF documents are recovery evidence only unless explicitly referenced by one of the CURRENT pointers above.

### Residue classification
- stale rule already absorbed by CURRENT: SUPERSEDED / SEARCH-EXCLUDED
- duplicate pointer/summary: DEDUP / ARCHIVE
- Handoff contradicting current source/runtime: HANDOFF_OVERRIDE_REQUIRED
- asset path with no binary: ASSET_PENDING, not IMPLEMENTED
- runtime consumer using pre-lock identity: EXECUTION_BINDING_BYPASS / REPLACE
- old screenshot/mockup not in accepted lineage: REFERENCE_ONLY or REJECTED
- orphan asset with zero runtime consumer: ORPHAN_CANDIDATE; remove only after use-count verification

### Character Formation current locks
- Core 6 identity set remains HARD_LOCK.
- Approved implementation anchors CF-A01 / CF-A02 / CF-A03 / CF-A05 are binding for their defined hierarchy.
- Signature Item fixed set is exactly:
  카메라 / 나침반 / 탐험 노트 / 쌍안경 / 물병.
- Character Formation context = before-travel packing/preparation space.
- island = destination hint only before Voyage/Drop.
- sensor depth default = CHARACTER_ONLY; UI itself must not move.
- approved full-screen images are regression references only and may not become runtime UI.

### Flow lock
`Core 6 만나기
→ 동행 탐험대원 선택
→ 동행 탐험대원 이름/호칭
→ 사용자 사진
→ Signature Item
→ 탐험 방향 1
→ 탐험 방향 2
→ 시스템 자동 대비 방향
→ A/B/C 동일 아이 후보
→ 선택
→ 닮기 보정
→ Visual ID 확정
→ Shared Expedition Accent
→ Voyage / Drop
→ 섬 발견
→ 섬 이름
→ Base Camp 이동
→ Base Camp 이름
→ Ready`

Within Character core, the corrected implementation order after photo is:
`사진 → Signature Item → 방향1 → 방향2`.

### Anti-loop rule
A previously settled HARD_LOCK is never reopened merely because a stale file, missing pointer, failed derivative, or old runtime consumer is discovered.
The failure applies to the stale/failed artifact or consumer, not to the canonical lock.

`RESIDUE_FOUND != REOPEN_CANONICAL`
`BINDING_FAILURE -> FIX_BINDING`
`DERIVATIVE_FAILURE -> REJECT_DERIVATIVE`
`CORE6_VISUAL_ID -> REMAINS_HARD_LOCK`

## 19. GLOBAL AI ACTIVITY SLOGAN — AUTHORITATIVE MEANING — 2026-09-23

These slogans are top-level guiding principles across TAKY and must not be reinterpreted as app/domain-specific slogans or reduced to a single tactic such as aggressive review, defensive review, validation, or implementation.

### Think Again, Keep Your Key
Authoritative meaning:
- 핵심을 놓치지 말고 다시 생각하라.
- 답을 풀 열쇠는 이미 가지고 있다.

Execution meaning:
- 다시 보고
- 의심하고
- 기준 단서를 복구하고
- 다른 방법을 찾되
- 핵심 / 맥락 / 의미 / 권한 / 소유권 / 최신 수정 / 제어권을 잃지 않는다.

### Think Again, You’re The Key
Authoritative meaning:
- 방법을 찾고 해결하라.
- 결국 답을 만들어내는 핵심 주체는 인간이다.

Human authority:
- AI 활동의 최종 판단과 책임 주체는 인간이다.
- HUMAN IS THE KEY.
- HUMAN IS THE TRIGGER.
- USER != DEBUGGER.

### Unified execution cycle
`HUMAN INTENT / DESIRED OUTCOME
→ THINK AGAIN
→ KEEP YOUR KEY
→ FIND A WAY / SOLVE
→ YOU'RE THE KEY
→ VERIFY / CORRECT / CONTINUE`

Operational methods such as offensive review, defensive protection, quarantine, rollback, validation, implementation, or recovery are subordinate methods only.
They MUST NOT redefine the slogans.

`SLOGAN -> GOVERNS METHODS`
`METHODS != SLOGAN MEANING`


## 20. APPROVED STATE INHERITANCE — PRIOR CONFIRMED DECISIONS — 2026-09-23

This section restores previously confirmed decisions as inherited protected state.
A newer local implementation slice MUST NOT silently narrow, replace, or reinterpret them.

### Core 6 / companion formation
- Core 6 = 두비 / 로리 / 잉크 / 노바 / 테이크 / 제로.
- Existing confirmed Visual IDs remain HARD_LOCK across Ready & Set / Snap & Pop / Hide & Seek.
- All six are introduced before primary companion selection.
- One becomes the primary companion; the other five remain Crew, not discarded.
- canonical character identity and user-facing nickname/display name are separate.
- relationship/history/atlas records follow the same companion identity across the family.
- user character = protagonist; selected companion = partner; remaining five = Crew.

### User character formation
- source photo identity is preserved.
- no completed user character is shown before the A/B/C candidate stage.
- user selects Direction 1 and Direction 2; system adds the contrast direction.
- A/B/C are the SAME CHILD with different expression/direction, not three different identities.
- profile recreation may reopen user choices, but it does not mutate Core 6 canonical identity.
- shared expedition accent may propagate to the user character / Crew clothing accents without changing character identity.

### Tools / items — inherited scope
The locked five Signature Items are NOT the total tool inventory.

Character Formation selection contract:
- 카메라
- 나침반
- 탐험 노트
- 쌍안경
- 물병
Choose exactly one.

Previously confirmed character-associated tool vocabulary remains available as world/character semantics and MUST NOT be erased by the five-item selection projection:
- 두비: existing confirmed Doobi tool lineage from the Core 6 guide remains inherited.
- 로리: 돋보기 / 식물 도감 / 지도.
- 잉크: 노트 / 펜 / 잉크.
- 노바: 별 조각 / 랜턴 / 별 지도.
- 테이크: 쌍안경 / 로프 / 멀티툴.
- 제로: 물병 / 방수 케이스 / 매트.

Common exploration asset vocabulary includes maps, books, lanterns, bags/luggage, camera, binoculars, water bottle, compass, travel tags, photos/postcards and other approved preparation-space props.

Snap & Pop retains its previously confirmed separate rule:
- five tools are freely usable;
- old map/tool unlocking progression is SUPERSEDED.
Do not project that unlock system back into Character Formation.

### Shared world / journey inheritance
- Character Formation occurs in the PRE-TRAVEL preparation/packing world.
- before Voyage/Drop, the island is only hinted by map/photo/postcard/window/travel notes.
- after Voyage/Drop: island discovery → island naming → Base Camp move → Base Camp naming → Ready.
- one shared island/world is retained across the app family rather than creating a separate island per app.
- Ready & Set = Base Camp / hub.
- Hide & Seek = jungle / waterfall exploration region.
- Snap & Pop = beach exploration region.
- island name and Base Camp name may change.
- learning history, badge/growth history, Crew relationship, Explorer_ID, island/world continuity remain accumulated.

### Shared family systems
Previously confirmed family-wide systems remain cross-app concerns:
- 탐험대 rules;
- badge system (star = grade/classification);
- gems;
- wishes;
- blessings;
- meaningful/fun history shown with badge on sharing surfaces.

These systems are not owned or redefined by a single app-specific UI slice.

### Inheritance rule
`NEW RESULT → INHERIT APPROVED DNA → APPLY ONLY APPROVED DELTA → COMPARE`

Therefore:
`LOCAL_RUNTIME_PROJECTION != NEW_CANONICAL`
`5_SIGNATURE_ITEMS != TOTAL_TOOL_INVENTORY`
`8_COMMON_TOOL_ASSETS != TOTAL_WORLD_TOOL_INVENTORY`
`APP-SPECIFIC IMPLEMENTATION != FAMILY-WIDE REDEFINITION`

If a local implementation is narrower than an inherited confirmed decision, the local implementation is incomplete; the inherited decision is not reopened.
