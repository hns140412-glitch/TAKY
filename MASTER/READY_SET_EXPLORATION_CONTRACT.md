# READY & SET EXPLORATION CONTRACT — 2026-09-19 RECOVERY

> Status: RECOVERED CANONICAL CONTRACT / IMPLEMENTATION GAP REVIEW REQUIRED
> Scope: Ready & Set child-facing exploration semantics
> Purpose: restore the user's previously decided exploration criteria as a first-class contract instead of scattered UI copy.

## 0. Governing principle

Ready & Set is the child's **BASE CAMP / Goal & Session Orchestrator**.

An **exploration is not a fixed subject card, a fake challenge, a timetable row, or an arbitrary timer session.**

An exploration is the child-facing execution projection of actual Planner-authoritative dated work:

`CONFIRMED SCHEDULE/ASSIGNMENT FACT
→ SUBJECT INTERPRETATION WHEN NEEDED
→ PLANNER ALLOCATION
→ DATED TODAY TODO INSTANCE
→ TODAY'S ISLAND EXPLORATION PIN
→ CHILD SELECTS ONE OR MORE TODAY TODOs
→ ONE EXPLORATION SESSION
→ TASK/LAP EXECUTION
→ WRAP-UP
→ EXPLORATION RECORD`

## 1. User-facing exploration vocabulary — HARD LOCK

Use the exploration family in child-facing UI:
- 탐험
- 오늘의 섬
- 탐험 핀
- 탐험대
- 길잡이
- 탐험 시작 / 탐험 진행 / 탐험 완료
- 탐험 기록

Do not revive user-facing:
- 작전
- 타임어택
- 출동
- 미션
- 작전 보고서

Internal code identifiers may remain for compatibility, but must not leak into child-facing copy.

## 2. Exploration source authority — HARD LOCK

`SCHEDULE COMMITMENT ≠ HOMEWORK TEMPLATE ≠ DATED TODO INSTANCE ≠ PROGRESS EVENT`

A fixed timetable row does not automatically become an exploration.

Authority split:
- PARENT = capture / input / confirm / support
- SUBJECT / LEARNING MASTER = interpret assignment/load where needed
- PLANNER / MAIN = allocate dated work
- CHILD = view actual today TODOs / select / execute
- READY & SET HOME = presentation + session orchestration only

No fixed subject category, decorative card, or fake task may be substituted for a missing Planner TODO.

## 3. Child entry criterion — HARD LOCK

The corrected child entry is the actual **Today's Island / 오늘의 섬 탐험 핀**.

Expected flow:
`아이 모드 홈
→ 오늘의 섬
→ Planner가 만든 실제 오늘 할 일 탐험 핀 표시
→ 아이가 탐험할 TODO 선택
→ 탐험 준비
→ 탐험 시작`

Do not use a hidden legacy “숙제 시작” path as the canonical entry.

If Planner has no dated TODO for today, the UI must truthfully show that there is no Planner-created exploration available. It must not fabricate one.

## 4. Exploration selection — HARD LOCK

A single exploration session may contain **one or more** actual Planner today TODOs.

Required invariant:
`ONE SESSION / ONE TARGET TIME / MULTIPLE TASKS / ONE ACTIVE TASK / ONE ACTIVE LAP`

One selected TODO is a valid special case; selection logic must not collapse the model to single-task-only.

Each selected Planner TODO retains its own stable identity and outcome.

## 5. Target-time relationship — CONFLICT REQUIRES CLOSURE

Known sources currently disagree in wording:
- REV_07 formal baseline states `SET ONE TARGET TIME` and `ONE TARGET TIME`.
- current runtime/UI exposes the focus timer as optional and records `targetMs = null` when unset.

No false convergence is allowed.

Until an explicit authority correction is recovered or approved:
- target time MUST NOT determine homework quantity or task completion;
- task completion remains evidence/state-based;
- implementation must not invent a target value;
- final required-vs-optional semantics remain OPEN_CONFLICT.

## 6. Session and task/lap semantics — HARD LOCK

- Ready & Set owns authoritative session/timestamp state.
- `TASK_CHANGE = LAP_END + NEXT_LAP_START`
- `APP_SWITCH != PAUSE`
- `APP_SWITCH != LAP_END`
- `APP_SWITCH != SESSION_END`
- `SCREEN_LOCK != PAUSE`
- `NETWORK_FAILURE != SESSION_END`
- duplicate start must not create/reset an active session.

Only one task/lap is active at a time even when the exploration contains multiple tasks.

## 7. Specialist routing — HARD LOCK

Within the same exploration session:
- vocabulary discovery/retrieval → Hide & Seek
- idea/thought/writing/speaking/expression → Snap & Pop
- general execution/problem work → Ready & Set

Routing preserves:
`session_id / goal_id / task_id / lap_id / target_time / timing state / return_target`

Specialist routing does not create a new exploration session.

## 8. Recording — HARD LOCK

Recording is **conditional**, never a permanent default control.

Show/suggest REC only for a task that actually requires recording/speaking.

For a recording task:
- same active learning session continues;
- timer continues;
- BGM stops while recording;
- return restores the same task/lap context.

## 9. Exploration end vs task completion — HARD LOCK

`SESSION_END != TASK_COMPLETE`

Valid task outcomes:
- COMPLETED
- PARTIAL
- DEFERRED
- BLOCKED
- WAITING_FOR_PARENT

Ending an exploration must never bulk-complete unfinished tasks.

Target-time attainment does not by itself mean task completion.

## 10. Carry-over and replanning — HARD LOCK

Incomplete work never disappears.

`DEFERRED → CARRY_OVER → RESCHEDULED`

Only genuinely completed identities suppress future candidates.
Do not duplicate same-day TODO instances.

## 11. Exploration record and sharing — HARD LOCK

Exploration history/report must preserve actual state and timing only.

No fabricated:
- completion percentage
- XP
- streak
- target quantity
- success state

Share content derives from the persisted report and does not mutate Planner/session state.

Child-facing share language is not fixed boilerplate. The Explorer-team / Guide interprets the actual situation in a supportive, non-evaluative way.

## 12. Guide / Explorer-team role — HARD LOCK

Guide is the child's companion/guide, not a parent proxy and not an evaluator.

Default concept:
- “나의 탐험대”
- guide example currently used: 루미
- companion tone: “오늘도 같이 가볼까?”

Guide may:
- transition between steps,
- ask only necessary clarification,
- support retry/recovery,
- help interpret the exploration record.

Guide must not shame, blame, score, or repeatedly interview the child.

## 13. Growth/experience record — PRESERVE

Experience records are not only for “잘함”.

Preserve meaningful:
- mistake
- correction
- recovery
- special behavior
- help needed
- successful persistence

“성장 씨앗 / 다음 탐험” may use these as improvement context without converting them into blame or fabricated scoring.

## 14. Known implementation gaps — 2026-09-19

### GAP-A — MULTI-TASK COLLAPSED TO SINGLE TASK — FAIL
Current:
- `ready-base-native-v2.js::chooseTask()` rewrites every other task `selected:false`.
- `ready-planner-selection-bridge-v1.js::bindPlannerTask()` does the same.
- `ready-base-runtime-v1.js` resolves one selected Planner task and starts `tasks:[label]`.

Impact:
- violates `MULTIPLE TASKS`.
- downstream REV_07 contract supports multiple tasks but upstream never supplies them.

Required correction:
- selection must preserve a set of selected Planner TODO identities.
- session start must bind all selected TODOs into the same exploration contract.
- only one becomes active task/lap at any moment.

### GAP-B — TODAY'S ISLAND ENTRY NOT FIRST-CLASS — FAIL
Current child home copy says “오늘 탐험 정하기” and renders Planner tasks, but the recovered **오늘의 섬 탐험 핀** entry criterion is not implemented as a first-class contract/state.

Impact:
- entry semantics can drift back toward generic task/mission UI.

Required correction:
- model/render today TODOs as Today's Island exploration pins.
- preserve Planner identity/provenance.

### GAP-C — EXPLORATION CONTRACT WAS SCATTERED — FAIL
Current REV_07 strongly defines session mechanics but does not consolidate the full child-facing exploration source/entry/selection/record contract.

Required correction:
- this document becomes the recovered exploration reference in TAKY.
- Ready project baseline must later adopt it explicitly rather than re-inventing semantics.

### GAP-D — TARGET TIME REQUIRED VS OPTIONAL — OPEN_CONFLICT
Do not silently choose one interpretation.
Resolve against source chronology/explicit user authority before final runtime lock.

## 15. Validation gate

A Ready & Set build cannot claim EXPLORATION CONTRACT PASS unless all are true:

1. actual Planner today TODOs are the source;
2. Today's Island exploration entry is visible and truthful;
3. no fake/fixed category is substituted for missing Planner data;
4. one or more TODOs may be selected;
5. one session binds the selected TODO set;
6. only one task/lap is active at a time;
7. app routing preserves session/task/lap;
8. recording is conditional;
9. session end does not bulk-complete tasks;
10. outcomes remain truthful;
11. incomplete work carries over;
12. report/share derives from persisted truth;
13. child-facing terminology remains in the exploration vocabulary;
14. unresolved target-time semantics are not falsely marked resolved.

## 16. Immediate execution consequence

Do **not** create a fake staging TODO merely to unblock device testing before GAP-A/B are corrected.

Testing the timer through a fabricated seed would validate a bypass, not the user's exploration flow.

Correct order:
`RECOVER CONTRACT
→ FIX EXPLORATION ENTRY/SELECTION
→ AUTOMATED CONTRACT TESTS
→ REBUILD STAGING PREVIEW
→ DEVICE VALIDATION`

END
