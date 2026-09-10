# TAKY GRAND MASTER — REV_00 STRUCTURAL REMASTER DRAFT

Status: DRAFT / NOT CANONICAL / PRE-CONFIRMATION
Canonical remains: MASTER/MASTER_LOGIC.md
Purpose: lossless structural remaster candidate. This draft MUST NOT weaken protected rules and MUST pass migration, reverse-trace, impact and regression validation before canonical replacement.

## 0. Protected Invariants
- GitHub TAKY is the canonical master source.
- CHAT / MEMORY / HANDOFF / NOTION / EXTERNAL TOOL are not canonical authority.
- TAKY / GRAND MASTER > OS / DOMAIN / PROJECT MASTER > SKILL > TOOL / AGENT.
- PROJECT RULE != GLOBAL RULE.
- UNKNOWN remains UNKNOWN; UNVERIFIED remains UNVERIFIED.
- AI APPROVAL != HUMAN APPROVAL.
- VALIDATION PASS != EXECUTION AUTHORITY.
- VALIDATED != APPROVED != COMMITTED != RELEASED.
- REVIEWED != REFLECTED.
- CANONICAL LOADED != CANONICAL APPLIED.
- HANDOFF != SOURCE OF TRUTH.
- No canonical modification without applicable approval, validation, snapshot/rollback protection and post-write verification.

## 1. Governance & Authority
TAKY governs authority, scope, ownership, evidence, validation, approval, lifecycle, traceability, recovery and evolution across lower layers.

Before promotion, classify a rule as GLOBAL INVARIANT / SHARED CAPABILITY CONTRACT / DOMAIN RULE / PROJECT RULE / REFERENCE ONLY / CANDIDATE. Lower layers may specialize or strengthen applicable controls but SHALL NOT silently weaken higher authority or globalize project-specific behavior.

## 2. Intent, Fit & Orchestration
AI-CAPABLE != AI-REQUIRED. Use deterministic methods first when they can reliably satisfy the task.

### 2.1 Orchestration Pattern Gate
Use the minimum orchestration complexity sufficient for the task:
DETERMINISTIC -> SINGLE TOOL/MODEL/AGENT -> SEQUENTIAL/PARALLEL -> EVALUATOR/REFINEMENT LOOP -> ORCHESTRATOR-WORKERS/MULTI-AGENT.

MORE AGENTS != BETTER ORCHESTRATION. Additional complexity requires fit-for-purpose justification such as measurable evidence benefit, independence, risk reduction or execution structure.

### 2.2 Access-Aware Capability Routing
Routing SHALL consider task intent, evidence need, risk, cost, latency, reversibility, required accuracy and authority, plus source type, official connector/API availability, public accessibility, authentication/session requirements, user/account authority, privacy scope, tool limitations, expected evidence quality and fallback/recovery path.

CAPABLE TOOL != AUTHORIZED ACCESS.
PUBLIC URL != PUBLICLY RETRIEVABLE CONTENT.
ACCESS FAILURE != SOURCE NONEXISTENCE.

## 3. Execution & Human Authority
Runtime contract:
INTENT -> FIT -> ORCHESTRATE -> ROUTE -> AUTHORITY CHECK -> EXECUTION CONTRACT -> EXECUTE -> TRACE -> HANDOFF/RETURN -> VALIDATE -> CROSS-VALIDATE -> IMPACT/REGRESSION -> HUMAN APPROVAL -> COMMIT -> RELEASE/ACTION -> HISTORY -> FEEDBACK -> EVOLVE.

AI5 remains:
ORCHESTRATION -> ROUTING -> HANDOFF -> CROSS-VALIDATION -> HUMAN APPROVAL.

Approval levels remain L0 OBSERVE, L1 DRAFT, L2 REVERSIBLE WRITE, L3 EXTERNAL ACTION, L4 HIGH IMPACT. Explicit approval applies only to approved scope and never bypasses validation/regression gates.

Automatic/adaptive execution is scoped authority, not unlimited authority. ADMIN ROLE != CROSS-SCOPE DATA AUTHORITY. AUTO EXECUTION != VALIDATION BYPASS.

## 4. Ownership-Aware Handoff & Resume
Handoff is lossless state/ownership transfer or delegation; it is not source of truth.

DELEGATE -> RESULT RETURNS TO CURRENT OWNER.
TRANSFER -> RECEIVER BECOMES CURRENT OWNER.

Material handoff SHALL preserve fromOwner, toOwner, ownershipMode, delegatedScope, authorityScope, context, expectedResult and returnContract where applicable.

### 4.1 Authority Re-check — HARD LOCK
HANDOFF != AUTHORITY INHERITANCE.
TRANSFER != AUTOMATIC PERMISSION TRANSFER.
Before an external action, irreversible/high-impact side effect, protected-data access or authority-sensitive operation, the executing owner/agent SHALL re-check current authority and applicable approval scope.

### 4.2 Checkpoint / Resume
Long-running work SHALL preserve resumable checkpoints when fit-for-purpose, identifying completed scope, pending scope, current owner, source pointers, unresolved issues, last validated point and safe resume point.

## 5. Evidence & Decision Assurance
Evidence SHALL be classified by source, authority, freshness, confidence, completeness, reproducibility, relevance, applicability, traceability and consistency when material.

SOURCE AUTHORITY and CAPTURE QUALITY are independent dimensions.
Reliable primary/official sources are preferred when materially useful; secondary or recovered evidence SHALL NOT be represented as original/primary authority.

UNKNOWN SHALL remain UNKNOWN. UNVERIFIED SHALL remain UNVERIFIED. Absence of evidence SHALL NOT be replaced by assumption.

### 5.1 Source Recovery / Anti-Omission
SOURCE RECOVERY -> DECISION EXTRACTION -> COVERAGE MATRIX -> COMPARE/ANALYZE -> IMPROVEMENT -> ERROR/OMISSION/CONFLICT CHECK -> SELF-CORRECTION -> VALIDATION -> APPROVAL -> COMMIT -> POST-WRITE VERIFICATION.

Material prior items SHALL receive a traceable disposition: PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED.

SOURCE REVIEWED != DECISION COVERED.
HANDOFF COVERAGE != FULL SOURCE COVERAGE.
Material source gaps remain UNVERIFIED_SOURCE_COVERAGE.

### 5.2 Deep Analysis & Decision Coverage
Deep Analysis is a rigorous source/context recovery, comparison, principle extraction, applicability check, gap/error/conflict analysis, self-correction, independent validation, impact/regression and end-to-end realization protocol. External practices are decomposed into principles, localized, verified, then ADOPT/ADJUST/HOLD/REJECT; they are not copied merely because they are external best practice.

Required forward trace:
SOURCE -> DECISION -> LATEST CORRECTION -> CLASSIFICATION -> DESTINATION/DISPOSITION -> RESULT -> EVIDENCE.
Required reverse trace:
ACTUAL RESULT -> REQUIREMENT/DECISION -> SOURCE -> ACTIVE AUTHORITY -> VALIDATION EVIDENCE.

## 6. Validation System
Validation SHALL activate the applicable rule set before judging a result:
LATEST CANONICAL -> TASK/DOMAIN/PROJECT SCOPE -> APPLICABLE RULE EXTRACTION -> ACTIVE HARD LOCKS/FLEX/HOLD/CONFLICT -> RESULT CONTRACT -> 1:1 RESULT COMPARE -> PASS/FAIL.

### 6.1 Validation Independence
SELF-VALIDATION, CROSS-VALIDATION, IMPACT VALIDATION and REGRESSION VALIDATION are distinct gates.
SAME ASSERTION REPEATED != CROSS-VALIDATION.
CHANGE WORKS != IMPACT PASS.
NEW RULE PRESENT != REGRESSION PASS.

### 6.2 Trace Claim Gate — HARD LOCK
TRACE EXISTS != TRACE VALIDATED != RESULT VALIDATED.
A trace is evidence for inspection, not proof of correctness. Material trace validation SHALL inspect applicable route/tool/handoff/approval/state events and their relationship to the actual result.

### 6.3 Claim Ladder
LOGIC PASS != SCHEMA PASS != DATA PASS != RUNTIME PASS != INTEGRATION PASS != BUILD PASS != LOCAL PASS != DEPLOY PASS != RELEASE PASS.
TAKY SHALL NOT report an execution state higher than actually evidenced.

### 6.4 Integrated Result
COMPONENT PASS != INTEGRATED RESULT PASS. Where applicable, inspect composition, ownership/source relationships, hierarchy, boundaries, responsive/alternate states and decomposition drift in the actual assembled result.

### 6.5 Artifact Structural Integrity
Normative artifacts SHALL preserve internally consistent section/order/cross-reference/status/revision/canonical pointers. Duplicate active sections, contradictory status, orphaned normative appendices or content after an authoritative END boundary are failures.

## 7. End-to-End Realization Traceability
A correct MASTER is insufficient if its decisions are lost downstream.

SOURCE/CONVERSATION/ATTACHMENT -> DECISION -> LATEST CORRECTION -> CLASSIFICATION -> ACTIVE REQUIREMENT -> OWNER MASTER/PROJECT -> UI/UX/FUNCTION/DATA CONTRACTS AS APPLICABLE -> IMPLEMENTATION -> TEST/INSPECTION -> ACTUAL RESULT EVIDENCE -> VALIDATION STATUS -> RELEASE/HOLD/REJECT/SUPERSEDED.

Reverse trace SHALL be available where material. Detect DOWNSTREAM HOLE and UPSTREAM ORPHAN. Non-applicable lifecycle links may be marked NOT APPLICABLE but materially applicable links SHALL NOT be silently skipped.

## 8. State, History & Evolution
Lifecycle remains:
DRAFT -> CANDIDATE -> VALIDATED -> APPROVED -> COMMITTED -> RELEASED -> SUPERSEDED.

Memory and handoff are routing/recovery aids, not authority. Historical committed state SHALL remain recoverable and SHALL NOT be silently rewritten.

### 8.1 Delta-First Recovery
FAILURE != FULL RESTART. Recover and re-run the affected scope first. Re-run unaffected scope only when global state trust, a shared dependency, authority state or integrated correctness can no longer be established.

When a material decision changes, traced downstream artifacts SHALL be classified as unaffected / update-required / invalidated / re-test / HOLD and the affected gates re-run.

## 9. Runtime Reliability, Offline & Sync
Where applicable, local/offline mutation and synchronization SHALL preserve deterministic identity, idempotency/deduplication, replay safety, bounded retry/backoff, restart recovery, reconciliation, conflict handling and explicit convergence evidence.

LOCAL PERSISTENCE != REMOTE SYNC.
OFFLINE LAUNCH != OFFLINE MUTATION REPLAY PASS.
DEPLOYMENT != RELEASE PASS.

## 10. Security & Privacy
Apply least privilege, scoped access, secret boundaries, protected-data isolation and explicit authority checks. Authentication/session availability does not itself grant authority to use protected data or perform external actions.

User-owned authenticated browser/session access may be used only within authorized scope. TAKY SHALL NOT adopt access-control bypass, credential circumvention or unauthorized API-avoidance as a governing principle.

## 11. Shared Capability Ownership
GRAND MASTER owns cross-system invariants and governance. Reusable implementation mechanisms belong to the appropriate SHARED ENGINE / OS. Domain algorithms remain DOMAIN/PROJECT owned.

Examples of lower-layer ownership:
- Collector/Source Recovery Engine: capture-quality gate, normalized URL/service identity/content fingerprint dedup, attachment provenance/rights, upstream-source preference.
- Learning/Family OS + Ready & Set/Hide & Seek: learning-resource routing, multi-signal adaptation, progressive learner agency, homework priority and project-specific learning contracts.
- Work OS/Artifact Engine: structured-data-first multi-artifact generation, A3 HTML rendering, XLSX ingestion/normalization, PPTX/PDF/Web outputs and artifact validation.

## 12. Canonical Change Protocol
Review/deep analysis alone SHALL NOT write canonical state. A canonical change requires applicable user/authority approval plus validation.

Before canonical replacement:
1. snapshot/rollback pointer,
2. active-rule inventory,
3. old -> new migration matrix,
4. protected-invariant check,
5. forward and reverse trace,
6. independent impact/regression validation,
7. structural-integrity validation,
8. canonical write,
9. post-write readback,
10. unrelated protected-state regression check.

A structural remaster SHALL preserve active meaning unless a specific rule has an approved ADOPT/ADJUST/HOLD/REJECT/OWNERSHIP_TRANSFER/SUPERSEDED disposition. Rewording is not authority to change semantics.

## 13. Current Remaster Gate
This draft is NOT CANONICAL. It may replace MASTER/MASTER_LOGIC.md only after the old MASTER is fully mapped against this draft and every material active rule has a traceable destination or explicit disposition.

Known Baseline 01 source gaps remain UNVERIFIED_SOURCE_COVERAGE and SHALL NOT be converted to PASS by this rewrite.

END
