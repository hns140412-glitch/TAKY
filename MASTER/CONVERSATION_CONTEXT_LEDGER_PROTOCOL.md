# TAKY CONVERSATION CONTEXT LEDGER PROTOCOL

Status: REV_00 / CANONICAL CROSS-SYSTEM CONTINUITY PROTOCOL
Date: 2026-09-12
Authority: TAKY / GRAND MASTER

## 0. Purpose
Prevent context loss caused by repeated summarization. This protocol preserves recoverable conversational meaning, correction history, decision evolution, evidence links and unresolved work so a new conversation can resume from traceable context rather than from a lossy summary.

`SUMMARY ≠ CONTEXT PRESERVATION`
`HANDOFF ≠ ORIGINAL EVIDENCE`
`CONCLUSION WITHOUT WHY ≠ RECOVERABLE DECISION`

Absolute zero omission cannot be claimed for inaccessible sources. Inaccessible material remains `UNVERIFIED_SOURCE_COVERAGE`.

## 1. Continuity chain

`ORIGINAL CONVERSATION / ATTACHMENT / SOURCE EVIDENCE → CONVERSATION CONTEXT LEDGER → IDEA / DECISION TRACE → CANONICAL OWNER → IMPLEMENTATION EVIDENCE → HANDOFF → NEW-CONVERSATION RECOVERY`

The Ledger is an index and meaning-link layer over evidence. It does not replace the original evidence and does not become authority merely by recording it.

## 2. Preserve the formation of a decision

For material context, preserve the applicable chain:
`USER INTENT → USER STATEMENT / SOURCE → ASSISTANT PROPOSAL → USER CORRECTION / REJECTION / REFINEMENT → WHY IT CHANGED → DECISION → STATUS / DISPOSITION → OWNER → IMPLEMENTATION → VALIDATION → NEXT UNRESOLVED GATE`

Do not retain only the final sentence when earlier turns materially explain scope, meaning, rejection, correction or exceptions.

## 3. Context Event

A material Context Event should retain, when available:
- stable event id
- conversation/date/sequence pointer
- related project/domain/app
- user intent
- relevant original-turn/source pointers
- conversation flow in order
- corrections/refinements and their reason
- decision or unresolved question
- disposition: `PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED`
- canonical owner / reflection status
- implementation evidence/status
- validation status
- supersedes / superseded-by links
- related Context Event ids
- next unresolved gate
- source coverage limitation

This structure is not permission to paraphrase away the original evidence. Original accessible evidence remains recoverable by pointer or preservation record.

## 3.1 Recovery Witness Event — HARD LOCK

When a user reintroduces earlier evidence because TAKY/Assistant failed to recover it, create/link a Recovery Witness Event rather than treating the material as a new requirement by default.

Examples include:
- user uses ChatGPT conversation search and supplies the prior turn;
- user attaches a screenshot of the earlier conversation;
- user re-uploads an old file that was previously said to be missing;
- user identifies a historical Handoff/MASTER/source pointer that proves prior existence.

Preserve, when available:
`ORIGINAL PRIOR CONTEXT → ASSISTANT RECOVERY/ABSENCE CLAIM → USER RECOVERY ACTION → RECOVERY WITNESS → RECOVERED REQUIREMENT/DECISION → CURRENT OWNER/REFLECTION`.

Classify the recovery process using `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`:
`TRUE_UNAVAILABLE / RECOVERY_FAILED / FALSE_MISSING_DECLARATION / USER_FORCED_RECOVERY / POST_CORRECTION_REOCCURRENCE`.

A screenshot/capture proves only the visible content it contains and its recovery role; it does not automatically override later valid user corrections or canonical authority.

## 4. No deletion by summarization

A Handoff or compact context may be generated for speed, but omission from that compact representation SHALL NOT mean deletion, rejection or supersession.

Material ideas/decisions disappear from active routing only through an explicit disposition or ownership transfer, not because a later summary omitted them.

`NOT IN SUMMARY ≠ REJECTED`
`NOT IN HANDOFF ≠ SUPERSEDED`
`NOT FOUND BY ONE SEARCH ≠ NEVER EXISTED`

## 5. New-conversation resume

`/재개`, `최신 타키 기준으로 재개`, or equivalent continuation for a context-bearing project SHALL recover more than the latest summary.

Minimum recovery when material:
1. latest canonical TAKY and applicable owner rules
2. latest Handoff/current-truth pointer
3. unresolved/open Context Events relevant to the project
4. linked material Idea/Decision traces
5. actual current implementation/runtime/test evidence
6. corrections/supersession links that change interpretation
7. Recovery Witness Events that prove previously lost or falsely-missing requirements
8. first unresolved gate

If a compact Handoff conflicts with recoverable original/context evidence, do not silently trust the compact Handoff. Reconcile against authority and evidence.

## 6. Raw conversation preservation relationship

`/대화전체보존` remains the evidence-preservation path for materially accessible USER↔Assistant conversation in original order.

The Context Ledger complements it:
- Conversation Evidence = what was actually said/shown and in what order.
- Context Ledger = why it mattered, what changed, and what it links to.
- Decision/Idea Trace = lifecycle and disposition.
- Recovery Witness = evidence that a prior context item was recovered after a miss/absence claim.
- Canonical = current approved authority.
- Handoff = efficient recovery pointer/state, not replacement for the above.

## 7. Attachments / URLs / external evidence

When an attachment, image, URL, file, GitHub commit, Notion record, Drive file or runtime result materially changes a decision, preserve its relationship to the relevant Context Event. Do not merely record that an attachment existed.

Where exact content is unavailable later, preserve the pointer and mark coverage limits rather than reconstructing from guesswork.

When the attachment is itself a screenshot/capture of a prior conversation used to correct a false-missing claim, link it as `RECOVERY_WITNESS_EVIDENCE` and, where possible, also link the original conversation/source independently.

## 8. Corrections and supersession

User corrections are first-class context. Preserve both the earlier proposal/decision and the later correction when the transition explains current meaning.

`SUPERSEDED` does not mean erased. It means retained as lineage with a forward link to the replacement.

A rejected idea may later be reconsidered only through a new Context Event that records why conditions changed.

## 8.1 Cross-Conversation Recurrence Pattern — HARD LOCK

Repeated user corrections or repeated Assistant failure classes across separate conversations SHALL be linkable as a Pattern Event when recurrence is material.

A Pattern Event should preserve:
- pattern id and failure class;
- member Context/Recovery Witness Event ids;
- projects/conversations affected;
- first known user correction;
- applicable canonical rule and when it became active;
- later recurrence after that rule/correction;
- downstream artifacts/results affected;
- root cause hypothesis with evidence level;
- regression fixture or validation gate that should prevent recurrence;
- current open/closed status.

`REPEATED INCIDENTS ≠ UNRELATED ONE-OFFS` when the same command-interpretation, recovery, omission, or completion-claim failure mechanism is evidenced.

A recurrence after explicit user correction or canonical hard lock is `POST_CORRECTION_REOCCURRENCE` and requires regression/root-cause treatment, not merely another local correction.

## 9. Implementation truth separation

Context/decision state and implementation state remain separate.

Examples:
- `ADOPTED / IMPLEMENTATION_PENDING`
- `IMPLEMENTED_BOUNDED`
- `VERIFIED`
- `DEVICE_UNVERIFIED`
- `GAP`

`DECIDED ≠ IMPLEMENTED`
`IMPLEMENTED ≠ VERIFIED`
`QUEUED ≠ IMPLEMENTED`

## 10. Anti-fragmentation gate

Before inventing a new rule, feature or architecture for an existing project:
1. search applicable Canonical owners
2. recover relevant unresolved Context Events and decision traces
3. inspect related Recovery Witness/Pattern Events
4. inspect related implementation evidence
5. determine whether the apparent new requirement is actually a lost/omitted prior requirement
6. only then classify as new / recovered / adjusted / conflicting

Repeated re-invention caused by summary omission or failed recovery is a continuity failure.

## 11. Storage principle

Do not force one giant monolithic file. The protocol may be implemented as append-only/event files plus indexes, provided links are stable and recoverable.

Recommended logical layers:
- `CONVERSATION_EVIDENCE/`
- `CONTEXT_LEDGER/`
- `RECOVERY_WITNESS/` or equivalent event type
- `PATTERN_LEDGER/` or equivalent recurrence index
- `DECISION_TRACE/` or existing Decision-Coverage mechanism
- canonical owner files
- `HISTORY/`
- Handoff/current-truth projections

Exact physical folder implementation may be adjusted by Work OS without weakening this protocol.

## 12. Validation

A continuity PASS requires more than a generated summary.

Check:
- material user corrections retained
- unresolved items retained
- superseded lineage linked
- source/attachment relationship retained
- recovery-witness relationship retained when applicable
- false-missing/user-forced-recovery events classified when applicable
- cross-conversation recurrence linked when material
- canonical reflection status distinguishable
- implementation truth distinguishable
- next unresolved gate recoverable
- inaccessible coverage marked honestly

`SUMMARY CREATED ≠ CONTINUITY PASS`
`USER SCREENSHOT RECOVERED ≠ PRIOR RECOVERY PASS`

## 13. Current bootstrap event — 2026-09-12

Recovered intent from the current conversation:
- User explicitly rejected lossy summary as the desired continuity mechanism because repeated summarization had produced major omissions and fragmentation.
- Desired target is context-dependent recording: preserve how discussion, corrections, evidence and decisions evolved.
- User approved proceeding with this Conversation Context Ledger approach because the current conversation appeared near its practical context limit.
- User later identified a broader recurrent failure: information existed in prior conversations, TAKY/Assistant declared it missing, and the user repeatedly had to use chat search and attach screenshots or other evidence to recover it.
- User explicitly requested a scan across all materially accessible conversation windows and relevant Notion review material, even at higher usage cost, so the recurring pattern can be reflected into TAKY and independently checked by Claude.

This bootstrap event establishes the protocol and the cross-conversation recovery-witness/pattern model; it does not claim historical conversations have already been perfectly reconstructed. Historical backfill remains an explicit recovery task and genuinely inaccessible raw history remains `UNVERIFIED_SOURCE_COVERAGE`. Known recoverable misses SHALL instead use the recovery-failure taxonomy rather than being hidden under that label.


## 11. Conversation-to-System compilation bridge

This Ledger preserves continuity and decision formation. Durable system compilation/coverage closure is separately governed by `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md` (TKY-C2S-001).

For material system-building conversations, the Ledger SHALL provide sufficient event/source linkage for downstream atomization and shall not substitute a compact Context Event for atomic coverage when one event contains multiple independently changing requirements, corrections, strategies or frontier ideas.

`CONTEXT EVENT CAPTURED != C2S COVERAGE CLOSED`
`LEDGER EXISTS != UNMAPPED MATERIAL = 0`

When a user correction changes the meaning of a prior system concept, preserve both the correction lineage and the downstream impact targets required by TKY-C2S-001.

END
