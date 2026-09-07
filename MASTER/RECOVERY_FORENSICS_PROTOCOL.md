# TAKY RECOVERY FORENSICS PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Activation: EXPLICIT USER INVOCATION ONLY
Default runtime state: OFF

## 1. CORE RULE

`USER KEYWORD = RECOVERY SEED, NOT RECOVERY SCOPE`
`KEYWORD HIT ≠ SOURCE COVERAGE`
`KEYWORD MISS ≠ PRIOR DECISION ABSENCE`
`MASTER ABSENCE ≠ CONVERSATION ABSENCE`
`HANDOFF ABSENCE ≠ PRIOR RULE ABSENCE`
`SUMMARY ABSENCE ≠ PRIOR RULE ABSENCE`

Ordinary source recovery and applicable-rule loading may occur in normal TAKY work.
Full historical forensic reconstruction SHALL NOT auto-start.

If an ordinary task reveals a material historical omission or conflict, mark `RECOVERY_REQUIRED` when material and wait for explicit user invocation before full forensic reconstruction.

## 2. CHRONOLOGY BEFORE CONSOLIDATION — HARD LOCK IN FORENSIC MODE

Before consolidating a recovered rule, trace the recoverable decision episode:

`EARLIEST RECOVERABLE PROPOSAL → USER RESPONSE → MODIFICATION → CONFIRM / HOLD / REJECT → LATER USER CORRECTION → CURRENT DISPOSITION`

A later summary SHALL NOT erase the decision's prior lifecycle.

## 3. RECOVERY FLOW

After chronology recovery, expand the material decision graph:

`SEED → SUBJECT / INTENT / ENTITY → DECISION EPISODE → SEMANTIC DECISION GRAPH → ORIGINAL SOURCE → HISTORICAL REV / HANDOFF / MASTER → CURRENT OWNER / RESULT → IMPLEMENTATION / RESULT EVIDENCE → FORWARD TRACE → REVERSE TRACE → COVERAGE MATRIX → SECOND-PASS OMISSION CHECK`

Recovery shall expand only as far as materially necessary to resolve the active decision graph.

## 4. RECOVERY SOURCE PRIORITY

When available and materially relevant, use:

`ORIGINAL / RAW CONVERSATION → ORIGINAL ATTACHMENT / ORIGINAL EXTERNAL SOURCE → HISTORICAL MASTER / REV → HANDOFF / CHECKPOINT → SUMMARY / SYNTHESIS`

This is a recovery-evidence preference, not an authority override.
Latest valid user correction and applicable higher authority still govern final disposition.

## 5. PROJECT CONTAMINATION GUARD

Semantic similarity, shared keywords or co-retrieval SHALL NOT establish project ownership.

`RELATED IDEA ≠ SAME PROJECT RULE`

Classify recovered cross-project material as:
- `DIRECT_PROJECT_SOURCE`
- `CROSS_PROJECT_BORROW_CANDIDATE`
- `REFERENCE_ONLY`
- `UNVERIFIED`

## 6. EVIDENCE CLASS

- DIRECT_SOURCE
- CONTEXT_SUPPORTED_INFERENCE
- WEAK_INFERENCE
- UNVERIFIED

Inference may create recovery candidates but SHALL NOT silently become canonical fact.

## 7. FORENSIC OUTPUT CONTRACT

A completed forensic report SHALL include, at fit-for-purpose depth:
1. Chronological Decision Trace
2. Current Active Rules
3. Superseded / Rejected / Adjusted Rules
4. Live Candidates / HOLD
5. Canonical Migration Candidates
6. Operational / Implementation Candidates
7. Unverified / Not Implemented
8. Coverage Gaps / Recovery Required

## 8. STOP RULE

Stop when every material node has either:
- a recoverable source and disposition, or
- an explicit unresolved status such as HOLD / CONFLICT / RECOVERY_REQUIRED / UNVERIFIED_SOURCE_COVERAGE,

and additional expansion is unlikely to change the material decision.

## 9. EXIT RULE

After forensic recovery, release unnecessary historical context and return to normal TAKY selective-context operation.

`RECOVERY MODE ≠ PERMANENT RUNTIME MODE`
