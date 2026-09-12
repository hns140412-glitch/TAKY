# TAKY LOSSLESS HANDOFF / RESUME PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Role: Operational protocol under TAKY GRAND MASTER for loss-resistant state transfer and verified resume.

## 1. Core Contract

HANDOFF ≠ SUMMARY.
HANDOFF = LOSSLESS RESUME PACKAGE / STATE RECOVERY MAP.
HANDOFF ≠ SOURCE OF TRUTH.
HANDOFF COMPLETE ≠ RESUME VERIFIED.

The purpose of Handoff is not maximum compression. Its purpose is to allow a new conversation, agent, session, or runtime to reconstruct the last valid working state without silently losing confirmed decisions, unresolved states, corrections, evidence, protected constraints, or material realization traceability.

Lossless does not require duplicating every source verbatim. It requires sufficient preserved state plus exact recoverable source pointers so that the intended working state can be reconstructed and compared.

## 2. Mandatory Handoff Blocks

A valid Handoff SHALL contain or explicitly mark UNKNOWN / NOT APPLICABLE for:

1. CANONICAL STATE
   - canonical repository / source
   - relevant MASTER / PROJECT / OS paths
   - revision/status
   - commit/snapshot when available

2. CURRENT GOAL / SCOPE
   - what is being done
   - what is explicitly outside the current scope

3. CONFIRMED / PROTECTED STATE
   - user-confirmed decisions
   - HARD LOCKs
   - approved terminology / architecture / behavior

4. DETAILED ACTIVE DECISIONS
   - implementation-relevant detail needed to resume correctly
   - do not compress details that change behavior

5. USER CORRECTIONS
   - later corrections override earlier assumptions only when evidence supports that relationship

6. UNRESOLVED STATE
   - HOLD
   - CONFLICT
   - MISSING
   - UNKNOWN
   - UNVERIFIED
   - pending approval

7. SUPERSEDED / REJECTED / EXCLUDED / TRANSFERRED STATE
   - prior candidates that must not be mistaken for current decisions
   - rejected/excluded rationale when material
   - ownership-transfer destination when retained elsewhere
   - reason / replacement pointer when known

8. ACTUAL INPUT / EVIDENCE POINTERS
   - source file / path / section / artifact / commit / conversation evidence sufficient for recovery

9. LAST VALID WORKING STATE
   - last known valid implementation/design/data state
   - known regressions after that state

10. VALIDATION STATE
   - PASS / FAIL / UNKNOWN separated by validation layer
   - LOGIC / DESIGN / FUNCTION / BUILD / LOCAL / DEPLOY / RELEASE shall not be collapsed

11. REALIZATION TRACEABILITY STATE
   - material requirement/decision IDs when they exist
   - current owner MASTER / PROJECT
   - applicable UI / function / data / implementation / test / evidence links
   - known downstream holes / upstream orphans
   - stage currently reached and next blocked gate

12. OPEN ERRORS / OMISSIONS / CONFLICTS

13. NEXT ACTION / RESUME POINT
   - exact next checkpoint
   - prerequisites
   - actions that SHALL NOT be started yet

14. ROLLBACK / RECOVERY POINTER
   - when modification or migration occurred

## 3. Source Pointer Contract

A Source Pointer SHOULD include, when available:

sourceType + repository/workspace + file/path + section/range + revision/commit/version + recoveryPurpose

If a decision exists only in transient conversation evidence and has not yet been canonicalized, the Handoff SHALL preserve enough of the decision itself to avoid loss and SHALL mark its authority/state accurately.

A pointer that cannot reasonably be recovered is not sufficient evidence of preservation.

FILENAME ≠ FILE CONTENT EVIDENCE.
POINTER EXISTS ≠ POINTER RECOVERABLE.

### 3.1 Recipient-Recoverable / Portable Source Gate — HARD LOCK

Handoff generation SHALL account for the actual or reasonably expected recovery capabilities of the receiving session/agent.

If a materially required canonical/project/evidence source is not expected to be recoverable by the recipient through available repository/app/network access, a pointer alone is insufficient when the source can lawfully and practically be included as a portable snapshot.

Correct pattern:
`RECIPIENT CAPABILITY → SOURCE RECOVERABILITY CHECK → POINTER OR PORTABLE SNAPSHOT → SNAPSHOT VERSION/SHA → CLASSIFICATION → RESUME CHECK`.

For portable snapshots:
- preserve source identity, repository/path, revision/commit and snapshot time when available;
- distinguish snapshot freshness from live-head freshness;
- do not claim the snapshot is the current live canonical after transfer unless independently reverified;
- include the maximum authorized material source needed for reconstruction when the user requested maximum/full handoff;
- classify evidence as CURRENT / CONFIRMED / HISTORICAL / SUPERSEDED / CONFLICT / HOLD / UNVERIFIED rather than mixing all files as equivalent evidence.

`REPOSITORY POINTER + NO RECIPIENT ACCESS ≠ RECOVERABLE HANDOFF`.
`LARGE ZIP ≠ SOURCE COVERAGE PASS`.
`SNAPSHOT VERIFIED ≠ LIVE HEAD VERIFIED`.

When live verification is impossible but a portable source snapshot exists, the recipient may validate the snapshot contents while separately marking current-live-head freshness as `UNVERIFIED`. This is preferable to discarding or shrinking the recoverable artifact.

## 4. Coverage Matrix — HARD GATE

Before Handoff PASS, construct a coverage relationship:

SOURCE ITEM → CLASSIFICATION → HANDOFF LOCATION OR SOURCE POINTER → RECOVERY CHECK → RESULT

Every relevant prior item SHALL be classified:
PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED.

Failure conditions:
- relevant source item has neither Handoff representation nor recoverable pointer
- confirmed state is silently omitted
- unresolved state is converted into confirmed state
- superseded candidate is presented as current
- EXCLUDE / OWNERSHIP_TRANSFER is used without rationale/destination where material
- current state is replaced by filename/revision inference
- validation status is upgraded without evidence
- material realization traceability or blocked stage is silently lost
- recipient lacks access to a material pointer and no feasible portable snapshot/recovery path is supplied
- historical/ideation/conflict evidence is packaged as if it were current confirmed state

Any such condition = HANDOFF FAIL.

## 5. Resume Simulation — HARD GATE

A Handoff is not VERIFIED until a resume simulation succeeds.

Simulation:
1. Assume a fresh conversation/session with no reliable conversational memory.
2. Load Handoff.
3. Recover latest canonical source when available, or identify the exact portable snapshot/live-freshness boundary.
4. Follow relevant Source Pointers and included snapshots.
5. Reconstruct confirmed, unresolved, superseded, transferred, implementation, traceability and validation state.
6. Compare reconstructed state against the source state used to generate the Handoff.
7. Rebuild applicable forward/reverse realization links sufficiently to identify current stage, holes/orphans and blocked next gate.
8. Run omission / conflict / authority / impact / regression checks.
9. PASS only if material state can be resumed without silent behavioral drift.

If canonical or evidence cannot be accessed or recovered, mark RESUME VERIFICATION = UNKNOWN / BLOCKED rather than PASS.

## 6. Resume Boot Contract

/재개 SHALL use:
LATEST CANONICAL → HANDOFF → SOURCE POINTER/SNAPSHOT RECOVERY → ACTUAL EVIDENCE → LAST VALID STATE → TRACEABILITY RECOVERY → COMPARE → CLASSIFY → RESUME

Do not execute implementation merely because a Handoff contains a next-action sentence. First verify authority, current state, applicable realization gate and evidence against canonical/source material when available.

## 7. Compression Rule

COMPACT ≠ HANDOFF.
SUMMARY ≠ LOSSLESS HANDOFF.

Compression is allowed only when recoverability is preserved.

Prefer:
- detailed state for behavior-changing decisions
- concise pointers for stable canonical material only when recipient recovery is viable
- portable snapshots when material pointers are not recoverable by the recipient and inclusion is feasible/authorized
- explicit state labels for unresolved/superseded/transferred items
- stable IDs/pointers for material requirement-to-result lineage

Do not optimize Handoff for shortness at the expense of recoverability.

## 8. Regression Fixture Requirement

TAKY SHOULD retain representative real failure cases as Handoff regression fixtures.

Initial fixture: Schedule / Homework Allocation state-transfer failure.

### 8.1 Corrected Current Fixture State

The earlier fixture wording incorrectly preserved an older project stage as if it were current. The latest user correction is authoritative for the fixture state:

- The current Base Timetable is CONFIRMED as the operating baseline.
- Homework allocation SHALL use that confirmed timetable as its baseline capacity map.
- The baseline is maintained, not treated as permanently immutable.
- One-off events create temporary schedule overrides.
- Quarterly changes, academy day/time changes, school schedule changes, or other recurring schedule changes may revise the baseline.
- After a relevant change, affected capacity SHALL be recalculated and homework SHALL be reallocated as needed.
- If no schedule delta exists, the confirmed Base Timetable remains in force; do not unnecessarily reopen full timetable confirmation.

Operational state model:

BASE_TIMETABLE_CONFIRMED
→ TEMP_EVENT_OVERRIDE when a one-off event occurs
→ SCHEDULE_REVISION when recurring/quarterly/academy schedule changes
→ CAPACITY_RECALCULATION
→ HOMEWORK_REALLOCATION

A compliant Handoff for this fixture must preserve at minimum:
- current Base Timetable = confirmed operating baseline.
- SCHEDULE FIRST, ASSIGNMENT SECOND means allocation uses the current effective timetable: confirmed baseline plus active overrides/revisions.
- prior pre-confirmation timetable state is historical / SUPERSEDED and must not be restored as current.
- obsolete candidate timetable ≠ current confirmed baseline.
- fixed academy/school/life schedule and travel/buffer affect capacity.
- event-based and recurring schedule changes may alter capacity and trigger reallocation.
- Subject interprets; MAIN allocates.
- FREE TIME EXISTS ≠ MUST STUDY.
- CAPACITY ≠ REQUIRED STUDY AMOUNT.
- PLANNED STUDY END ≤ 22:00 is a planning boundary, not proof of forced termination.
- incomplete work becomes Carry-over rather than silent deletion/failure.
- planned-vs-actual duration/history may inform later allocation.
- parent checking / correction flow and other resource dependencies must not disappear if active in the source state.

Regression failure examples:
- asking to reconfirm the whole timetable solely because an older Handoff said it was unconfirmed.
- allocating homework against an obsolete timetable while a newer confirmed baseline exists.
- ignoring a supplied event/quarterly/academy schedule delta.
- treating a temporary event override as a permanent baseline revision without evidence.
- treating baseline confirmation as meaning the timetable can never change.

This fixture validates state-transfer behavior; it does not itself promote project-specific schedule details into GRAND MASTER CORE.

## 9. Handoff Validation Result Schema

HANDOFF VALIDATION
- Canonical reference: PASS / FAIL / UNKNOWN
- Source coverage: PASS / FAIL / UNKNOWN
- Recipient source recoverability: PASS / FAIL / UNKNOWN
- Portable snapshot fidelity: PASS / FAIL / UNKNOWN / NOT APPLICABLE
- Live-head freshness: PASS / FAIL / UNKNOWN
- Evidence classification accuracy: PASS / FAIL / UNKNOWN
- Protected decisions: PASS / FAIL / UNKNOWN
- User corrections: PASS / FAIL / UNKNOWN
- HOLD/CONFLICT preservation: PASS / FAIL / UNKNOWN
- Superseded/rejected/excluded/transferred-state separation: PASS / FAIL / UNKNOWN
- Source pointer recoverability: PASS / FAIL / UNKNOWN
- Last-valid-state recovery: PASS / FAIL / UNKNOWN
- Realization traceability recovery: PASS / FAIL / UNKNOWN
- Validation-state accuracy: PASS / FAIL / UNKNOWN
- Next-action accuracy: PASS / FAIL / UNKNOWN
- Resume simulation: PASS / FAIL / UNKNOWN
- Regression fixture: PASS / FAIL / UNKNOWN

OVERALL HANDOFF PASS requires all materially applicable gates to PASS. A package may be usable with live-head freshness UNKNOWN only if that limitation is explicitly isolated and the portable snapshot is sufficient for the claimed resume scope; it SHALL NOT be labeled live-current.

## 10. Boundary

This protocol governs state transfer and recovery quality. It does not make Handoff canonical authority and does not absorb project/domain rules into GRAND MASTER.

Project-specific detailed schedules, app behavior, business data and artifacts remain owned by their proper lower master/source. The Handoff preserves or points to them; it does not redefine their authority.

End-to-end realization semantics are governed by `MASTER/TRACEABILITY_PROTOCOL.md`; Handoff preserves enough of that state to resume correctly.

Command meaning preservation and maximum feasible execution are governed by `MASTER/INTENT_EXECUTION_PROTOCOL.md`.
