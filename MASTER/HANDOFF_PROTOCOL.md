# TAKY LOSSLESS HANDOFF / RESUME PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Role: Operational protocol under TAKY GRAND MASTER for loss-resistant state transfer and verified resume.

## 1. Core Contract

HANDOFF ≠ SUMMARY.
HANDOFF = LOSSLESS RESUME PACKAGE / STATE RECOVERY MAP.
HANDOFF ≠ SOURCE OF TRUTH.
HANDOFF COMPLETE ≠ RESUME VERIFIED.

The purpose of Handoff is to allow a new conversation, agent, session, or runtime to reconstruct the last valid working state without silently losing confirmed decisions, unresolved states, corrections, evidence, protected constraints, or material realization traceability.

Lossless does not require duplicating every source verbatim when the recipient can reliably recover it. When the recipient cannot access a materially required source, recoverability may require a portable full snapshot or reconstructable diff+complete base.

## 2. Mandatory Handoff Blocks

A valid Handoff SHALL contain or explicitly mark UNKNOWN / NOT APPLICABLE for:
1. CANONICAL STATE
2. CURRENT GOAL / SCOPE
3. CONFIRMED / PROTECTED STATE
4. DETAILED ACTIVE DECISIONS
5. USER CORRECTIONS
6. UNRESOLVED STATE
7. SUPERSEDED / REJECTED / EXCLUDED / TRANSFERRED STATE
8. ACTUAL INPUT / EVIDENCE POINTERS
9. LAST VALID WORKING STATE
10. VALIDATION STATE
11. REALIZATION TRACEABILITY STATE
12. OPEN ERRORS / OMISSIONS / CONFLICTS
13. NEXT ACTION / RESUME POINT
14. ROLLBACK / RECOVERY POINTER when applicable

Validation layers such as LOGIC / DESIGN / FUNCTION / BUILD / LOCAL / DEPLOY / RELEASE SHALL NOT be collapsed.

## 3. Source Pointer Contract

A Source Pointer SHOULD include, when available:
`sourceType + repository/workspace + file/path + section/range + revision/commit/version + recoveryPurpose`.

If a decision exists only in transient conversation evidence and has not yet been canonicalized, preserve enough of the decision itself to avoid loss and mark its authority/state accurately.

A pointer that cannot reasonably be recovered is not sufficient evidence of preservation.

`FILENAME ≠ FILE CONTENT EVIDENCE`.
`POINTER EXISTS ≠ POINTER RECOVERABLE`.

### 3.1 Recipient-Recoverable / Portable Source Gate — HARD LOCK

Handoff generation SHALL account for actual or reasonably expected recovery capabilities of the receiving session/agent.

If a materially required source is not expected to be recoverable by the recipient, a pointer alone is insufficient when the source can lawfully and practically be included as a portable snapshot.

Correct pattern:
`RECIPIENT CAPABILITY → SOURCE RECOVERABILITY CHECK → POINTER OR PORTABLE SNAPSHOT → SNAPSHOT VERSION/SHA → CLASSIFICATION → RESUME CHECK`.

For portable snapshots:
- preserve source identity, repository/path, revision/commit and snapshot time when available;
- distinguish snapshot freshness from live-head freshness;
- do not claim a snapshot is current live canonical after transfer unless independently reverified;
- include maximum authorized material source needed for reconstruction when the user requested maximum/full handoff;
- classify evidence as CURRENT / CONFIRMED / HISTORICAL / SUPERSEDED / CONFLICT / HOLD / PROCESS / UNVERIFIED.

`REPOSITORY POINTER + NO RECIPIENT ACCESS ≠ RECOVERABLE HANDOFF`.
`LARGE ZIP ≠ SOURCE COVERAGE PASS`.
`SNAPSHOT VERIFIED ≠ LIVE HEAD VERIFIED`.

### 3.2 Self-Contained Bundle Closure — HARD LOCK

For a claimed `maximum / full / all / 최대 / 전체` handoff where the recipient may not have repository access, the package SHALL include a machine-readable `MANIFEST.json` and pass bundle closure.

Each materially included artifact SHALL record, when applicable:
- `artifact_id`;
- original source/repository/path;
- canonical commit/version or snapshot identity;
- `bundle_path`;
- SHA-256;
- `authority_class`;
- `freshness`;
- `owner`;
- `required_for_resume`.

Hard requirements:
1. every `required_for_resume` artifact physically exists in the bundle;
2. each declared SHA-256 matches the actual included file;
3. each Handoff/manifest artifact pointer resolves to a declared artifact ID;
4. recipient without repository access receives either a full source snapshot or reconstructable diff+complete base for each materially required canonical source;
5. authority/time class is explicit; mixed classes are allowed in one manifest/table only when each item is individually classified;
6. resume simulation covers every materially required canonical owner, rather than relying on a fixed arbitrary number of questions;
7. coverage boundary states what the bundle proves and does not prove.

Reference validator:
`python ENFORCEMENT/handoff_bundle_validator.py <bundle-root>`.

A failed bundle closure is `HANDOFF_LOSS` with reason `BUNDLE_CLOSURE_MISSING`.
Do not invent a parallel failure taxonomy merely to label package structure.

`OFFLINE_RECONSTRUCTION_PASS ≠ LIVE_STATE_CURRENT`.

## 4. Coverage Matrix — HARD GATE

Before Handoff PASS, construct:
`SOURCE ITEM → CLASSIFICATION → HANDOFF LOCATION OR SOURCE POINTER → RECOVERY CHECK → RESULT`.

Every relevant prior item SHALL be classified:
`PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED`.

Failure conditions include:
- relevant source item has neither Handoff representation nor recoverable pointer;
- confirmed state is silently omitted;
- unresolved state is converted into confirmed state;
- superseded candidate is presented as current;
- EXCLUDE / OWNERSHIP_TRANSFER lacks rationale/destination where material;
- current state is replaced by filename/revision inference;
- validation status is upgraded without evidence;
- material realization traceability or blocked stage is lost;
- recipient lacks access to a material pointer and no feasible portable snapshot/recovery path is supplied;
- historical/ideation/conflict evidence is packaged as current confirmed state;
- claimed self-contained maximum/full package fails bundle closure.

Any such condition = HANDOFF FAIL.

## 5. Resume Simulation — HARD GATE

A Handoff is not VERIFIED until a resume simulation succeeds.

Simulation:
1. assume a fresh session with no reliable conversational memory;
2. load Handoff and MANIFEST when applicable;
3. recover latest canonical source when available, or identify exact portable snapshot/live-freshness boundary;
4. follow source pointers and included snapshots;
5. reconstruct confirmed, unresolved, superseded, transferred, implementation, traceability and validation state;
6. compare reconstructed state against source state used to generate the Handoff;
7. rebuild applicable forward/reverse realization links sufficiently to identify current stage and blocked next gate;
8. run omission / conflict / authority / impact / regression checks;
9. for self-contained bundles, ensure each materially required owner has at least one successful reconstruction assertion;
10. PASS only if material state can be resumed without silent behavioral drift.

If canonical/evidence cannot be accessed or recovered, mark RESUME VERIFICATION = UNKNOWN / BLOCKED rather than PASS.

## 6. Resume Boot Contract

`/재개` SHALL use:
`LATEST CANONICAL → HANDOFF → SOURCE POINTER/SNAPSHOT/MANIFEST RECOVERY → ACTUAL EVIDENCE → LAST VALID STATE → TRACEABILITY RECOVERY → COMPARE → CLASSIFY → RESUME`.

Do not execute merely because a Handoff contains a next-action sentence. First verify authority, current state, applicable realization gate and evidence against canonical/source material when available.

## 7. Compression Rule

COMPACT ≠ HANDOFF.
SUMMARY ≠ LOSSLESS HANDOFF.

Compression is allowed only when recoverability is preserved.
Prefer detailed state for behavior-changing decisions; concise pointers only when recovery is viable; portable snapshots when material pointers are not recoverable; explicit state labels for unresolved/superseded/transferred items; stable IDs/pointers for material lineage.

## 8. Regression Fixture Requirement

TAKY SHOULD retain representative real failure cases as Handoff regression fixtures.

Initial fixture: Schedule / Homework Allocation state-transfer failure.

### 8.1 Corrected Current Fixture State

The current Base Timetable is CONFIRMED as the operating baseline. Homework allocation uses the current effective timetable: confirmed baseline plus active overrides/revisions. One-off events create temporary overrides; recurring/quarterly/academy/school changes may revise the baseline and trigger capacity recalculation/homework reallocation. If no schedule delta exists, do not unnecessarily reopen full timetable confirmation.

Operational state model:
`BASE_TIMETABLE_CONFIRMED → TEMP_EVENT_OVERRIDE or SCHEDULE_REVISION → CAPACITY_RECALCULATION → HOMEWORK_REALLOCATION`.

A compliant Handoff preserves the current confirmed baseline, latest corrections, capacity effects, Subject-vs-MAIN ownership, `FREE TIME EXISTS ≠ MUST STUDY`, `CAPACITY ≠ REQUIRED STUDY AMOUNT`, carry-over behavior, and active parent/resource dependencies. Project-specific details remain lower-layer rules and are not promoted into GRAND MASTER by this fixture.

## 9. Handoff Validation Result Schema

HANDOFF VALIDATION
- Canonical reference: PASS / FAIL / UNKNOWN
- Source coverage: PASS / FAIL / UNKNOWN
- Recipient source recoverability: PASS / FAIL / UNKNOWN
- Portable snapshot fidelity: PASS / FAIL / UNKNOWN / NOT APPLICABLE
- Bundle closure: PASS / FAIL / UNKNOWN / NOT APPLICABLE
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

End-to-end realization semantics are governed by `MASTER/TRACEABILITY_PROTOCOL.md`; command meaning preservation by `MASTER/INTENT_EXECUTION_PROTOCOL.md`; mechanical bundle enforcement by `MASTER/ENFORCEMENT_PROTOCOL.md` and `ENFORCEMENT/handoff_bundle_validator.py`.
