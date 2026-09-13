# TAKY Validation Rules — REV_00

Role: validation-composition and claim-level gate layer.
Rule ownership registry: `MASTER/RULE_REGISTRY.json`.

## Semantic ownership boundary — HARD LOCK

`VALIDATION COMPOSITION ≠ SECOND SEMANTIC OWNER`.

This file defines when/how validation gates are composed. It SHALL NOT redefine failure taxonomy, recovery semantics, intent/result semantics, Handoff portability semantics, or external-reference authority semantics already owned elsewhere.

Normative owners:
- failure/discrepancy token semantics → `MASTER/FAILURE_TAXONOMY.md`
- intent/result execution fidelity → `MASTER/INTENT_EXECUTION_PROTOCOL.md`
- recovery/negative-existence/user-QA exhaustion → `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`
- Handoff portability/resume/bundle closure → `MASTER/HANDOFF_PROTOCOL.md`
- executable/auditable gates/replay → `MASTER/ENFORCEMENT_PROTOCOL.md`
- workspace/reference authority boundary → `MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md`
- machine-readable owner registry → `MASTER/RULE_REGISTRY.json`

If explanatory wording here conflicts with a declared semantic owner, the owner controls.

## Global gate

`SOURCE / APPROVED REFERENCE → IDENTITY & PROTECTED-STATE LOCK → APPLICABLE-RULE EXTRACTION → DECISION-COVERAGE / TRACEABILITY → EXECUTION → ACTUAL RESULT INSPECTION → 1:1 COMPARE → INTEGRATED-RESULT CHECK → DOMAIN CHECK → IMPACT CHECK → REGRESSION CHECK → ENFORCEMENT GATE → PASS / FAIL`.

FAIL → do not present as completed or canonical.
PASS → may proceed only to the next authorized state.

## Execution Truthfulness — HARD LOCK

TAKY SHALL NOT report an execution state higher than the highest state actually evidenced.

`AGREED ≠ SAVED ≠ CANONICAL WRITTEN ≠ IMPLEMENTED ≠ BUILT ≠ DEPLOYED ≠ RELEASE PASS`.

This invariant summarizes the claim ladder; it does not replace detailed gates.

## Rule scope / promotion gate — HARD LOCK

`PROJECT RULE ≠ GLOBAL RULE`.

A rule from DOMAIN / PROJECT / runtime / external reference SHALL NOT become GRAND MASTER merely because it is useful, repeated, strict, popular, or AI-recommended.
Before promotion classify it as:
`GLOBAL INVARIANT / SHARED CAPABILITY CONTRACT / DOMAIN RULE / PROJECT RULE / REFERENCE ONLY / CANDIDATE`.

Lower-layer specialization may be stricter than global evidence semantics but SHALL NOT weaken higher authority.
Reference-only/external promotion also follows `MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md` and `MASTER/ENFORCEMENT_PROTOCOL.md`.

## Rule activation gate

CANONICAL LOADED ≠ CANONICAL APPLIED.
RULE EXISTS ≠ RULE APPLIED.
RULE MENTIONED ≠ RESULT VALIDATED.

For material work, identify rules actually applicable to the current task/domain/project and verify the real output against them. Generic practice SHALL NOT substitute for an active MASTER / GUIDE / DOMAIN / PROJECT rule.

## Enforcement / continual-harness activation

`RULE WRITTEN ≠ RULE ENFORCED`.
`RULE MENTIONED ≠ ENFORCEMENT`.
`LESSON RECORDED ≠ RECURRENCE PREVENTED`.

All executable/auditable enforcement semantics are owned by `MASTER/ENFORCEMENT_PROTOCOL.md`.
When a material correction/failure recurrence is mechanically checkable or replayable, run the applicable deterministic validator/replay/equivalent gate before recurrence-prevention PASS.

History/rollback SHALL preserve prior rule state, failure evidence, enforcement delta and validation result. Human approval remains separate when the owning policy requires it.

## Negative-existence / recovery activation

`SEARCH MISS ≠ SOURCE ABSENCE`.
`RECOVERY FAILURE ≠ USER NEVER SAID`.
`SUMMARY / HANDOFF / MASTER ABSENCE ≠ PRIOR DECISION ABSENCE`.

Before material negative-existence claims or before asking the user to recover evidence/debug a materially recoverable issue, apply `MASTER/RECOVERY_FORENSICS_PROTOCOL.md` and `MASTER/ENFORCEMENT_PROTOCOL.md`.

Outcome token meanings come only from `MASTER/FAILURE_TAXONOMY.md`; this file does not redeclare them.

## Handoff / portability activation

When maximum/full/self-contained Handoff is requested, apply `MASTER/HANDOFF_PROTOCOL.md` plus `MASTER/ENFORCEMENT_PROTOCOL.md`.
A generated package is not portable merely because it contains many files or checksums. Actual bundle closure, manifest resolution, required file/hash integrity and resume simulation are required when applicable.

`OFFLINE_RECONSTRUCTION_PASS ≠ LIVE_STATE_CURRENT`.

## Integrated-result gate

COMPONENT PASS ≠ INTEGRATED RESULT PASS.
LAYER SEPARATION ≠ COMPOSITION PASS.
NO COLLISION ≠ GOOD RELATIONSHIP.
INTENDED OVERLAP ≠ ACCIDENTAL COLLISION.

When separately produced parts are assembled, inspect final output for applicable alignment, spacing, anchoring, hierarchy, overlap/collision, clipping, z-order, source/ownership relationships, safe areas/boundaries, state transitions and representative target conditions.

Planned overlap may PASS when intentional and task-supporting. Unplanned overlap, excessive separation, broken alignment/anchoring or alternate-state composition failure = FAIL when it harms intended relation/usability.

## End-to-end realization / traceability gate — HARD LOCK

A material source decision/requirement shall be traceable forward through every applicable downstream stage and the actual result shall be traceable backward to authoritative source/decision.

Forward:
`SOURCE / CONVERSATION / ATTACHMENT → DECISION → LATEST CORRECTION → CLASSIFICATION → ACTIVE REQUIREMENT → OWNER MASTER → UI/UX CONTRACT → FUNCTION CONTRACT → DATA/STATE → IMPLEMENTATION → TEST/EVIDENCE → ACTUAL RESULT → STATUS`.

Reverse:
`ACTUAL RESULT → TEST/EVIDENCE → IMPLEMENTATION → FUNCTION/DATA/UI CONTRACT → REQUIREMENT → DECISION → SOURCE/LATEST CORRECTION → AUTHORITY`.

Six gates:
- A Conversation / Source Coverage
- B MASTER Integrity
- C MASTER → Design/UI Traceability
- D Design → Function/Data Traceability
- E Implementation → Actual Result Evidence
- F Impact / Regression / Resume

Material gaps block the next dependent stage.
Detect both:
- DOWNSTREAM HOLE = active requirement missing required downstream realization/test/evidence.
- UPSTREAM ORPHAN = design/function/code/test/output with no authoritative requirement/source rationale where required.

Operational details are governed by `MASTER/TRACEABILITY_PROTOCOL.md`.

## Artifact / image rule

NAME ≠ VISUAL ID.
REFERENCE IMAGE = VISUAL ID when explicitly approved by the user.
Approved Visual ID must not be regenerated into materially different identity without explicit approved delta.
For composite images validate every character/object and positional mapping. Correct labels with wrong visual identity = FAIL.

## Validation independence

SELF-VALIDATION, CROSS-VALIDATION, IMPACT VALIDATION and REGRESSION VALIDATION are separate gates.

- SELF-VALIDATION: compare result to active contract/rules.
- CROSS-VALIDATION: use an independent evidence path/method/source/representation/validator when material.
- IMPACT VALIDATION: inspect intended and unintended downstream/upstream consequences.
- REGRESSION VALIDATION: compare protected pre-change state to post-change state.

SAME ASSERTION REPEATED ≠ CROSS-VALIDATION.
CHANGE WORKS ≠ IMPACT PASS.
NEW RULE PRESENT ≠ REGRESSION PASS.

For corrected omission/recovery/enforcement failures, regression validation SHALL include representative replay/equivalent evidence when mechanically applicable.

## Validation dimensions

- Source coverage
- Authority / reference isolation
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
- Recovery-failure / false-missing / user-forced-recovery recurrence
- Handoff portability / bundle closure when applicable
- Rule enforcement / harness realization
- Implementation evidence
- Release evidence

## Claim-level gate

LOGIC PASS ≠ SCHEMA PASS ≠ DATA PASS ≠ RUNTIME PASS ≠ INTEGRATION PASS ≠ BUILD PASS ≠ LOCAL PASS ≠ DEPLOY PASS ≠ RELEASE PASS.

A document delta, schema, local save, offline launch/cache, deploy response, relation field, deterministic replay or bundle fixture proves only its own level. Each higher PASS needs representative evidence at that level. Untested real-device, external-service, synchronization and end-to-end behavior remains UNKNOWN / UNVERIFIED.

`DETERMINISTIC GATE PASS ≠ LIVE LLM RUNTIME PASS`.
`REFERENCE ISOLATION RULE PRESENT ≠ EXTERNAL WORKSPACE RUNTIME ENFORCEMENT VERIFIED`.

## Ambiguity semantics

Research/evidence uncertainty remains `UNKNOWN / UNVERIFIED` when evidence is insufficient.
Release/result uncertainty SHALL NOT PASS; classify according to applicable gate.

`EVIDENCE AMBIGUITY ≠ RELEASE PASS`.

## Structural-integrity gate

When an active normative document uses an END/terminal marker, exactly one authoritative terminal boundary is allowed and normative content after it = FAIL. Validate unique/ordered sections, cross-references, canonical/status/revision metadata, and distinguish historical lineage labels from current governance.

Rule-owner integrity is additionally checked by `ENFORCEMENT/rule_registry_lint.py`.

## Connected/offline sync gate — conditional

For projects requiring offline, multi-device, external projection or eventual sync, validate distinct governance authority, runtime authority/event ledger, device replica/outbox and reporting projection.

LOCAL SAVE ≠ REMOTE ACKNOWLEDGEMENT.
OFFLINE-CAPABLE UI ≠ OFFLINE DATA SYNC.
TEMPLATE ID ≠ DATED INSTANCE ID ≠ EVENT ID.
RELATION EXISTS ≠ CORRECT OWNERSHIP / MEANING.

Validate identifiers/idempotency, replay/order, ownership/conflict policy, retry/recovery triggers, visible pending/conflict state, server-side scope authorization, secret non-exposure, connector throttling/failure, reconciliation and representative restart/reconnect/duplicate/out-of-order/multi-device/long-offline tests. Unperformed cases remain UNKNOWN.

## Decision-disposition gate

Every material source-derived item requires a traceable PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED disposition. HOLD needs reason/owner/exit condition; EXCLUDE needs scope rationale; OWNERSHIP_TRANSFER needs a named recoverable destination.

When the user requests first/full-conversation and attachment verification, Handoff/summary coverage alone is insufficient. Recover available original evidence and mark inaccessible raw history `UNVERIFIED_SOURCE_COVERAGE` rather than claiming impossible completeness.

For explicit global/all-conversation forensic audit, also inventory source families and check recurring correction/failure patterns across recovered conversations. A large report built from one chat/Handoff is NOT full-scan PASS.

## Status vocabulary

PASS / PASS_WITH_CONDITIONS / FAIL / NOT PASS / UNKNOWN / UNVERIFIED / NOT PERFORMED / HOLD / CONFLICT.

Do not collapse design validation into implementation validation. Do not claim PASS when material source coverage, end-to-end traceability, required enforcement, authority isolation, or reverse-validation remains UNVERIFIED.
