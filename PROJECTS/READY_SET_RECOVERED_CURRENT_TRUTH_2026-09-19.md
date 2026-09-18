# READY & SET — RECOVERED CURRENT TRUTH 2026-09-19

Status: CONTEXT RECOVERED / IMPLEMENTATION GAPS IDENTIFIED / PRODUCT EDITS NOT YET APPLIED  
Project manifest: `PROJECTS/READY_SET_CONTEXT_MANIFEST.json`  
Resolution: `HISTORY/2026-09-19_READY_SET_CONTEXT_RESOLUTION.json`

## 1. Recovery result

Ready & Set context has been reconstructed from:
- Ready formal REV_07 baseline;
- Drive Current Truth and Whole Implementation Contract;
- preserved Ready/Notion raw conversations;
- current 2026-09-19 conversation delta;
- NotebookLM Pilot 02 source map;
- current TAKY C2S/context rules;
- live Ready GitHub source and CI.

This is a targeted recovery scope, not proof that every historical Ready conversation is accessible. Missing historical ranges remain `UNVERIFIED_SOURCE_COVERAGE`.

## 2. Product definition

Ready & Set is the child's **BASE CAMP / Goal & Session Orchestrator**.

Canonical exploration chain:

`CONFIRMED FACT
→ SUBJECT INTERPRETATION WHEN NEEDED
→ PLANNER ALLOCATION
→ DATED TODAY TODO
→ TODAY'S ISLAND EXPLORATION PIN
→ CHILD SELECTS ONE OR MORE TODOs
→ ONE EXPLORATION SESSION
→ TASK/LAP
→ WRAP-UP
→ EXPLORATION RECORD`

An exploration is not:
- a fixed subject category,
- a timetable row,
- a fabricated challenge,
- an arbitrary timer session.

## 3. Authority

`PARENT = CAPTURE / INPUT / CONFIRM / SUPPORT`  
`LEARNING MASTER / SUBJECT = INTERPRET / LOAD ANALYSIS`  
`PLANNER / MAIN = ALLOCATE`  
`CHILD = VIEW / FACT INPUT WHEN APPLICABLE / SELECT TODAY / EXECUTE`  
`READY = PRESENTATION / EXECUTION / SESSION ORCHESTRATION`

Ready must not absorb Planner or Learning Master authority.

## 4. Planner semantics

Hard:
- `SCHEDULE COMMITMENT ≠ HOMEWORK TEMPLATE ≠ DATED TODO INSTANCE ≠ PROGRESS EVENT`
- `FREE TIME EXISTS ≠ MUST STUDY`
- `CAPACITY ≠ REQUIRED STUDY AMOUNT`
- `PHYSICAL PAGE ≠ LEARNING UNIT`
- `MINUTES ≠ PRIMARY SPLIT UNIT`
- `PLANNED STUDY END ≤ 22:00`
- incomplete work persists
- `DEFERRED → CARRY_OVER → RESCHEDULED`

Talent:
- one weekly package;
- six books are separate book-level facts but one weekly package;
- next Tuesday is a cycle/deadline boundary, not an ordinary extra allocation slot;
- daily division must be activity/load-aware rather than minute/page-first.

English:
- reusable workbook reference;
- actual post-academy range is a new fact;
- child or parent may enter factual range;
- weekday prints/components are independent learning units;
- actual next academy is the deadline boundary;
- missing homework/deadline must not be invented.

## 5. Exploration session

Hard:
- `ONE SESSION / ONE TARGET TIME / MULTIPLE TASKS / ONE ACTIVE TASK / ONE ACTIVE LAP`
- `TASK_CHANGE = LAP_END + NEXT_LAP_START`
- `APP_SWITCH != PAUSE`
- `APP_SWITCH != LAP_END`
- `APP_SWITCH != SESSION_END`
- `SCREEN_LOCK != PAUSE`
- `NETWORK_FAILURE != SESSION_END`
- `SESSION_END != TASK_COMPLETE`

Task outcomes:
`COMPLETED / PARTIAL / DEFERRED / BLOCKED / WAITING_FOR_PARENT`

## 6. Confirmed timer / recording

Timer visual authority:
- yellow focus field;
- `그냥! 지금 하면 돼!`;
- full analog clock;
- task/exploration context;
- remaining/target;
- pause / `완료했어요`;
- BGM;
- conditional REC.

Do not revive:
- Focus Mode as authority;
- Time Attack as whole-product definition;
- old Golden contracts/assets;
- rejected `ready-focus-tools-v1.js`.

Recording:
- same session continues;
- timer continues;
- BGM stops while recording;
- local/browser DSP preferred;
- M4A/AAC only when actually supported;
- original and transfer are separately preserved;
- submitted filename has no clean/original suffix;
- actual iPhone MIME/acoustics/native share remain device-unverified.

## 7. Live implementation state

Ready safe source:
- branch: `taky/exploration-journey-2026-09-18`
- HEAD: `3d96878ada0458196ff8bfc68fdcf7087ea4d1ca`
- PR #4: OPEN / DRAFT / UNMERGED / MERGEABLE
- version: `0.9.4-rc25`
- cache: `ready-set-v094-rev07-staging28-runtime-hardening-v1`
- production/main unchanged.

Five current product regression workflows at this head are SUCCESS.

### Important test limitation
Those green workflows do **not** prove the recovered Exploration Contract, because the current suite does not fail when upstream Planner selection collapses to one task.

## 8. Confirmed implementation gaps

### FAIL — multi-task exploration selection
Current upstream source still collapses selection to a single task:
- `ready-base-native-v2.js`
- `ready-planner-selection-bridge-v1.js`
- `ready-base-runtime-v1.js`

Downstream REV_07 session contract supports multiple tasks, but the entry/runtime bridge supplies only one.

### FAIL — Today's Island exploration-pin entry
Current child UI uses exploration copy and displays Planner tasks, but **Today's Island / exploration pin** is not yet a first-class runtime projection/contract.

### PARTIAL — Stage E authority migration
`ready-stage-e.js` contains both:
- preserved legacy migration/detection concepts such as `NEXT_TUE`;
- newer corrected semantics such as `estimatedMin:null`, `minuteCapacityAuthority:false`, `nextTuesdayNormalSlot:false`.

This must be separated and regression-tested so legacy history detection cannot become active authority.

### PARTIAL — Parent authority
Parent/Child role split and FACT capture semantics exist, but Parent UI/runtime still needs a field-level audit so difficulty/time/allocation authority does not leak back into Parent.

### SOURCE/CI PASS, DEVICE PENDING — timer/session
Timestamp-based restore, duplicate-start lock and continuity logic exist and current regressions are green.

### SOURCE/CI PASS, DEVICE PENDING — recording
Conditional REC, timer continuation, BGM stop/resume, local DSP and original/transfer preservation exist. iPhone behavior remains unverified.

## 9. OPEN / HOLD / CONFLICT

### OPEN_CONFLICT — target time
REV_07 says one target time; current runtime explicitly permits no target. No false convergence. Target time may not fabricate homework quantity or completion.

### HOLD — weekly/daily visual
Structure/direction exists, but final visual lock does not. User liked one composition but said it was visually tiring; weekly still requires review.

### OPEN — iPhone device validation
Do not resume until exploration source/entry/selection gaps are corrected and rebuilt.

### UNVERIFIED_SOURCE_COVERAGE
PILOT_02 is targeted recovery, not all-account-history proof.

## 10. Latest corrections preserved

- Do not use the user as a debugger.
- A main PWA icon must not be mistaken for staging evidence.
- Planner-empty state must not be bypassed by inserting a fake task just to reach the timer.
- "타키 기준" must reconstruct project-specific durable context, not only load global governance.
- NotebookLM/Drive are long-memory/context-recovery layers; TAKY/C2S remains the authority/coverage layer.

## 11. Next implementation order

1. Make this context resolution a mechanical CI gate.
2. Expand Ready exploration tests so single-task collapse fails.
3. Fix Planner multi-select → one session / many tasks.
4. Implement Today's Island exploration pins with stable Planner identity.
5. Audit Parent FACT UI against authority split.
6. Separate Stage E legacy migration/history from active Planner semantics.
7. Rebuild staging preview.
8. Resume actual iPhone/PWA validation.
9. Keep weekly/daily visual design as a separate HOLD.

END
