# Learning App Family Master — REV_00

> Status: REV_00 / PRE-CONFIRMATION; previously approved shared content preserved
> Historical filename REV_01 is a lineage identifier, not official finalization.
> Date: 2026-09-06
> Scope: Ready & Set / Hide & Seek / Snap & Pop shared world, session, app-routing, Guide and PWA update contracts
> Authority: TAKY / GRAND MASTER > applicable GUIDE / Family Learning OS rules > this shared capability contract > project masters > implementation
> Load OS/GUIDE_FAMILY_LEARNING_OS.md first, and OS/GUIDE_CHARACTER_RELATIONSHIP.md when applicable. No existing Guide authority or project behavior is redefined by this metadata correction.

## 1. PRODUCT FAMILY PRINCIPLE — HARD LOCK

One island, one connected learning journey, three specialist apps.

- Ready & Set = BASE CAMP / Goal & Session Orchestrator
- Hide & Seek = Vocabulary Discovery / Retrieval Specialist
- Snap & Pop = Thought / Expression / Writing / Speaking Specialist
- Guide = existing detailed Guide Master; this document does not redefine persona, tone or detailed behavior.
- Imagination Cloud = shared on-demand thinking/visualization mode governed by Guide.

Shared invariant:

`ONE ISLAND / ONE SESSION / MULTIPLE TASKS / MULTIPLE APPS / ONE LEARNING HISTORY`

## 2. ISLAND ONBOARDING — HARD LOCK

Initial experience:

`ISLAND DISCOVERY → CHILD NAMES ISLAND → STARTING POINT → BUILD BASE CAMP → CHILD NAMES BASE CAMP → RADIO LINK WITH GUIDE → FIRST JOURNEY`

Rules:
- `ISLAND_NAME = CHILD_DEFINED`
- `BASE_CAMP_NAME = CHILD_DEFINED`
- System may suggest names, but direct child naming/speaking is primary.
- BASE CAMP is the functional shared start/return point; its display name may be child-defined.

## 3. SHARED SESSION CONTRACT — HARD LOCK

- `ONE SESSION`
- `ONE TARGET TIME`
- `MULTIPLE TASKS` allowed
- `ONE ACTIVE TASK`
- `ONE ACTIVE LAP`
- `ONE SESSION STATE OWNER = Ready & Set`

Task transition and app transition are different events:

- `TASK_CHANGE = CURRENT_LAP_END + NEXT_LAP_START`
- `APP_SWITCH != PAUSE`
- `APP_SWITCH != LAP_END`
- `APP_SWITCH != SESSION_END`

Specialist apps report task-level events only. They do not complete the entire session.

Common task events:
`TASK_STARTED / TASK_PROGRESS / TASK_COMPLETED / TASK_PARTIAL / TASK_BLOCKED / HELP_NEEDED / RETURN_TO_BASE`

## 4. TIMER CONTRACT — HARD LOCK

Timer must be timestamp-based, not dependent on a foreground 1-second counter.

Authoritative timing state includes at minimum:
`session_id / started_at / paused_duration / active_task_id / active_lap_id / active_app`

Elapsed time derives from timestamps and explicit pause duration.

Backgrounding, lock-screen state, PWA/app switching and specialist-app routing must not silently reset the timer.

## 5. END VS COMPLETE — HARD LOCK

`SESSION_END != TASK_COMPLETE`

A session may end while tasks remain partial, deferred, blocked or waiting for parent help.

Minimum task states:
`COMPLETED / PARTIAL / DEFERRED / BLOCKED / WAITING_FOR_PARENT`

Unfinished work must remain visible and may later become carry-over/rescheduled work.

## 6. VOICE WRAP-UP / RADIO CONTRACT

Radio is the shared world-facing voice connection to the existing Guide.

At session end:
`END REQUEST → AUTO SUMMARY OF KNOWN STATE → ASK ONLY MISSING/AMBIGUOUS ITEMS → CHILD VOICE RESPONSE → STRUCTURE TASK STATES → SESSION END`

Rules:
- Child voice is primary input.
- Guide asks only what is necessary to complete missing state.
- Do not turn wrap-up into a repetitive interview.
- Live conversation is not saved recording by default.

## 7. IMAGINATION CLOUD — SHARED ON-DEMAND MODE

Triggers may include:
- CHILD QUESTION
- CONCEPT CONFUSION
- EXPRESSION STUCK
- VISUALIZATION BENEFIT

Rules:
- Guide decides minimum necessary use; child may directly request it.
- Visuals must explain, not decorate.
- It must not replace the child's answer or authorship.
- Preserve current session/task/lap.
- `IMAGINATION CLOUD MUST RETURN` to the original task.

Per-app use:
- Ready & Set: short understanding support during execution.
- Hide & Seek: word meaning/context/retrieval support.
- Snap & Pop: thought, scene and expression expansion.

## 8. DATA OWNERSHIP — HARD LOCK

Shared Learning Domain owns long-term source/task/session/history meaning.

Apps are projections/capture/execution experiences, not isolated long-term learning silos.

Shared logical chain:
`SOURCE → ASSIGNMENT → GOAL → SESSION → TASK → LAP → RESULT / HELP → LEARNING HISTORY`

App-specific rewards and visuals may differ; learning history remains unified.

## 9. PWA DEPLOYMENT & UPDATE CONTRACT — HARD LOCK

Recommended operating mode:

`GITHUB PUSH → HOST AUTO DEPLOY → APP CHECKS NEW VERSION → DOWNLOAD/PREPARE UPDATE → APPLY ONLY AT SAFE POINT`

Rules:
- Automatic deployment is allowed.
- Update detection is automatic.
- Do not force reload while an active learning session is running.
- If update becomes ready during an active session, mark `UPDATE_READY` and apply after session end/return to safe idle state.
- Preserve session/task/lap state before any reload or activation.
- Cache/version identifiers must be traceable.
- Stale cache must not silently keep an obsolete app forever.
- Icon/name/manifest changes are release-sensitive and should be applied after UI/brand freeze.
- iOS/PWA may retain home-screen icon/name cache; release QA must verify installed-home-screen behavior and document re-add only when platform behavior requires it.

Recommended user-facing behavior:
`UPDATE READY → continue current learning safely → session ends → apply update → restore idle/base camp state`

## 10. ICON / APP NAME RELEASE GATE

After UI and visual direction are approved:
- produce original ultra-high-density illustration master icons for all three apps,
- derive required PWA sizes from the master asset,
- update app name, short name, manifest metadata and Apple touch icon references,
- validate home-screen display, mask/safe zone, legibility and cache behavior on real iPhone/Safari.

Do not repeatedly churn icons/names during active UI exploration.

## 11. PROJECT BOUNDARIES

Ready & Set owns orchestration/session state.
Hide & Seek owns vocabulary task experience/results.
Snap & Pop owns thought/expression experience/results and its original gem/wish/blessing growth world.
Guide owns detailed guidance/persona logic.
Learning Domain owns long-term learning interpretation/history.

### 11.1 PROJECT OWNER POINTER REGISTRY — HARD RECOVERY ROUTE

Shared-family compaction SHALL NOT be used as a substitute for the current detailed project owner.
Before declaring a project detail missing, recover the applicable active/inherited project MASTER and reverify its repository/branch HEAD.

Current recoverable owner routes:
- Ready & Set → `hns140412-glitch/Ready-Set` → `READY_SET_CANONICAL_PRODUCT_CONTRACT.md` + `READY_SET_RUNTIME_STATE_MODEL.md`; historical REV_06/REV_07 material is lineage only unless explicitly preserved by the active rewrite canonical.
- Hide & Seek → `hns140412-glitch/Hide-Seek` → `Hide_Seek_UI_MASTER_LOGIC_REV_04.md`.
- Snap & Pop → `hns140412-glitch/Snap-Pop` → `Snap_Pop_UI_MASTER_LOGIC_REV_12.md`, which preserves/inherits applicable REV_11/REV_10 detail unless explicitly superseded.

Rules:
- Reverify the actual active branch/HEAD before current implementation or release claims; a historical Handoff SHA is not sufficient.
- `CENTRAL SUMMARY OMISSION ≠ PROJECT RULE ABSENCE`.
- `HANDOFF POINTER ≠ PROJECT AUTHORITY`.
- A project rule confirmed in an inherited active MASTER SHALL NOT be downgraded to `RECOVERY_REQUIRED` merely because it is absent from this shared file.
- Conversely, historical detail outside the active/inherited project owner SHALL NOT be promoted merely because it appears in a recovery summary.

Snap & Pop Family Expansion remains project-owned. Recover its active inherited project lineage before judging details such as Original/Core separation, family letters/notes, multiple child profiles, child-specific isolation, family special exploration, diary/illustration/share or related optional surfaces. Shared-family governance preserves the boundary; it does not automatically activate every expansion feature.

Ready project-specific Main Guide + Random Guest behavior remains Ready-owned. `SPECIAL FRIEND` remains a separate GUIDE recovery concept unless direct source evidence establishes equivalence.

## 11.2 SHARED GROWTH BACKLOG INHERITANCE — HARD LOCK

The family SHALL consume applicable unresolved shared engineering gaps from:
`MASTER/LEARNING_APP_FAMILY_GROWTH_BACKLOG.json`.

This support registry is not proof of implementation. It preserves centrally discovered deficiencies, improvement direction and exit conditions so project development does not lose them.

Before material implementation/release work in Ready & Set, Hide & Seek or Snap & Pop:
1. load applicable OPEN/PARTIAL family growth items;
2. map each material item to the project implementation/milestone, or mark NOT_APPLICABLE/HOLD with reason;
3. implement against the current project MASTER rather than replacing project authority;
4. update evidence only when the stated exit conditions are actually met;
5. preserve newer evidence that supersedes an older growth item.

Current shared high-priority gap families include:
- safe-point PWA/service-worker update atomicity;
- unified app/SW/data-schema/contract version compatibility;
- version-aware local-first conflict/reconciliation;
- state snapshot vs immutable event/history separation;
- cross-app registry and contract handshake;
- external side-effect/deploy budget;
- outcome/learning feedback evidence.

`FAMILY BACKLOG ITEM != PROJECT IMPLEMENTATION`.
`PROJECT IMPLEMENTATION WITHOUT APPLICABLE GAP REVIEW = REVIEW_REQUIRED` when a material OPEN/PARTIAL item applies.

## 11A. PRODUCT IMPLEMENTATION INTEGRITY — HARD LOCK

Ready & Set, Hide & Seek and Snap & Pop SHALL apply `MASTER/PRODUCT_IMPLEMENTATION_INTEGRITY_PROTOCOL.md` to material implementation/progress claims.

Family-wide rules:
- core/domain contracts, C2S closure, test count and CI success do not directly equal product completion;
- each app keeps a product-completion matrix against its actual user-facing requirement inventory;
- structural integrity, representative input, UI/UX realization, current integration path, runtime and device evidence remain separate;
- if architecture is a material cause of unsafe growth or validation/product divergence, feature growth pauses for explicit REPAIR / REFACTOR / REWRITE-REBUILD disposition;
- reusable family/shared assets remain reusable-asset maturity and SHALL NOT be averaged into a rewrite target's implementation percentage;
- historical deployed URLs or stale production paths SHALL NOT prove current family integration.

This gate applies symmetrically to all three apps; it is not a Hide-only exception.

## 12. REGRESSION GATE

A release fails if any of the following occur:
- app switch pauses/resets a session without explicit pause,
- app switch closes a lap,
- specialist app completes the whole session,
- session end marks all tasks complete,
- update reload interrupts active work,
- different apps create conflicting long-term learning records,
- Guide redefinition conflicts with existing Guide Master,
- Imagination Cloud becomes decorative or answer-generating,
- child-defined island/base-camp names are lost after update.

END — LEARNING APP FAMILY MASTER REV_00
