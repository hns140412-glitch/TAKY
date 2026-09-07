# TAKY Validation Rules — REV_00

## Global gate
SOURCE / APPROVED REFERENCE → IDENTITY & PROTECTED-STATE LOCK → APPLICABLE-RULE EXTRACTION → DECISION-COVERAGE / TRACEABILITY → EXECUTION → ACTUAL RESULT INSPECTION → 1:1 COMPARE → INTEGRATED-RESULT CHECK → DOMAIN CHECK → IMPACT CHECK → REGRESSION CHECK → PASS / FAIL.

FAIL → do not present as completed or canonical.
PASS → may proceed only to the next authorized state.

## Execution Truthfulness — HARD LOCK

TAKY SHALL NOT report an execution state higher than the highest state actually evidenced.

`AGREED ≠ SAVED ≠ CANONICAL WRITTEN ≠ IMPLEMENTED ≠ BUILT ≠ DEPLOYED ≠ RELEASE PASS`

This invariant summarizes the claim ladder; it does not replace the detailed validation gates.

## Rule scope / promotion gate — HARD LOCK

`PROJECT RULE ≠ GLOBAL RULE`

A rule from a DOMAIN / PROJECT / runtime SHALL NOT become GRAND MASTER merely because it is useful, repeated or strict.
Before promotion classify it as:
`GLOBAL INVARIANT / SHARED CAPABILITY CONTRACT / DOMAIN RULE / PROJECT RULE / REFERENCE ONLY / CANDIDATE`.

Lower-layer specialization may be stricter than global evidence semantics but SHALL NOT weaken higher authority.

## Rule activation gate
CANONICAL LOADED ≠ CANONICAL APPLIED.
RULE EXISTS ≠ RULE APPLIED.
RULE MENTIONED ≠ RESULT VALIDATED.

For material work, identify the rules actually applicable to the current task/domain/project and verify the real output against them. Generic UX, engineering, writing, design or implementation practice shall not substitute for a specific active MASTER / GUIDE / DOMAIN / PROJECT rule.

## Integrated-result gate
COMPONENT PASS ≠ INTEGRATED RESULT PASS.
LAYER SEPARATION ≠ COMPOSITION PASS.
NO COLLISION ≠ GOOD RELATIONSHIP.
INTENDED OVERLAP ≠ ACCIDENTAL COLLISION.

When separately produced parts are assembled, inspect the final output for applicable alignment, spacing, anchoring, hierarchy, overlap/collision, clipping, z-order, source/ownership relationships, safe areas/boundaries, state transitions and representative target conditions.

Planned overlap may PASS when intentional and task-supporting. Unplanned overlap, excessive separation, crooked/inconsistent alignment, broken anchoring or alternate-state composition failure = FAIL when it harms the intended relation or usability.

## End-to-end realization / traceability gate — HARD LOCK
A material source decision/requirement shall be traceable forward through every applicable downstream stage and the actual result shall be traceable backward to authoritative source/decision.

Forward pattern:
`SOURCE / CONVERSATION / ATTACHMENT → DECISION → LATEST CORRECTION → CLASSIFICATION → ACTIVE REQUIREMENT → OWNER MASTER → UI/UX CONTRACT → FUNCTION CONTRACT → DATA/STATE → IMPLEMENTATION → TEST/EVIDENCE → ACTUAL RESULT → STATUS`.

Reverse pattern:
`ACTUAL RESULT → TEST/EVIDENCE → IMPLEMENTATION → FUNCTION/DATA/UI CONTRACT → REQUIREMENT → DECISION → SOURCE/LATEST CORRECTION → AUTHORITY`.

Six gates:
- A Conversation / Source Coverage
- B MASTER Integrity
- C MASTER → Design/UI Traceability
- D Design → Function/Data Traceability
- E Implementation → Actual Result Evidence
- F Impact / Regression / Resume

Material gaps block the next dependent stage. A UI-facing requirement without an approved UI/state mapping, an implementation feature without functional/data contract, or a claimed feature without representative actual-result evidence is NOT PASS.

Detect both:
- DOWNSTREAM HOLE = active requirement missing required downstream realization/test/evidence.
- UPSTREAM ORPHAN = design/function/code/test/output with no authoritative requirement/source rationale where required.

When a requirement changes, follow traced dependencies, revalidate affected artifacts and confirm unrelated protected state did not regress.

Operational details are governed by `MASTER/TRACEABILITY_PROTOCOL.md`.

## Artifact / image rule
NAME ≠ VISUAL ID.
REFERENCE IMAGE = VISUAL ID when explicitly approved by the user.
Approved Visual ID must not be regenerated into a different species, face, hair, ears, body, gender impression, signature prop, or identity without explicit approved delta.

For composite images validate every character/object individually and positional mapping. Correct labels with wrong visual identity = FAIL.

## Validation independence
SELF-VALIDATION, CROSS-VALIDATION, IMPACT VALIDATION and REGRESSION VALIDATION are separate gates.

- SELF-VALIDATION: compare result to active contract/rules.
- CROSS-VALIDATION: use an independent evidence path, method, source, representation or validator when material.
- IMPACT VALIDATION: inspect intended and unintended downstream/upstream consequences.
- REGRESSION VALIDATION: compare protected pre-change state to post-change state.

SAME ASSERTION REPEATED ≠ CROSS-VALIDATION.
CHANGE WORKS ≠ IMPACT PASS.
NEW RULE PRESENT ≠ REGRESSION PASS.

## Validation dimensions
- Source coverage
- Authority
- Applicability / active-rule coverage
- Decision disposition / lineage
- End-to-end realization traceability
- Ownership
- Data flow
- Protected decisions / HARD LOCKs
- Identity consistency
- Functional correctness
- Result correctness
- Integrated composition / relationship correctness
- Impact
- Regression
- Omission / duplication / conflict
- Implementation evidence
- Release evidence

## Claim-level gate
LOGIC PASS ≠ SCHEMA PASS ≠ DATA PASS ≠ RUNTIME PASS ≠ INTEGRATION PASS ≠ BUILD PASS ≠ LOCAL PASS ≠ DEPLOY PASS ≠ RELEASE PASS.

A document delta, schema, local save, offline launch/cache, deploy response or relation field proves only its own level. Each higher PASS needs representative evidence at that level. Untested real-device, external-service, synchronization and end-to-end behavior remains UNKNOWN / UNVERIFIED.

## Ambiguity semantics

Research/evidence uncertainty remains `UNKNOWN / UNVERIFIED` when evidence is insufficient.
Release/result uncertainty SHALL NOT PASS; classify it as `NOT PASS / FAIL` according to the applicable gate.

`EVIDENCE AMBIGUITY ≠ RELEASE PASS`

## Structural-integrity gate
When an active normative document uses an END/terminal marker, exactly one authoritative terminal boundary is allowed and normative content after it = FAIL. Validate unique/ordered sections, cross-references, canonical/status/revision metadata, and distinguish historical lineage labels from current governance.

## Connected/offline sync gate — conditional
For projects requiring offline, multi-device, external projection or eventual sync, validate distinct governance authority, runtime authority/event ledger, device replica/outbox and reporting projection.

LOCAL SAVE ≠ REMOTE ACKNOWLEDGEMENT.
OFFLINE-CAPABLE UI ≠ OFFLINE DATA SYNC.
TEMPLATE ID ≠ DATED INSTANCE ID ≠ EVENT ID.
RELATION EXISTS ≠ CORRECT OWNERSHIP / MEANING.

Validate identifiers/idempotency, replay/order, ownership/conflict policy, retry/recovery triggers, visible pending/conflict state, server-side scope authorization, secret non-exposure, connector throttling/failure, reconciliation and representative restart/reconnect/duplicate/out-of-order/multi-device/long-offline tests. Unperformed cases remain UNKNOWN.

## Decision-disposition gate
Every material source-derived item requires a traceable PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED disposition. HOLD needs reason/owner/exit condition; EXCLUDE needs scope rationale; OWNERSHIP_TRANSFER needs a named recoverable destination.

When a user requests first/full-conversation and attachment verification, Handoff/summary coverage alone is insufficient. Recover available original evidence and mark inaccessible raw history UNVERIFIED_SOURCE_COVERAGE rather than claiming impossible completeness.

## Status vocabulary
PASS / FAIL / NOT PASS / UNKNOWN / UNVERIFIED / NOT PERFORMED.
Do not collapse design validation into implementation validation.
Do not claim PASS when material source coverage, end-to-end traceability or reverse-validation remains UNVERIFIED.