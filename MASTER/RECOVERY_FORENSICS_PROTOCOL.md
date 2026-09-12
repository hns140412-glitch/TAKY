# TAKY RECOVERY FORENSICS PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Activation: EXPLICIT USER INVOCATION ONLY
Default runtime state: OFF

## 1. CORE RULE

`USER KEYWORD = RECOVERY SEED, NOT RECOVERY SCOPE`
`KEYWORD HIT ≠ SOURCE COVERAGE`
`KEYWORD MISS ≠ PRIOR DECISION ABSENCE`
`SEARCH MISS ≠ SOURCE ABSENCE`
`RECOVERY FAILURE ≠ USER NEVER SAID`
`MASTER ABSENCE ≠ CONVERSATION ABSENCE`
`HANDOFF ABSENCE ≠ PRIOR RULE ABSENCE`
`SUMMARY ABSENCE ≠ PRIOR RULE ABSENCE`
`CURRENT CHAT MISS ≠ ACCOUNT-HISTORY ABSENCE`

Ordinary source recovery and applicable-rule loading may occur in normal TAKY work.
Full historical forensic reconstruction SHALL NOT auto-start.

If an ordinary task reveals a material historical omission or conflict, mark `RECOVERY_REQUIRED` when material and wait for explicit user invocation before full forensic reconstruction.

When the user explicitly requests all conversations, first conversation, full history, global scan, forensic recovery, or equivalent cross-conversation reconstruction, this protocol SHALL expand across every materially accessible recovery surface rather than silently limiting scope to the current chat, latest Handoff, one keyword query, one folder, or one repository.

## 1.1 Negative-Existence Claim Gate — HARD LOCK

A negative claim such as “없다”, “말한 적 없다”, “확인되지 않는다”, “자료가 없다”, “규칙이 없다” or equivalent is a material evidence claim when it affects recovery, design, implementation, deletion, supersession, HOLD, or user effort.

One failed query, one keyword miss, one summary omission, one MASTER omission, one Handoff omission, or one inaccessible surface SHALL NOT by itself justify a global absence claim when other recovery paths materially exist.

Before a material negative-existence claim, use fit-for-purpose multi-path recovery as available:

`CURRENT CONVERSATION → CONVERSATION/LIBRARY RAW EVIDENCE → CONTEXT LEDGER → HANDOFF/SOURCE POINTERS → ATTACHMENTS/SCREENSHOTS → HISTORICAL MASTER/REV → CURRENT CANONICAL/PROJECT SOURCE → CONNECTED WORKSPACE/DRIVE/NOTION → ACTUAL IMPLEMENTATION/EVIDENCE`.

Search semantically and by distinctive entities/relations, not by exact keyword alone, when wording may have changed.

If coverage is still incomplete, state the boundary precisely: `NOT FOUND IN CHECKED SOURCES / RECOVERY_REQUIRED / UNVERIFIED_SOURCE_COVERAGE`; do not convert it to `NEVER EXISTED`.

## 1.2 Recovery-Failure Taxonomy — HARD LOCK

For material cross-conversation recovery, distinguish:

- `TRUE_UNAVAILABLE` — original source is genuinely inaccessible after available recovery paths are checked; preserve pointer/gap as `UNVERIFIED_SOURCE_COVERAGE`.
- `RECOVERY_FAILED` — source was materially recoverable but the recovery/search process failed to retrieve it before a decision or claim was made.
- `FALSE_MISSING_DECLARATION` — TAKY/Assistant declared an item absent/not found without sufficient recovery, and later evidence proves the item existed.
- `USER_FORCED_RECOVERY` — the user had to search old chats, locate a file, capture a screenshot, re-upload evidence, or otherwise perform recovery work that TAKY should reasonably have attempted itself.
- `POST_CORRECTION_REOCCURRENCE` — the same material omission/misinterpretation/recovery failure recurs after the user correction or canonical rule already existed.

`TRUE_UNAVAILABLE ≠ RECOVERY_FAILED`.
`UNVERIFIED_SOURCE_COVERAGE` SHALL NOT be used to conceal a known recovery failure.

A `USER_FORCED_RECOVERY` event is also a `NO USER-AS-QA` failure unless the required source was genuinely inaccessible to available tools and the user was the only possible source holder.

A `POST_CORRECTION_REOCCURRENCE` event is a regression failure and SHALL trigger root-cause review rather than another isolated patch only.

## 2. CHRONOLOGY BEFORE CONSOLIDATION — HARD LOCK IN FORENSIC MODE

Before consolidating a recovered rule, trace the recoverable decision episode:

`EARLIEST RECOVERABLE PROPOSAL → USER RESPONSE → MODIFICATION → CONFIRM / HOLD / REJECT → LATER USER CORRECTION → CURRENT DISPOSITION`.

A later summary SHALL NOT erase the decision's prior lifecycle.

When a user supplies a screenshot/capture of an earlier conversation after TAKY failed to recover it, preserve both events:

`ORIGINAL PRIOR TURN / CAPTURED CONTENT → ASSISTANT FALSE-MISSING OR RECOVERY GAP → USER RECOVERY ACTION → RECOVERED DECISION → CURRENT REFLECTION`.

Do not misclassify the recovered screenshot as a newly invented requirement merely because it entered the current chat later.

## 3. RECOVERY FLOW

After chronology recovery, expand the material decision graph:

`SEED → SUBJECT / INTENT / ENTITY → DECISION EPISODE → SEMANTIC DECISION GRAPH → ORIGINAL SOURCE → HISTORICAL REV / HANDOFF / MASTER → CURRENT OWNER / RESULT → IMPLEMENTATION / RESULT EVIDENCE → FORWARD TRACE → REVERSE TRACE → COVERAGE MATRIX → SECOND-PASS OMISSION CHECK → RECURRENCE CHECK`.

Recovery shall expand only as far as materially necessary to resolve the active decision graph, except when the user explicitly requests a full/global/all-conversation scan; then scope is every materially accessible relevant conversation/source surface, with unresolved coverage recorded rather than silently omitted.

## 3.1 Cross-Conversation Recurrence Scan — HARD LOCK WHEN EXPLICITLY REQUESTED

A full/global conversation audit SHALL not stop at recovering isolated decisions. It SHALL identify repeated failure patterns across conversations/projects where materially relevant.

Maintain a recurrence ledger sufficient to answer:
- what the user originally asked;
- how TAKY/Assistant interpreted it;
- what was omitted, substituted, or falsely declared missing;
- whether the user had to recover/prove it;
- whether an applicable TAKY rule already existed;
- whether the same pattern recurred later;
- what downstream artifact/implementation was affected;
- which canonical gate should prevent recurrence.

At minimum classify applicable events with the recovery-failure taxonomy in §1.2 plus command/result discrepancy classes from `MASTER/INTENT_EXECUTION_PROTOCOL.md`.

## 4. RECOVERY SOURCE PRIORITY

When available and materially relevant, use:

`ORIGINAL / RAW CONVERSATION → ORIGINAL ATTACHMENT / USER-PROVIDED RECOVERY WITNESS → ORIGINAL EXTERNAL SOURCE → HISTORICAL MASTER / REV → HANDOFF / CHECKPOINT → SUMMARY / SYNTHESIS`.

This is a recovery-evidence preference, not an authority override.
Latest valid user correction and applicable higher authority still govern final disposition.

A screenshot of a prior chat is `RECOVERY_WITNESS_EVIDENCE`: it can directly prove visible conversation content and that the user recovered it, but it does not automatically become canonical authority over later valid corrections or current source-of-truth state.

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
- RECOVERY_WITNESS_EVIDENCE
- CORROBORATED
- DOCUMENTED_CLAIM
- CONTEXT_SUPPORTED_INFERENCE
- WEAK_INFERENCE
- UNVERIFIED

Inference may create recovery candidates but SHALL NOT silently become canonical fact.

## 7. FORENSIC OUTPUT CONTRACT

A completed forensic report SHALL include, at fit-for-purpose depth:
1. Source Coverage / Recovery Surface Inventory
2. Chronological Decision Trace
3. Current Active Rules
4. Superseded / Rejected / Adjusted Rules
5. Live Candidates / HOLD
6. Canonical Migration Candidates
7. Operational / Implementation Candidates
8. False-Missing / User-Forced-Recovery / Recurrence Ledger
9. Unverified / Not Implemented
10. Coverage Gaps / Recovery Required
11. Cross-source / independent validation plan when material

For explicit full/global scans, a result is not “full” merely because the report is large. Every material accessible source family SHALL be inventoried and either examined/dispositioned or explicitly recorded as not yet covered.

## 8. STOP RULE

Stop when every material node has either:
- a recoverable source and disposition, or
- an explicit unresolved status such as HOLD / CONFLICT / RECOVERY_REQUIRED / UNVERIFIED_SOURCE_COVERAGE,

and additional expansion is unlikely to change the material decision.

For a full/global scan, also require that the source-family inventory has no silently unvisited material recovery surface and that recurrence patterns have been checked across recovered conversations, not only within the latest chat.

## 9. EXIT RULE

After forensic recovery, release unnecessary historical context and return to normal TAKY selective-context operation.

`RECOVERY MODE ≠ PERMANENT RUNTIME MODE`

Preserve the resulting recovery ledger, Context Events, canonical deltas, unresolved coverage, and regression fixtures so ordinary future work can use targeted recovery instead of repeatedly rescanning the entire history.
