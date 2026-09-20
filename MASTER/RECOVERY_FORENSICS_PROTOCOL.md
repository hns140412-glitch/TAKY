# TAKY RECOVERY FORENSICS PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Activation: EXPLICIT USER INVOCATION ONLY for full historical forensics
Default full-forensic runtime state: OFF
Normative failure-token semantics: `MASTER/FAILURE_TAXONOMY.md`

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

Ordinary targeted source recovery and applicable-rule loading may occur in normal TAKY work. Full historical forensic reconstruction SHALL NOT auto-start.

If an ordinary task reveals a material historical omission or conflict, mark `RECOVERY_REQUIRED` when material and wait for explicit user invocation before full forensic reconstruction.

When the user explicitly requests all conversations, first conversation, full history, global scan, forensic recovery, or equivalent cross-conversation reconstruction, this protocol SHALL expand across every materially accessible recovery surface rather than silently limiting scope to the current chat, latest Handoff, one keyword query, one folder, or one repository.

## 1.1 Negative-Existence Claim Gate — HARD LOCK

A negative claim such as “없다”, “말한 적 없다”, “확인되지 않는다”, “자료가 없다”, “규칙이 없다” or equivalent is a material evidence claim when it affects recovery, design, implementation, deletion, supersession, HOLD, or user effort.

One failed query, one keyword miss, one summary omission, one MASTER omission, one Handoff omission, or one inaccessible surface SHALL NOT by itself justify a global absence claim when other recovery paths materially exist.

Before a material negative-existence claim, use fit-for-purpose multi-path recovery as available:

`CURRENT CONVERSATION → CONVERSATION/LIBRARY RAW EVIDENCE → CONTEXT LEDGER → HANDOFF/SOURCE POINTERS → ATTACHMENTS/SCREENSHOTS → HISTORICAL MASTER/REV → CURRENT CANONICAL/PROJECT SOURCE → CONNECTED WORKSPACE/DRIVE/NOTION → ACTUAL IMPLEMENTATION/EVIDENCE`.

Search semantically and by distinctive entities/relations, not by exact keyword alone, when wording may have changed.

If coverage is still incomplete, state the boundary precisely: `NOT FOUND IN CHECKED SOURCES / RECOVERY_REQUIRED / UNVERIFIED_SOURCE_COVERAGE`; do not convert it to `NEVER EXISTED`.

## 1.1A Recovery-Family Exhaustion Before User Request — HARD LOCK

Before asking the user to find an old chat, re-upload a recoverable file, provide a screenshot as proof, or perform debugging/evidence gathering that TAKY can materially attempt itself, inventory distinct recovery families.

Distinct families include, when available:
- current conversation;
- conversation/library raw evidence;
- Context Ledger / Handoff / source pointers;
- canonical/history/repository;
- connected workspace such as Drive/Notion;
- actual implementation/runtime/evidence.

Repeated keyword variations inside one source are one family, not multiple recovery attempts.

Execution rule:
- 3 or more materially available families → attempt at least 3 materially distinct families;
- fewer than 3 materially available families → attempt all materially available families;
- a material unattempted recovery family remains → user recovery/debug request is blocked;
- the user is genuinely the only possible source holder → a bounded request is allowed and the boundary must be stated.

The recovery attempt record SHALL identify available families, attempted families, blocked/unavailable families, whether a material path remains, and whether the user is the only possible source holder.

Violation is classified using the normative taxonomy as `RECOVERY_FAILED / USER_AS_QA`; later proof by the user may additionally become `USER_FORCED_RECOVERY`.

`THREE KEYWORDS ≠ THREE RECOVERY FAMILIES`.
`NO USER-AS-QA ≠ NEVER ASK THE USER`; it means do not ask before available system-side recovery is exhausted or when the user is not uniquely required.

## 1.1B Evidence Recovery Pass for C2S / targeted recovery — HARD LOCK

This protocol also governs **targeted historical recovery invoked by C2S** when a material prior state must be recovered to compile correctly. Full forensic mode does not need to be globally activated for this bounded pass.

Required distinction:

`NO_EVIDENCE_FOUND != EVIDENCE_ABSENT`

A targeted Evidence Recovery Pass SHOULD combine materially available recovery modes instead of repeating exact-keyword searches in one surface:
- current term;
- legacy/superseded/alternate terms;
- semantic entity/relationship search;
- decision-state markers such as `확정 / LOCK / PASS / 기준 / 수정 / 교체 / HOLD / SUPERSEDED`;
- attachment/image/ZIP/manifest lineage;
- parent/sibling folder traversal;
- historical revision neighbors;
- reverse trace from later summary/Handoff/canonical claims to original evidence.

When one material trace is found, expand locally around that trace before concluding recovery is exhausted.

If the user has explicitly said a prior artifact/decision existed, that assertion is a recovery seed with high materiality. It does not itself prove the historical content, but it blocks premature global absence claims while accessible system-side recovery paths remain.

Allowed bounded outputs:
- `RECOVERED_DIRECT`
- `RECOVERED_CORROBORATED`
- `NOT_FOUND_IN_CHECKED_SOURCES`
- `UNVERIFIED_SOURCE_COVERAGE`
- `TRUE_UNAVAILABLE`

A later user-provided screenshot/image/file that proves an item was recoverable after TAKY declared it missing SHALL create:
1. a recovery-failure event;
2. a correction atom;
3. affected-artifact propagation;
4. recurrence-prevention review.

## 1.2 Recovery-Failure Activation Subset — HARD LOCK

Normative semantics for all failure/discrepancy tokens are owned solely by `MASTER/FAILURE_TAXONOMY.md`. This section is only the recovery-specific activation subset and SHALL NOT redefine those meanings.

Recovery-specific tokens:
- `TRUE_UNAVAILABLE`
- `UNVERIFIED_SOURCE_COVERAGE`
- `RECOVERY_FAILED`
- `FALSE_MISSING_DECLARATION`
- `USER_FORCED_RECOVERY`
- `POST_CORRECTION_REOCCURRENCE`

Apply definitions and cross-axis mappings in `MASTER/FAILURE_TAXONOMY.md`.

`TRUE_UNAVAILABLE ≠ RECOVERY_FAILED`.
`UNVERIFIED_SOURCE_COVERAGE` SHALL NOT be used to conceal a known recovery failure.
A `USER_FORCED_RECOVERY` event is also a `NO USER-AS-QA` failure unless the required source was genuinely inaccessible to available tools and the user was the only possible source holder.
A `POST_CORRECTION_REOCCURRENCE` event is a regression failure and SHALL trigger root-cause review rather than another isolated patch only.

## 2. CHRONOLOGY BEFORE CONSOLIDATION — HARD LOCK IN FORENSIC MODE

Before consolidating a recovered rule, trace the recoverable decision episode:
`EARLIEST RECOVERABLE PROPOSAL → USER RESPONSE → MODIFICATION → CONFIRM / HOLD / REJECT → LATER USER CORRECTION → CURRENT DISPOSITION`.

A later summary SHALL NOT erase the decision's prior lifecycle.
When a user supplies a screenshot/capture of an earlier conversation after TAKY failed to recover it, preserve both the original prior content and the recovery event. Do not misclassify the recovered screenshot as a newly invented requirement merely because it entered the current chat later.

## 3. RECOVERY FLOW

After chronology recovery, expand the material decision graph:
`SEED → SUBJECT / INTENT / ENTITY → DECISION EPISODE → SEMANTIC DECISION GRAPH → ORIGINAL SOURCE → HISTORICAL REV / HANDOFF / MASTER → CURRENT OWNER / RESULT → IMPLEMENTATION / RESULT EVIDENCE → FORWARD TRACE → REVERSE TRACE → COVERAGE MATRIX → SECOND-PASS OMISSION CHECK → RECURRENCE CHECK`.

Recovery shall expand only as far as materially necessary to resolve the active decision graph, except when the user explicitly requests a full/global/all-conversation scan; then scope is every materially accessible relevant conversation/source surface, with unresolved coverage recorded rather than silently omitted.

## 3.1 Cross-Conversation Recurrence Scan — HARD LOCK WHEN EXPLICITLY REQUESTED

A full/global conversation audit SHALL not stop at recovering isolated decisions. It SHALL identify repeated failure patterns across conversations/projects where materially relevant.

Maintain a recurrence ledger sufficient to answer what the user asked, how TAKY/Assistant interpreted it, what was omitted/substituted/falsely declared missing, whether the user had to recover it, whether an applicable rule already existed, whether the same pattern recurred, what downstream artifact was affected, and which gate should prevent recurrence.

At minimum classify applicable events with the recovery activation subset in §1.2 plus applicable intent/result, reflection/handoff, and enforcement classes from `MASTER/FAILURE_TAXONOMY.md`.
`MASTER/INTENT_EXECUTION_PROTOCOL.md` owns execution flow that activates intent/result checks; it does not independently own token semantics.

## 4. RECOVERY SOURCE PRIORITY

When available and materially relevant, prefer:
`ORIGINAL / RAW CONVERSATION → ORIGINAL ATTACHMENT / USER-PROVIDED RECOVERY WITNESS → ORIGINAL EXTERNAL SOURCE → HISTORICAL MASTER / REV → HANDOFF / CHECKPOINT → SUMMARY / SYNTHESIS`.

This is a recovery-evidence preference, not an authority override. Latest valid user correction and applicable higher authority still govern final disposition.

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

Stop when every material node has either a recoverable source and disposition, or an explicit unresolved status such as HOLD / CONFLICT / RECOVERY_REQUIRED / UNVERIFIED_SOURCE_COVERAGE, and additional expansion is unlikely to change the material decision.

For a full/global scan, also require that the source-family inventory has no silently unvisited material recovery surface and that recurrence patterns have been checked across recovered conversations, not only within the latest chat.

## 9. EXIT RULE

After forensic recovery, release unnecessary historical context and return to normal TAKY selective-context operation.
`RECOVERY MODE ≠ PERMANENT RUNTIME MODE`

Preserve the resulting recovery ledger, Context Events, canonical deltas, unresolved coverage, and regression fixtures so ordinary future work can use targeted recovery instead of repeatedly rescanning the entire history.

## 10. NotebookLM-assisted recovery specialization

When NotebookLM is used to help inspect large conversation/source sets, activate `MASTER/NOTEBOOKLM_RECOVERY_PROTOCOL.md` (TKY-NBLM-001).

NotebookLM may accelerate chronology, correction, recurrence and omission-candidate discovery, but it SHALL remain a recovery assistant:
- raw/original source remains preferred evidence;
- NotebookLM output remains `REFERENCE_ONLY / EVIDENCE_ASSIST`;
- derived summaries/Handoffs shall not replace available raw conversation;
- source-security screening is required before notebook ingestion;
- notebook-derived claims used for canonical change require raw-source recheck plus TKY-C2S disposition.

`NOTEBOOKLM ASSISTED != FORENSIC SOURCE AUTHORITY OVERRIDE`

## 11. Context-economy boundary

Ordinary continuity recovery is governed by TKY-CONTINUITY-001.

Full forensic mode remains OFF unless explicitly invoked for full/global reconstruction. A routine missing historical detail should first use the progressive L0→L1→L2→L3 ladder rather than activating this full protocol.

`TARGETED CONTINUITY RECOVERY != FULL FORENSIC MODE`
