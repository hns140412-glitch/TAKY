# READY WHOLE IMPLEMENTATION CONTRACT

Status: REV_00 / CANONICAL LOWER-LAYER PROJECT CONTRACT / EVOLVING DESIGN SOURCE
Date: 2026-09-11
Authority: TAKY / GRAND MASTER > GUIDE FAMILY LEARNING OS > LEARNING APP FAMILY MASTER > THIS READY PROJECT CONTRACT > Ready implementation
Review command / subtitle: **Think Again, You’re The Key!**

This file owns Ready-specific realization and anti-omission rules. Shared GUIDE, Family Learning, app-family, Handoff and deployment authority remain in their higher owners.

## 0. Recovery / anti-omission

For Ready work:

`TAKY canonical → GUIDE FAMILY LEARNING OS → LEARNING APP FAMILY MASTER → READY WHOLE CONTRACT → latest Ready project master/lineage → Handoff/current truth → live GitHub branch/runtime/tests → actual device evidence`

Hard:
- Handoff is recovery evidence, not canonical authority.
- Code existence does not prove actual behavior.
- UI mockup does not prove runtime behavior.
- Do not ask the user to reconstruct a recoverable prior rule.
- Before inventing a local rule, recover applicable existing Guide/Family/Ready rules.
- Inaccessible raw turns remain `UNVERIFIED_SOURCE_COVERAGE`.

## 1. Product / authority split

### Parent
`PARENT = CAPTURE / INPUT / CONFIRM / SUPPORT`

Parent may:
- capture homework/source facts
- enter and revise real schedule facts
- confirm OCR/recognition results
- correct missing/incorrect facts
- grade/support later
- confirm child-reported actual work
- respond to WAITING_FOR_PARENT

Parent does NOT own:
- daily homework distribution
- daily study amount
- difficulty interpretation
- estimated-time authority
- pedagogical sequencing
- automatic allocation

Parent mode = support, not surveillance.

### Learning Master / Subject
`SUBJECT = INTERPRET / LOAD ANALYSIS`

Owns concept/skill target, difficulty/cognitive/activity load, divisible learning units, subject-specific meaning and uncertainty.

### Planner / MAIN
`MAIN = ALLOCATE`

Owns dated task creation, schedule/deadline/load balancing, carry-over, weekly/daily allocation, remaining-work recalculation and condition-aware adjustment.

Hard:
- `SUBJECT INTERPRETS; MAIN ALLOCATES`
- `FREE TIME EXISTS ≠ MUST STUDY`
- `CAPACITY ≠ REQUIRED STUDY AMOUNT`
- `SCHEDULE COMMITMENT ≠ HOMEWORK TEMPLATE ≠ DATED TODO INSTANCE ≠ PROGRESS EVENT`

### Child
`CHILD = VIEW / FACT INPUT WHEN APPLICABLE / SELECT TODAY / EXECUTE`

Child sees whole assignment facts plus Planner-prepared TODAY TASK, may enter newly received factual school/event homework, selects allowed execution order and executes.

### Ready & Set
`READY = BASE CAMP / EXECUTION + SESSION ORCHESTRATOR`

Ready receives confirmed/planned work and owns:
`GOAL AWARENESS → TODAY TASK AWARENESS → EXECUTION ORDER → START → SESSION/LAP → SPECIALIST ROUTE → RETURN → RESULT/EVIDENCE → REPORT → ACTUAL RESULT UPWARD`

Ready must not silently absorb Learning Master or Planner authority.

## 2. Parent mode UX

Visible distinction:
- Parent topbar: `부모 모드`
- Parent home primary: `숙제 입력 · 확인`
- Child topbar: `아이 모드`
- Child home primary: `오늘 탐험 정하기`

If Parent/Child screens are functionally identical, FAIL.

Parent Home operational zones:

### 일정 관리
- active timetable profile
- semester / vacation schedule
- academy day/time/subject
- school/life commitments
- temporary cancellation/makeup
- hospital/family/special event
- effective date/period
- confirmation state

### 숙제 입력 · 확인
- camera capture
- manual factual input
- detected/entered facts
- confirmation required
- provenance
- deadline boundary
- book/workbook/package linkage

### 학습 지원
- current progress
- completed/partial
- child report confirmation
- grading
- WAITING_FOR_PARENT
- applicable artifacts/recordings/files

Do not turn Parent Home into a generic admin spreadsheet.

## 3. Schedule first / fixed-but-editable baseline

`SCHEDULE FIRST, ASSIGNMENT SECOND`

Confirmed Base Timetable = current operating baseline.

Fixed means stable planning authority, NOT immutable data.

Operational state:

`BASE_TIMETABLE_CONFIRMED`
`→ TEMP_EVENT_OVERRIDE` for one-off change
`→ SCHEDULE_REVISION` for recurring/semester/vacation/academy/school pattern change
`→ CAPACITY_RECALCULATION`
`→ HOMEWORK_REALLOCATION`

Rules:
- If no schedule delta exists, keep current effective baseline; do not reopen full timetable confirmation.
- Parent may edit real-world schedule facts.
- Planner may not arbitrarily move externally fixed commitments.
- History stays linked to the schedule revision effective at that time.
- Active Ready Focus Session must not be silently rewritten by schedule sync.

Separate meanings:
- `parent_editable`
- `planner_movable`

`parent_editable ≠ planner_movable`

## 4. Notion / standalone / hybrid schedule sources

Supported source modes:

### NOTION CONNECTED
Notion timetable/calendar is an operational source.

### STANDALONE
Family/Ready planning layer stores schedule without Notion.

### HYBRID
Recurring schedule may come from Notion while temporary overrides/events come from local/Ready, or vice versa.

Hard:
- Planner consumes one normalized internal schedule model regardless of source.
- Notion is not canonical authority.
- Notion connection loss must not destroy the local execution loop.

Normalized candidate:

`ScheduleEvent(event_id, source, source_id, member_id, profile_id, title, category, subject, start_at, end_at, recurrence, effective_from, effective_to, confirmed, parent_editable, planner_movable, ready_enabled, override_of, updated_at)`

`ScheduleProfile(profile_id, name, effective_from, effective_to, state, revision, provenance)`

Current Notion `Ready & Set 시간표` already contains schedule title, weekday, start/end text, type, changeable, confirmation state, Ready linkage, task relation, family relation, order and original memo.

Current delta:
- true datetime/event representation not yet verified
- term/vacation profile/effective period not yet implemented
- `변경 가능` must not ambiguously combine parent editability with Planner movability
- preserve existing DB where useful; do not break it merely to satisfy calendar UI

Exact native Notion Calendar schema = HOLD / ADR until implementation review.

## 5. Homework / assignment intake

Parent primary entry: `숙제 입력 · 확인`

Shared rapid capture contract:

`촬영 시작 → 셔터 → 로컬 임시저장 → 즉시 다음 촬영 → 반복 → 분석 맡기기/저장하고 분석 → batch OCR/analysis → grouping/classification → quality gate → failed page only retake → targeted re-analysis → Review-before-Commit → confirmed assignment FACT → external save/sync`

Hard:
- no per-shot forced classification
- no whole-batch restart for one bad image
- photo count must not dominate rapid capture
- system copy stays literal; Guide carries warmth/wit
- Ready may render/route the capture surface
- OCR/intake interpretation belongs to GUIDE/MAIN + Learning Master, not Ready

Ownership:
`CAPTURE SURFACE → GUIDE/MAIN Assignment Intake → Learning Master interpretation → Planner allocation`

Common factual fields may include:
`assignment_id / member_id / subject / source_type / source_actor / provenance / captured_at / assignment_cycle / book/workbook_ref / range / teacher_instruction / artifacts / confirmation_state / deadline_boundary / analysis_state / planner_state / lifecycle`

If child/parent facts conflict:
- preserve both claims
- mark `CONFIRMATION_REQUIRED`
- do not silently overwrite

## 6. Learning-unit / load interpretation

Hard:
- `PHYSICAL PAGE ≠ LEARNING UNIT`
- `MINUTES ≠ PRIMARY SPLIT UNIT`

Possible load evidence:
- new concept
- reading/comprehension
- memory/recall
- repetitive calculation
- reasoning/thinking
- writing
- error/correction likelihood
- sustained attention
- parent-help dependency
- transition fatigue

Time/page count may be factual inputs and later reality checks, but not sole learning-load truth.

Examples:
- 연산: repetitive calculation/fatigue
- 한자: memory/recall
- 국어: reading/comprehension/writing
- 사회: reading + concept linkage
- 수학: concept/application/error correction
- 생각하는 피자: reasoning/exploration/sustained thinking

Do not blindly stack multiple high-reasoning/high-load tasks because minutes fit.

## 7. Planner allocation / condition

Planner inputs:
`effective schedule + confirmed assignment facts + deadline + divisible learning units + difficulty/cognitive/activity load + remaining amount + recent actual performance/pace + carry-over + condition evidence + available execution windows`

Planner outputs:
- dated TODAY TASKs
- amount by executable learning unit
- order constraints/recommendation
- carry-over
- next replan boundary

Condition is a planning variable, NOT a diagnosis or child score.

Candidate evidence:
- tired / okay / energetic
- late return / sleep context if explicitly known
- reasoning-heavy day
- recent Focus interruptions
- recent actual completion pace
- recent plan-vs-actual
- parent-help availability where relevant

Rules:
- deterministic/local rules first
- cached/reused interpretation second
- AI only when ambiguity materially benefits from it
- one unusual observation must not justify unbounded load increase
- being fast does not justify inflating homework volume

Exact weights/thresholds = HOLD until validation.

## 8. Cost gate

`USER REQUEST ≠ EXPENSIVE EXECUTION AUTHORIZATION`

Normally deterministic/no paid AI needed:
- schedule matching
- deadline calculation
- carry-over
- deterministic allocation
- state transitions
- timestamp timer
- local persistence
- normal app routing

Potential variable cost:
- OCR/vision provider
- LLM interpretation
- speech analysis
- paid character/image generation

High-cost path:
`expected usage → costly segment → lower-cost alternative → approval`

Paid image generation remains locked without explicit approval.

## 9. Ready execution/session contract

Core:
`GOAL → TODAY TASKS → ONE TARGET TIME → START SESSION → TASK/LAP → SPECIALIST APP IF NEEDED → RETURN → WRAP-UP → END → REPORT`

Hard:
- ONE SESSION
- ONE TARGET TIME
- MULTIPLE TASKS
- ONE ACTIVE TASK
- ONE ACTIVE LAP
- Ready = single session-state owner

`TASK_CHANGE = LAP_END + NEXT_LAP_START`

`APP_SWITCH != PAUSE`
`APP_SWITCH != LAP_END`
`APP_SWITCH != SESSION_END`

`SESSION_END != TASK_COMPLETE`

Task states:
`COMPLETED / PARTIAL / DEFERRED / BLOCKED / WAITING_FOR_PARENT`

## 10. Cross-app handoff

Ready outbound specialist handoff must preserve applicable execution context:
- session_id
- goal_id
- task_id
- lap_id
- target_time
- session_start_at
- timing state
- pause/issue state
- return_target
- from_app

Hide/Snap may own specialist task experience but must not create a competing top-level Ready session.

Return must restore the same Ready execution context.

## 11. Timer / background / lock continuity

Timer authority = timestamps. Foreground interval ticks are display helpers only.

Must survive/restorably handle:
- Ready internal navigation
- unrelated app switch and return
- Hide switch and return
- Snap switch and return
- Safari/PWA backgrounding
- screen lock/unlock
- temporary network loss
- BFCache/pageshow
- safe reload/recovery where platform permits

Hard:
- screen lock != pause
- app switch != pause
- network failure != session end
- network outage must not block local Timer/Core
- returning to Ready must not require “start again”
- no duplicate session after return

## 12. Pause / ISSUE / Recording / System Wait

Distinct states:

### Explicit Pause
Child intentionally pauses.

### ISSUE
Real learning interruption/problem requiring attribution.
Examples may include preparation/material/help/condition interruptions.
Long time alone does not prove ISSUE or stuck.

### Recording
If required by the task, recording/re-recording is learning execution.

`RECORDING != PAUSE != ISSUE`

### System Wait
AI/server/file/network processing wait.
- not child failure
- not ISSUE automatically
- system wait must not inflate Focus attribution

App switch alone is none of these.

## 13. Lock-screen timer requirement

Separate two requirements:

A. **Timer continuity while locked** = required Ready runtime behavior using timestamp restoration.

B. **Timer visible on lock screen** = preserved user requirement from prior Ready Handover.

Hard:
- pure PWA must not be falsely presented as providing native iOS Live Activity behavior
- current lock-screen visibility implementation = NOT IMPLEMENTED
- native/wrapper/App Clip/ActivityKit route = architecture decision candidate
- actual iPhone lock-screen result is required before PASS

## 14. Retrospective/manual actual result

`READY NOT RUNNING ≠ NO LEARNING`

If learning occurred outside an active Ready session:
- child may report whole/partial
- parent may report
- parent may confirm child report

Provenance:
`AUTO / CHILD_REPORTED / PARENT_REPORTED / PARENT_CONFIRMED`

Do not fabricate:
- elapsed time
- Focus time
- fake Session
- fake Lap

Create reconciliation/result evidence linked to task/assignment.

## 15. Real-world phone availability

Known design requirement:
- morning phone use may support a brief preview
- phone is generally unavailable/off during school
- main Ready execution begins after returning home

Hard:
- `PHONE OFF ≠ LEARNING INACTIVE`
- `READY NOT RUNNING ≠ CHILD DID NOTHING`
- school gap must not look like failure
- no GPS/location tracking

Morning success:
child can close the phone and still remember today’s learning goal / what must be done.

After-school success:
child opens Ready and knows what to do next without asking a parent.

## 16. Visual schedule hierarchy

Information priority:
`WHAT + HOW MUCH = primary`
`WHEN = secondary`
`HOW LONG = Focus-level importance`

Zoom:
`WEEK MAP → DAY MAP → TODAY EXPEDITION MAP → FOCUS CLOCK`

WEEK:
weekly rhythm / confirmed commitments / event indications.

DAY:
today’s learning goal + tasks + enough time context; school hours need not dominate.

TODAY EXPEDITION:
confirmed TODAY TASKs become spatial destinations/nodes with real amount/unit.

FOCUS:
reduce visual noise and execute one current task.

Hard:
- final child schedule ≠ plain text list
- map itself must carry information structure
- “white cards on island background” pseudo-map = FAIL
- schedule is context; learning goal/tasks are protagonist

## 17. World / event transport

Cloud Drop vs Voyage:
- First Journey intro/first-arrival choice only
- both converge to the same island/base-camp system

Normal routine:
- child’s Island

Special Event:
- pier/harbor
- boat
- Event Island/destination
- return to own Island/Base Camp

Do not use boat for every ordinary academy trip.
Ready does not invent Event classification; actual schedule authority does.

Growth/badges/Wish Shop remain Snap & Pop ownership.

## 18. Guide / 동반 탐험대원

Existing Guide rules remain functional authority.

`동반 탐험대원 = Ready-world persona of Guide`

Do not invent a second assistant role.

Guide:
- child’s ally
- not teacher
- not judge
- not parent proxy
- not surveillance

Guide presence is context-sensitive:
departure / transition / blocked-help / return-completion.

During Focus, presence is reduced unless needed.

### 18.1 MAIN GUIDE + RANDOM GUEST — READY PROJECT CONTRACT

Ready REV_07 inherits the confirmed REV_06 Main Guide + Random Guest lineage unless explicitly overridden.

Project semantics:
- Main Guide remains the child's continuing Ready companion.
- An applicable Duo Coaching / English sentence recording event may bring exactly one Random Guest alongside the Main Guide.
- Guest selection is Smart Random rather than unrestricted repetition; exact weights remain controlled-flex/project detail.
- Guest presence does not create a second Guide authority or replace the Main Guide relationship.
- `SPECIAL FRIEND ≠ RANDOM GUEST` unless separately recovered direct evidence establishes equivalence.

Duo tone hard lock:
- the child, the child's weakness, pronunciation gap or mistake is never the comedy target;
- light comedy may target the situation, the Guides, timing or a harmless event;
- confidence and successful communication take priority over pronunciation-score pressure.

Share-card relationship:
- ordinary applicable task/share representation defaults to child + Main Guide;
- when an actual Duo Coaching event occurred and the Guest materially participated, the corresponding Duo result/share representation may include child + Main Guide + that Guest;
- a Guest SHALL NOT be inserted into a share/result merely because a Guest exists in the roster.

## 19. First Journey

Whole first-run flow:

`REGISTER → PHOTO → 1ST 3-CARD CONSULTATION → 1ST CONFIRM → 2ND 3-CARD CONSULTATION → 2ND CONFIRM → SYSTEM AUTO CONTRAST DIRECTION → KEYWORD COMBINATION → A/B/C CANDIDATE DIRECTIONS → COMPARE/SELECT → RESEMBLANCE REFINEMENT → FINAL CONFIRM → CHARACTER MASTER → GUIDE/COMPANION SELECT → NAME → CLOUD DROP or VOYAGE INTRO → ISLAND REVEAL/NAME → BASE CAMP REVEAL/NAME → CREW NAME → FIRST REAL SCHEDULE/GOAL AWARENESS`

Hard:
- PHOTO = top identity authority
- mood/direction ≠ personality diagnosis
- the child makes exactly **2 direct consultation selections**
- each child selection is **1 of 3 cards**
- after each selection, show an explicit confirmation step before advancing
- the **third contrast direction is derived automatically by the system** from the first two selections; the child does not perform a third consultation round
- combine first choice + second choice + auto contrast into three distinct A/B/C candidate directions
- candidate choice ≠ final confirmation
- original PHOTO remains refinement authority
- companion uses existing Guide authority
- first Journey must connect into real schedule/task awareness
- paid generation remains approval-gated

Regression fail:
- old 6-mood choose-3 UI revived
- 3 child consultation rounds
- direct jump from photo to three generated candidates without the two consultation confirmations
- auto contrast presented as a third child choice

## 20. Focus UI confirmed direction

Preserve:
- headline `그냥! 지금 하면 돼!`
- selected task directly below
- Full Analog Clock = visual hero
- actual current local time
- remaining time primary
- target time secondary
- top-right `♪` = BGM quick control
- bottom panel = current task + BGM state
- Pause / Complete / ISSUE reachable without vertical scrolling
- no fake iOS status bar/notch
- safe-area aware
- 100dvh
- remove `FOCUS MODE`

Do not replace the confirmed clock with a game HUD.

## 21. Visual Fidelity Gate

`REFERENCE SHOWN ≠ LOOSE INSPIRATION`

Before WEEK/DAY/Expedition implementation:
1. logic/ownership locked
2. visual concept locked
3. actual mockup/reference locked at target viewport
4. implementation
5. same-viewport side-by-side comparison
6. responsive/device regression
7. PASS only on actual rendered result

Fail:
- generic SaaS/dashboard aesthetic
- preschool worksheet quality
- cheap/free-icon map
- flat unrelated art mixed with premium dimensional character
- card-UI escape
- functional PASS claimed as visual-fidelity PASS

## 21A. External UI reference activation — 2026-09-19

Ready activates `TKY-UIREF-001` in validation-first mode.

Reviewed source roles:
- Material Design 3: component taxonomy/state/reference comparison only.
- Apple HIG/UI Design Tips: iPhone/PWA platform-fit, touch-target, legibility, layout, feedback and accessibility validation.
- daisyUI: normalized component vocabulary/state naming and optional implementation reference; no automatic theme inheritance.
- Mobbin: real-world flow/pattern comparison; no branded composition copying and no automatic pattern adoption.

Hard:
- `EXTERNAL REFERENCE != READY AUTHORITY`.
- Existing adventure/exploration identity, Focus direction and confirmed Ready locks remain protected.
- Reference findings may create `ADOPT / ADJUST / HOLD / REJECT / CONFLICT` candidates; material visual/interaction changes require authorization under TAKY governance.
- Generic SaaS/dashboard convergence caused by external libraries/references = FAIL.
- Current supplied reference message claims 9 sites + 110 UI terms, but only four named sources are currently recoverable; the remaining material stays `UNVERIFIED_SOURCE_COVERAGE` until recovered.

## 22. Implementation truth snapshot — reverified 2026-09-12

This snapshot is evidence only and becomes stale as code changes.

Known:
- Ready isolated branch: `runtime-session-bridge-2026-09-10`
- branch HEAD reverified at reflection: `0dabe55bff83262d53c084c87faa11d2f2e56f52`
- Parent/Child semantic code = partial
- Parent capture-first UI = partial/gap
- learning-load runtime interpretation = gap/partial
- Planner allocation = stale/partial, needs rework
- Notion timetable DB = exists
- native Notion Calendar model = ADR/gap
- standalone/hybrid schedule adapter = gap
- schedule profile/revision/override = gap
- specialist handoff code = exists, real iPhone timer roundtrip unverified
- timestamp timer baseline = exists, lock/swap regression unverified
- lock-screen visibility = requirement preserved, not implemented
- retrospective actual-result candidate = partial, device unverified
- WEEK/DAY final visual = design gate
- Focus visual direction = confirmed, final fidelity regression still needed

`CODE EXISTS ≠ ACTUAL BEHAVIOR VERIFIED`

## 23. Regression / release gates

### Parent / intake
- Parent Home visibly differs from Child Home
- capture entry obvious
- no Parent difficulty/minutes/allocation authority
- fact confirmation works
- conflicting facts become confirmation-required

### Schedule
- Notion-connected
- standalone
- hybrid
- profile effective date
- semester/vacation switch
- academy day/time/subject revision
- temporary override
- history preserved
- active Focus not corrupted

### Planner
- schedule + deadline + load + condition
- no minute-capacity-first authority
- carry-over
- actual-result feedback
- no Ready-side allocation authority drift

### Continuity
- Focus start
- lock/unlock
- unrelated app switch/return
- Hide roundtrip
- Snap roundtrip
- offline/reconnect
- BFCache/reload recovery
- task switch
- partial/complete
- wrap-up

FAIL if:
- timer stops/resets/drifts
- duplicate session created
- app switch ends Lap
- return loses task/lap
- network failure blocks local execution
- active update force-reloads session
- Parent controls leak into child execution
- Guide becomes parent proxy
- schedule sync rewrites history
- Ready First Journey regresses to three child consultation rounds or old 6-mood selection
- Random Guest is conflated with Special Friend or used as a second authority

## 24. Resume contract

New conversation:

`TAKY canonical → GUIDE/Family + Learning App Family → READY WHOLE CONTRACT → READY_CURRENT_TRUTH_LATEST/Handoff → live branch HEAD → runtime/deploy evidence → first unresolved gate`

When a requirement appears:
1. determine whether new or previously lost
2. recover canonical/master/handoff/code evidence first
3. restore recovered rule
4. classify true new item
5. never silently rewrite authority

## 25. Implementation order

Do not jump from logic directly to child visual HTML.

1. Parent Mode functional information architecture
2. Schedule profile/revision/override data contract
3. Notion/standalone/hybrid adapter boundary
4. Homework capture entry + Review-before-Commit
5. Learning-load interpretation boundary
6. Planner allocation contract
7. TODAY TASK projection
8. cross-app/timer continuity harness
9. WEEK/DAY visual contract and hero mockup
10. implementation
11. same-viewport visual QA
12. iPhone continuity regression
13. only then explicit production promotion

## 26. Recovered source lineage

Material recovery evidence includes:
- `Ready_Set_Ui_Master_Logic_REV_06.md`
- `Ready_Set_Ui_Master_Logic_REV_07.md`
- `Ready_Set_HANDOVER_20260904.md`
- `READY_CURRENT_TRUTH_HANDOFF_2026-09-08_1210_KST.md`
- `READY_CURRENT_TRUTH_LATEST.md`
- `TAKY_INDEPENDENT_FULL_CONVERSATION_REAUDIT_2026-09-07.md`
- `TAKY_CURRENT_CHAT_ACCESSIBLE_PRESERVATION_2026-09-10_MOBILE_GATEWAY.md`
- Notion `Ready & Set 시간표`
- recovered direct conversation evidence for Main Guide + Random Guest / Duo Coaching / share-card conditions
- current accessible 2026-09-11~12 conversation/user corrections
- live GitHub branch/runtime evidence

Inaccessible raw prior turns remain `UNVERIFIED_SOURCE_COVERAGE`.

END
