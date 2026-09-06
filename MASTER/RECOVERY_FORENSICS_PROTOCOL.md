# TAKY RECOVERY FORENSICS PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Activation: EXPLICIT USER REQUEST OR MATERIAL RECOVERY/OMISSION DISPUTE ONLY
Default runtime state: OFF

## 1. CORE RULE

`USER KEYWORD = RECOVERY SEED, NOT RECOVERY SCOPE`
`KEYWORD HIT ≠ SOURCE COVERAGE`
`KEYWORD MISS ≠ PRIOR DECISION ABSENCE`
`MASTER ABSENCE ≠ CONVERSATION ABSENCE`
`HANDOFF ABSENCE ≠ PRIOR RULE ABSENCE`
`SUMMARY ABSENCE ≠ PRIOR RULE ABSENCE`

## 2. RECOVERY FLOW

`SEED → SUBJECT / INTENT / ENTITY → DECISION EPISODE → SEMANTIC DECISION GRAPH → ORIGINAL CONVERSATION / ATTACHMENTS → REV / HANDOFF / MASTER → LATER USER CORRECTIONS → IMPLEMENTATION / RESULT EVIDENCE → FORWARD TRACE → REVERSE TRACE → COVERAGE MATRIX → SECOND-PASS OMISSION CHECK`

Recovery shall expand only as far as materially necessary to resolve the active decision graph.

## 3. EVIDENCE CLASS

- DIRECT_SOURCE
- CONTEXT_SUPPORTED_INFERENCE
- WEAK_INFERENCE
- UNVERIFIED

Inference may create recovery candidates but SHALL NOT silently become canonical fact.

## 4. STOP RULE

Stop when every material node has either:
- a recoverable source and disposition, or
- an explicit unresolved status such as HOLD / CONFLICT / RECOVERY_REQUIRED / UNVERIFIED_SOURCE_COVERAGE,

and additional expansion is unlikely to change the material decision.

## 5. EXIT RULE

After forensic recovery, release unnecessary historical context and return to normal TAKY selective-context operation.

`RECOVERY MODE ≠ PERMANENT RUNTIME MODE`
